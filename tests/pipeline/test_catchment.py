"""Checks for the catchment calculations on small hand-made examples."""

import numpy as np
import scipy.sparse as sp

from pipeline.catchment import greedy_max_coverage, two_step_supply, within


def distance_matrix(distances: list[list[float | None]]) -> sp.csr_matrix:
    """Facility x home matrix in the stored convention (distance + 1, None = out of range)."""
    return sp.csr_matrix(np.array([[0.0 if d is None else d + 1.0 for d in row] for row in distances]))


def test_within_keeps_distance_zero_and_respects_threshold():
    matrix = distance_matrix([[0, 400, 401, None]])
    assert within(matrix, 400).toarray().tolist() == [[1.0, 1.0, 0.0, 0.0]]


def test_two_step_supply_shares_capacity_between_all_homes_in_reach():
    # One playground of 100 m2 reached by two homes with 10 and 30 children: 2.5 m2 per child each.
    matrix = distance_matrix([[100, 300, None]])
    supply = two_step_supply(matrix, np.array([100.0]), np.array([10.0, 30.0, 5.0]), threshold_m=400)
    assert supply.tolist() == [2.5, 2.5, 0.0]


def test_two_step_supply_ignores_administrative_borders_and_conserves_capacity():
    # Home 1 reaches both facilities, homes 0 and 2 one each.
    matrix = distance_matrix([[50, 200, None], [None, 100, 350]])
    capacity = np.array([120.0, 80.0])
    demand = np.array([20.0, 20.0, 20.0])
    supply = two_step_supply(matrix, capacity, demand, threshold_m=400)
    assert supply.tolist() == [3.0, 5.0, 2.0]
    assert np.isclose((supply * demand).sum(), capacity.sum())


def test_two_step_supply_treats_missing_demand_as_zero_not_as_error():
    matrix = distance_matrix([[100, None]])
    supply = two_step_supply(matrix, np.array([50.0]), np.array([0.0, 10.0]), threshold_m=400)
    assert supply.tolist() == [0.0, 0.0]


def test_greedy_coverage_never_counts_a_child_twice():
    # Sites 0 and 1 overlap on home 1; site 2 only reaches home 3.
    reach = sp.csr_matrix(np.array([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 0, 1]], dtype=float))
    children = np.array([10.0, 50.0, 20.0, 15.0])
    picks = greedy_max_coverage(reach, children, steps=3)
    assert picks == [(1, 70.0), (2, 15.0), (0, 10.0)]
    assert sum(gain for _, gain in picks) == children.sum()


def test_greedy_coverage_stops_when_nothing_is_left_to_gain():
    reach = sp.csr_matrix(np.array([[1, 1], [1, 0]], dtype=float))
    assert greedy_max_coverage(reach, np.array([5.0, 5.0]), steps=5) == [(0, 10.0)]


def test_greedy_coverage_only_removes_homes_inside_the_threshold():
    # Regression: the stored matrix also holds pairs beyond the threshold (here 900 m).
    # Picking site 0 must not mark the far home as covered.
    matrix = distance_matrix([[100, 900], [None, 200]])
    reach = within(matrix, 400)
    picks = greedy_max_coverage(reach, np.array([10.0, 8.0]), steps=2)
    assert picks == [(0, 10.0), (1, 8.0)]
