"""
map_manager.py
--------------
Bridges Python routing data with a visual Folium map.

Design notes:
- Split into build_base_map() and draw_route() per the "separate map style
  from map data" improvement. This means you can unit test draw_route's
  polyline logic without re-initializing tiles/zoom every time, and the
  base map (markers, tiles) only needs to be rebuilt when stop data changes.
- save_map() writes to a fixed path so QWebEngineView can repeatedly reload
  the same file:// URL.
"""

import os

import folium

from config import STOPS, GRAPH
from pathfinding import RouteResult

MAP_OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map.html")


def _network_center() -> tuple[float, float]:
    """Average lat/lon across all stops, used to center the map on load."""
    lats = [s.lat for s in STOPS.values()]
    lons = [s.lon for s in STOPS.values()]
    return (sum(lats) / len(lats), sum(lons) / len(lons))


def build_base_map() -> folium.Map:
    """
    Create the base Folium map: centered on the network, with every stop
    marked, and every edge drawn as a faint connecting line so the user can
    see the overall network shape before picking a route.
    """
    center = _network_center()
    fmap = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")

    # Draw all edges faintly in the background so the network is visible.
    drawn_edges = set()
    for stop_name, neighbors in GRAPH.items():
        for neighbor_name in neighbors:
            edge_key = frozenset((stop_name, neighbor_name))
            if edge_key in drawn_edges:
                continue
            drawn_edges.add(edge_key)
            folium.PolyLine(
                locations=[STOPS[stop_name].as_tuple(), STOPS[neighbor_name].as_tuple()],
                color="#999999",
                weight=2,
                opacity=0.4,
            ).add_to(fmap)

    # Add a marker for every stop.
    for stop in STOPS.values():
        folium.Marker(
            location=stop.as_tuple(),
            popup=stop.name,
            tooltip=stop.name,
            icon=folium.Icon(color="blue", icon="bus", prefix="fa"),
        ).add_to(fmap)

    return fmap


def draw_route(fmap: folium.Map, route: RouteResult) -> folium.Map:
    """
    Highlight the optimal route on top of an existing base map.
    Draws a bold polyline over the path and re-marks start/end distinctly.
    """
    folium.PolyLine(
        locations=route.coordinates,
        color="#e63946",
        weight=6,
        opacity=0.9,
        tooltip=f"{route.num_stops} stops, {route.total_distance_km} km",
    ).add_to(fmap)

    # Distinct start/end markers so the highlighted route stands out.
    start_name, end_name = route.path[0], route.path[-1]
    folium.Marker(
        location=STOPS[start_name].as_tuple(),
        popup=f"Start: {start_name}",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
    ).add_to(fmap)
    folium.Marker(
        location=STOPS[end_name].as_tuple(),
        popup=f"Destination: {end_name}",
        icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
    ).add_to(fmap)

    return fmap


def save_map(fmap: folium.Map, path: str = MAP_OUTPUT_PATH) -> str:
    """Render the map to an HTML file and return its path."""
    fmap.save(path)
    return path


def generate_route_map(route: RouteResult | None = None) -> str:
    """
    Convenience one-shot function: builds the base map, optionally overlays
    a route, saves it, and returns the file path for QWebEngineView to load.
    """
    fmap = build_base_map()
    if route is not None:
        fmap = draw_route(fmap, route)
    return save_map(fmap)
