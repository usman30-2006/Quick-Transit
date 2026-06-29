"""
tests/test_pathfinding.py
--------------------------
Unit tests for pathfinding.py using a small, hand-verifiable graph.
No Qt or Folium dependencies are needed here, since pathfinding.py is
pure Python logic -- this is the payoff of keeping it decoupled from the UI.

Run with:  python -m pytest tests/test_pathfinding.py -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from config import Stop
from pathfinding import (
    find_shortest_path,
    haversine_distance,
    InvalidStopError,
    NoPathFoundError,
    SameStopError,
)


# A small, easy-to-verify-by-hand test network:
#
#   A --1-- B --1-- C
#   |               |
#   4 ------ D ------1
#
# Shortest path A -> C should be A-B-C (cost 2), not A-D-C (cost 5).
TEST_STOPS = {
    "A": Stop("A", 0.0, 0.0),
    "B": Stop("B", 0.0, 1.0),
    "C": Stop("C", 0.0, 2.0),
    "D": Stop("D", 1.0, 1.0),
}

TEST_GRAPH = {
    "A": {"B": 1.0, "D": 4.0},
    "B": {"A": 1.0, "C": 1.0},
    "C": {"B": 1.0, "D": 1.0},
    "D": {"A": 4.0, "C": 1.0},
}

# An isolated stop with no edges, to test NoPathFoundError.
DISCONNECTED_STOPS = {**TEST_STOPS, "Z": Stop("Z", 5.0, 5.0)}
DISCONNECTED_GRAPH = {**TEST_GRAPH, "Z": {}}


def test_finds_correct_shortest_path():
    result = find_shortest_path(TEST_GRAPH, "A", "C", stops=TEST_STOPS)
    assert result.path == ["A", "B", "C"]
    assert result.total_distance_km == 2.0
    assert result.num_stops == 3


def test_path_includes_coordinates():
    result = find_shortest_path(TEST_GRAPH, "A", "C", stops=TEST_STOPS)
    assert result.coordinates == [(0.0, 0.0), (0.0, 1.0), (0.0, 2.0)]


def test_single_hop_path():
    result = find_shortest_path(TEST_GRAPH, "A", "B", stops=TEST_STOPS)
    assert result.path == ["A", "B"]
    assert result.total_distance_km == 1.0


def test_invalid_start_stop_raises():
    with pytest.raises(InvalidStopError):
        find_shortest_path(TEST_GRAPH, "NotARealStop", "C", stops=TEST_STOPS)


def test_invalid_end_stop_raises():
    with pytest.raises(InvalidStopError):
        find_shortest_path(TEST_GRAPH, "A", "NotARealStop", stops=TEST_STOPS)


def test_same_start_and_end_raises():
    with pytest.raises(SameStopError):
        find_shortest_path(TEST_GRAPH, "A", "A", stops=TEST_STOPS)


def test_no_path_found_for_disconnected_node():
    with pytest.raises(NoPathFoundError):
        find_shortest_path(DISCONNECTED_GRAPH, "A", "Z", stops=DISCONNECTED_STOPS)


def test_haversine_zero_distance_for_same_point():
    d = haversine_distance((33.6844, 73.0479), (33.6844, 73.0479))
    assert d == pytest.approx(0.0, abs=1e-6)


def test_haversine_known_distance():
    # Roughly the distance between two well-known coordinates (Islamabad
    # and Lahore), used here just as a sanity check on magnitude, not an
    # exact survey distance.
    islamabad = (33.6844, 73.0479)
    lahore = (31.5497, 74.3436)
    d = haversine_distance(islamabad, lahore)
    assert 250 < d < 300  # straight-line distance is roughly ~275 km
