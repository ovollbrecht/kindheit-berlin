"""Walking-network accessibility: distances from residential blocks to facilities.

All distances are metres along the pedestrian network built by walk_network.py.
"""

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import scipy.sparse as sp
import shapely
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

from pipeline.walk_network import GRAPH_PATH, MARKED_CROSSING

# A facility polygon is entered at every network node this close to it (metres).
ENTRANCE_TOLERANCE_M = 15.0
# Facilities further than this from any network node are treated as not connected.
MAX_SNAP_DISTANCE_M = 150.0
# Tiny positive weight for the artificial edges "facility -> its entrance nodes"
# (scipy drops explicit zeros from sparse graphs).
ENTRANCE_EDGE_WEIGHT_M = 1e-6
DIJKSTRA_BATCH_SIZE = 32


@dataclass
class WalkGraph:
    xy: np.ndarray  # (n, 2) node coordinates
    edge_u: np.ndarray
    edge_v: np.ndarray
    edge_length: np.ndarray
    node_major: np.ndarray
    node_crossing: np.ndarray
    usable: np.ndarray  # nodes of the largest connected component

    @classmethod
    def load(cls, path: Path = GRAPH_PATH) -> "WalkGraph":
        data = np.load(path)
        xy = np.column_stack([data["x"], data["y"]])
        graph = cls(xy, data["edge_u"], data["edge_v"], data["edge_length"], data["node_major"], data["node_crossing"], np.ones(len(xy), bool))
        _, labels = connected_components(graph.matrix(), directed=False)
        graph.usable = labels == np.bincount(labels).argmax()
        return graph

    @property
    def node_count(self) -> int:
        return len(self.xy)

    def matrix(self, blocked_nodes: np.ndarray | None = None, extra_nodes: int = 0) -> sp.csr_matrix:
        """Symmetric weighted adjacency matrix; edges touching blocked nodes are removed."""
        u, v, length = self.edge_u, self.edge_v, self.edge_length
        if blocked_nodes is not None:
            keep = ~(blocked_nodes[u] | blocked_nodes[v])
            u, v, length = u[keep], v[keep], length[keep]
        size = self.node_count + extra_nodes
        return sp.coo_matrix((length, (u, v)), shape=(size, size)).tocsr()

    def without_main_road_crossings(self, allow_secured: bool) -> "WalkGraph":
        """Copy of the graph in which main roads cannot be crossed.

        allow_secured=True keeps crossings with traffic signals or markings (zebra).
        Connectivity is re-evaluated by the caller through infinite distances.
        """
        blocked = self.node_major.copy()
        if allow_secured:
            blocked &= self.node_crossing < MARKED_CROSSING
        keep = ~(blocked[self.edge_u] | blocked[self.edge_v])
        return WalkGraph(self.xy, self.edge_u[keep], self.edge_v[keep], self.edge_length[keep], self.node_major, self.node_crossing, self.usable & ~blocked)

    def snap(self, points_xy: np.ndarray, exclude: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        """Nearest usable node for each point -> (node index, snap distance)."""
        allowed = self.usable if exclude is None else self.usable & ~exclude
        candidates = np.flatnonzero(allowed)
        distance, position = cKDTree(self.xy[candidates]).query(points_xy)
        return candidates[position], distance

    def entrance_nodes(self, geometries: gpd.GeoSeries) -> list[np.ndarray]:
        """Network nodes at which each facility geometry can be entered.

        Polygons: all usable nodes within ENTRANCE_TOLERANCE_M. Points, or polygons
        without such a node: the single nearest node (if within MAX_SNAP_DISTANCE_M).
        """
        usable_nodes = np.flatnonzero(self.usable)
        tree = shapely.STRtree(shapely.points(self.xy[usable_nodes]))
        result = []
        for geometry in geometries:
            nodes = usable_nodes[tree.query(geometry, predicate="dwithin", distance=ENTRANCE_TOLERANCE_M)]
            if len(nodes) == 0:
                nodes = usable_nodes[tree.query(geometry, predicate="dwithin", distance=MAX_SNAP_DISTANCE_M)]
                if len(nodes) > 0:
                    nearest = np.argmin(shapely.distance(geometry, shapely.points(self.xy[nodes])))
                    nodes = nodes[[nearest]]
            result.append(nodes)
        return result


def nearest_facility_distance(graph: WalkGraph, entrances: list[np.ndarray], origin_nodes: np.ndarray) -> np.ndarray:
    """Network distance from each origin node to the nearest facility (inf if unreachable)."""
    sources = np.unique(np.concatenate(entrances))
    distances = dijkstra(graph.matrix(), directed=False, indices=sources, min_only=True)
    return distances[origin_nodes]


def facility_distance_matrix(graph: WalkGraph, entrances: list[np.ndarray], origin_nodes: np.ndarray, limit_m: float) -> sp.csr_matrix:
    """Sparse matrix [facility, origin] of network distances up to limit_m.

    Each facility becomes an artificial node linked to all its entrance nodes, so a
    facility with several entrances is reached via the closest one. Stored values
    are distance + 1 so that a true distance of 0 is distinguishable from "no entry".
    """
    facility_count = len(entrances)
    facility_index = np.repeat(np.arange(facility_count), [len(nodes) for nodes in entrances])
    links = sp.coo_matrix(
        (np.full(len(facility_index), ENTRANCE_EDGE_WEIGHT_M), (graph.node_count + facility_index, np.concatenate(entrances))),
        shape=(graph.node_count + facility_count, graph.node_count + facility_count),
    )
    matrix = (graph.matrix(extra_nodes=facility_count) + links).tocsr()

    rows, columns, values = [], [], []
    for start in range(0, facility_count, DIJKSTRA_BATCH_SIZE):
        batch = np.arange(start, min(start + DIJKSTRA_BATCH_SIZE, facility_count))
        distances = dijkstra(matrix, directed=False, indices=graph.node_count + batch, limit=limit_m)[:, origin_nodes]
        row, column = np.nonzero(np.isfinite(distances))
        rows.append(batch[row])
        columns.append(column)
        values.append(distances[row, column] + 1.0)
    return sp.coo_matrix((np.concatenate(values), (np.concatenate(rows), np.concatenate(columns))), shape=(facility_count, len(origin_nodes))).tocsr()


def straight_line_distance(origin_xy: np.ndarray, geometries: gpd.GeoSeries) -> np.ndarray:
    """Straight-line distance from each origin point to the nearest facility geometry.

    The entrance tolerance is subtracted so that straight-line and network distance
    end at the same place (a network route ends at a node up to that far from the facility).
    """
    tree = shapely.STRtree(geometries.values)
    _, distance = tree.query_nearest(shapely.points(origin_xy), return_distance=True, all_matches=False)
    return np.maximum(distance - ENTRANCE_TOLERANCE_M, 0.0)
