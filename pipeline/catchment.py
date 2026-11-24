"""Catchment-based calculations on a sparse facility x home distance matrix.

The matrices come from accessibility.facility_distance_matrix and store
distance + 1, so that an explicit entry of 1.0 means "distance 0".
"""

import numpy as np
import scipy.sparse as sp


def within(matrix: sp.csr_matrix, threshold_m: float) -> sp.csr_matrix:
    """0/1 matrix: which facility is within the threshold of which home."""
    reach = matrix.copy()
    reach.data = (reach.data - 1.0 <= threshold_m).astype(float)
    reach.eliminate_zeros()
    return reach


def two_step_supply(matrix: sp.csr_matrix, capacity: np.ndarray, demand: np.ndarray, threshold_m: float) -> np.ndarray:
    """Two-step floating catchment area: capacity per demand unit reachable from each home.

    Step 1: each facility's capacity is divided by all demand within the threshold.
    Step 2: each home sums the ratios of the facilities it can reach.
    The capacity of all facilities with any demand is handed out exactly once.
    """
    reach = within(matrix, threshold_m)
    demand_per_facility = reach @ demand
    ratio = np.divide(capacity, demand_per_facility, out=np.zeros(len(capacity)), where=demand_per_facility > 0)
    return reach.T @ ratio


def greedy_max_coverage(reach: sp.csr_matrix, demand: np.ndarray, steps: int) -> list[tuple[int, float]]:
    """Pick facilities one by one, each time the one that covers the most not-yet-covered demand.

    Returns (facility index, newly covered demand) per step. Demand covered by an
    earlier pick is never counted again. The greedy choice is not guaranteed to be
    optimal, but it is at least 63 % of the optimum (the classic bound for this problem).
    """
    uncovered = demand.astype(float).copy()
    picks = []
    for _ in range(min(steps, reach.shape[0])):
        gains = reach @ uncovered
        best = int(np.argmax(gains))
        if gains[best] <= 0:
            break
        picks.append((best, float(gains[best])))
        uncovered[reach[best].indices] = 0.0
    return picks
