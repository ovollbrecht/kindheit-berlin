"""Network distance checks on a tiny graph: a square block 0-1-2-3 with 100 m sides."""

import geopandas as gpd
import numpy as np
import shapely

from pipeline.accessibility import ENTRANCE_TOLERANCE_M, WalkGraph, facility_distance_matrix, nearest_facility_distance, straight_line_distance


def square_graph(main_road_nodes=(), crossings=None) -> WalkGraph:
    xy = np.array([[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]])
    major = np.zeros(4, bool)
    major[list(main_road_nodes)] = True
    crossing = np.zeros(4, np.int8) if crossings is None else np.array(crossings, np.int8)
    # The side 3-0 is missing: walking from node 0 to node 3 means going around the block.
    return WalkGraph(xy, np.array([0, 1, 2]), np.array([1, 2, 3]), np.full(3, 100.0), major, crossing, np.ones(4, bool))


def test_walking_distance_follows_the_network_not_the_straight_line():
    graph = square_graph()
    walking = nearest_facility_distance(graph, [np.array([3])], np.array([0]))
    straight = straight_line_distance(graph.xy[[0]], gpd.GeoSeries([shapely.Point(0, 100)]))
    assert walking[0] == 300.0
    assert straight[0] == 100.0 - ENTRANCE_TOLERANCE_M


def test_distance_matrix_uses_the_closest_entrance_and_the_limit():
    graph = square_graph()
    # Facility 0 has entrances at nodes 2 and 3, facility 1 at node 0.
    matrix = facility_distance_matrix(graph, [np.array([2, 3]), np.array([0])], np.array([0, 1]), limit_m=150).toarray()
    assert np.allclose(matrix, [[0.0, 101.0], [1.0, 101.0]], atol=1e-3)


def test_main_road_without_secured_crossing_blocks_the_route():
    graph = square_graph(main_road_nodes=[1])
    blocked = graph.without_main_road_crossings(allow_secured=True)
    assert np.isinf(nearest_facility_distance(blocked, [np.array([3])], np.array([0]))[0])


def test_signalised_crossing_keeps_the_route_open():
    graph = square_graph(main_road_nodes=[1], crossings=[0, 2, 0, 0])
    assert nearest_facility_distance(graph.without_main_road_crossings(allow_secured=True), [np.array([3])], np.array([0]))[0] == 300.0
    assert np.isinf(nearest_facility_distance(graph.without_main_road_crossings(allow_secured=False), [np.array([3])], np.array([0]))[0])


def test_polygon_is_entered_at_every_node_within_tolerance():
    graph = square_graph()
    playground = shapely.box(90, 90, 110, 110)  # touches node 2 only
    entrances = graph.entrance_nodes(gpd.GeoSeries([playground]))
    assert entrances[0].tolist() == [2]
