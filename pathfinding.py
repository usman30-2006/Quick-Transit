"""
pathfinding.py
---------------
Core routing engine: the Haversine heuristic and the A* search algorithm.

Design notes:
- No PySide6 / Folium imports here on purpose. This module has zero GUI
  dependencies, which means it's trivially unit-testable (see tests/).
- Custom exceptions (NoPathFoundError, InvalidStopError) let the UI layer
  show a friendly QMessageBox instead of crashing on a stack trace.
- Returns a RouteResult with the path AND metadata (total distance), so the
  UI can display something like "Route: 5 stops, 12.4 km" for free.
"""

import heapq
import math
from dataclasses import dataclass, field

from config import STOPS, GRAPH, Stop


class PathfindingError(Exception):
    """Base class for all routing errors."""


class InvalidStopError(PathfindingError):
    """Raised when a start/end stop name doesn't exist in the network."""

    def __init__(self, stop_name: str):
        self.stop_name = stop_name
        super().__init__(f"'{stop_name}' is not a known stop in the network.")


class NoPathFoundError(PathfindingError):
    """Raised when start and end stops exist but no route connects them."""

    def __init__(self, start: str, end: str):
        self.start = start
        self.end = end
        super().__init__(f"No route exists between '{start}' and '{end}'.")


class SameStopError(PathfindingError):
    """Raised when the start and destination stop are identical."""

    def __init__(self, stop_name: str):
        self.stop_name = stop_name
        super().__init__(f"Start and destination are both '{stop_name}'.")


@dataclass
class RouteResult:
    """The output of a successful pathfind: the path plus useful metadata."""
    path: list[str]                 # ordered list of stop names
    total_distance_km: float        # sum of edge weights along the path
    coordinates: list[tuple[float, float]] = field(default_factory=list)  # (lat, lon) per stop

    @property
    def num_stops(self) -> int:
        return len(self.path)


def haversine_distance(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
    """
    Calculate the great-circle distance between two (lat, lon) points in km.
    Used as the A* heuristic: an admissible, never-overestimating estimate
    of the remaining distance to the goal (straight-line "as the crow flies").
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def _validate_stops(start: str, end: str, stops: dict[str, Stop]) -> None:
    if start not in stops:
        raise InvalidStopError(start)
    if end not in stops:
        raise InvalidStopError(end)
    if start == end:
        raise SameStopError(start)


def find_shortest_path(
    graph: dict[str, dict[str, float]],
    start: str,
    end: str,
    stops: dict[str, Stop] = STOPS,
) -> RouteResult:
    """
    A* search over `graph` from `start` to `end`.

    graph: adjacency list {stop_name: {neighbor_name: edge_weight_km}}
    stops: lookup table for coordinates, used by the Haversine heuristic.

    Returns a RouteResult on success.
    Raises InvalidStopError / SameStopError / NoPathFoundError on failure.
    """
    _validate_stops(start, end, stops)

    goal_coord = stops[end].as_tuple()

    # g_score: best known cost from start to each node
    g_score: dict[str, float] = {start: 0.0}
    # came_from: for path reconstruction
    came_from: dict[str, str] = {}
    # priority queue of (f_score, node) -- f_score = g_score + heuristic
    open_heap: list[tuple[float, str]] = []
    heapq.heappush(open_heap, (0.0, start))
    visited: set[str] = set()

    while open_heap:
        _, current = heapq.heappop(open_heap)

        if current == end:
            return _reconstruct_path(came_from, current, g_score[end], stops)

        if current in visited:
            continue
        visited.add(current)

        for neighbor, weight in graph.get(current, {}).items():
            tentative_g = g_score[current] + weight

            if tentative_g < g_score.get(neighbor, math.inf):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                h = haversine_distance(stops[neighbor].as_tuple(), goal_coord)
                f_score = tentative_g + h
                heapq.heappush(open_heap, (f_score, neighbor))

    # Open set exhausted without reaching the goal -> graph is disconnected.
    raise NoPathFoundError(start, end)


def _reconstruct_path(
    came_from: dict[str, str],
    current: str,
    total_distance: float,
    stops: dict[str, Stop],
) -> RouteResult:
    """Walk the came_from chain backwards to build the ordered stop list."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()

    coordinates = [stops[name].as_tuple() for name in path]
    return RouteResult(path=path, total_distance_km=round(total_distance, 2), coordinates=coordinates)
