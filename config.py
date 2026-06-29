"""
config.py
---------
Defines the static bus network data: stops (with coordinates) and the
weighted connections (edges) between them.

Design notes:
- Stops are modeled as a `Stop` dataclass instead of raw tuples/dicts.
  This avoids lat/lon ordering bugs and gives IDE autocomplete + type hints.
- The graph is an adjacency list: {stop_name: {neighbor_name: weight, ...}}.
  This gives O(1) neighbor lookups for A*, instead of scanning an edge list.
- Weights here represent distance in kilometers, but could just as easily
  represent travel time if you swap in real-world data.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Stop:
    """A single bus stop with a name and geographic coordinates."""
    name: str
    lat: float
    lon: float

    def as_tuple(self) -> tuple[float, float]:
        """Return (lat, lon) -- the order Folium expects."""
        return (self.lat, self.lon)


# ---------------------------------------------------------------------------
# Bus stops (sample data for a small city network).
# Replace with real GTFS data or your own coordinates as needed.
# ---------------------------------------------------------------------------
STOPS: dict[str, Stop] = {
    "Central Station":   Stop("Central Station", 33.6844, 73.0479),
    "Blue Area":          Stop("Blue Area", 33.7077, 73.0563),
    "Saddar":              Stop("Saddar", 33.5996, 73.0498),
    "F-10 Markaz":         Stop("F-10 Markaz", 33.6960, 73.0118),
    "G-9 Markaz":          Stop("G-9 Markaz", 33.6939, 73.0339),
    "Faisal Mosque":       Stop("Faisal Mosque", 33.7295, 73.0372),
    "Rawal Lake":          Stop("Rawal Lake", 33.6844, 73.1206),
    "Airport":             Stop("Airport", 33.5491, 72.8260),
    "Bahria Town":         Stop("Bahria Town", 33.5360, 73.1530),
    "PWD Chowk":           Stop("PWD Chowk", 33.5786, 73.1469),
}


# ---------------------------------------------------------------------------
# Graph edges: adjacency list of {stop_name: {neighbor_name: distance_km}}
# Distances are illustrative (roughly proportional to real distances), not
# survey-accurate. Edges are bidirectional and added symmetrically below.
# ---------------------------------------------------------------------------
def _build_graph() -> dict[str, dict[str, float]]:
    raw_edges = [
        ("Central Station", "Blue Area", 3.2),
        ("Central Station", "Saddar", 9.5),
        ("Central Station", "G-9 Markaz", 4.8),
        ("Blue Area", "F-10 Markaz", 4.0),
        ("Blue Area", "Faisal Mosque", 5.5),
        ("G-9 Markaz", "F-10 Markaz", 2.6),
        ("G-9 Markaz", "Saddar", 7.1),
        ("F-10 Markaz", "Faisal Mosque", 4.3),
        ("Saddar", "Rawal Lake", 6.0),
        ("Saddar", "Airport", 17.4),
        ("Rawal Lake", "PWD Chowk", 5.9),
        ("Rawal Lake", "Bahria Town", 8.2),
        ("PWD Chowk", "Bahria Town", 4.1),
        ("PWD Chowk", "Airport", 21.0),
        ("Airport", "Bahria Town", 24.5),
    ]

    graph: dict[str, dict[str, float]] = {name: {} for name in STOPS}
    for a, b, weight in raw_edges:
        graph[a][b] = weight
        graph[b][a] = weight  # bidirectional
    return graph


GRAPH: dict[str, dict[str, float]] = _build_graph()


def get_stop_names() -> list[str]:
    """Convenience helper for populating UI dropdowns."""
    return sorted(STOPS.keys())
