"""Build a pedestrian network for Berlin from the OpenStreetMap extract.

Output: data/interim/walk_graph.npz with
  x, y            node coordinates in EPSG:25833
  edge_u, edge_v  node indices of each (undirected) edge
  edge_length     metres
  node_major      True if the node lies on a main road (see MAJOR_HIGHWAYS), whether
                  or not that road itself is walkable. A route passing such a node
                  crosses the road or runs along it.
  node_crossing   0 = no crossing facility mapped, 1 = marked crossing (e.g. zebra),
                  2 = traffic signals

Modelling decisions (documented in docs/METHODOLOGY.md):
- Every way a pedestrian may legally and practically use is walkable; motorways
  and ways with foot/access restrictions are not.
- Berlin's main roads mostly have separately mapped sidewalks (foot=use_sidepath),
  so the carriageway is not part of the walking graph. Their nodes are flagged
  anyway, so that analyses can count main-road crossings on a route.
- Edge length is planar distance in EPSG:25833; slope and waiting times are ignored.
"""

from pathlib import Path

import numpy as np
import osmium
from pyproj import Transformer

from pipeline.sources import ANALYSIS_CRS

ROOT = Path(__file__).resolve().parent.parent
PBF_PATH = ROOT / "data" / "raw" / "berlin.osm.pbf"
GRAPH_PATH = ROOT / "data" / "interim" / "walk_graph.npz"

NOT_WALKABLE_HIGHWAYS = {
    "motorway", "motorway_link", "trunk", "trunk_link", "construction", "proposed",
    "raceway", "bus_guideway", "busway", "abandoned", "razed", "planned", "rest_area", "services",
}
MAJOR_HIGHWAYS = {"primary", "primary_link", "secondary", "secondary_link", "trunk", "trunk_link"}
FOOT_ALLOWED = {"yes", "designated", "permissive", "official"}
ACCESS_DENIED = {"no", "private", "customers", "delivery", "agricultural", "forestry", "military"}
NO_CROSSING, MARKED_CROSSING, SIGNAL_CROSSING = 0, 1, 2
MARKED_CROSSING_VALUES = {"marked", "zebra", "uncontrolled"}


def crossing_kind(tags) -> int:
    """Classify a highway=crossing / highway=traffic_signals node."""
    if tags.get("highway") == "traffic_signals" or tags.get("crossing") == "traffic_signals" or tags.get("crossing:signals") == "yes":
        return SIGNAL_CROSSING
    if tags.get("crossing") in MARKED_CROSSING_VALUES or tags.get("crossing:markings") not in (None, "no"):
        return MARKED_CROSSING
    return NO_CROSSING


def is_walkable(tags) -> bool:
    highway = tags.get("highway")
    foot = tags.get("foot")
    if highway in NOT_WALKABLE_HIGHWAYS:
        # Trunk roads with an explicitly allowed sidewalk remain usable.
        return highway in {"trunk", "trunk_link"} and foot in FOOT_ALLOWED
    if tags.get("area") == "yes" and highway not in {"pedestrian", "footway"}:
        return False
    if foot in FOOT_ALLOWED:
        return True
    if foot in {"no", "private", "use_sidepath"}:
        return False
    if tags.get("access") in ACCESS_DENIED:
        return False
    return True


def build_graph() -> dict[str, np.ndarray]:
    crossing_kinds: dict[int, int] = {}
    major_ids: set[int] = set()
    node_index: dict[int, int] = {}
    lons: list[float] = []
    lats: list[float] = []
    edge_u: list[int] = []
    edge_v: list[int] = []

    # Nodes precede ways in the file: collect crossing nodes first, then turn
    # walkable ways into edges between consecutive nodes.
    highway_objects = (
        osmium.FileProcessor(str(PBF_PATH), osmium.osm.NODE | osmium.osm.WAY)
        .with_locations()
        .with_filter(osmium.filter.KeyFilter("highway"))
    )
    for way in highway_objects:
        if way.is_node():
            kind = crossing_kind(way.tags)
            if kind != NO_CROSSING:
                crossing_kinds[way.id] = kind
            continue
        is_major = way.tags.get("highway") in MAJOR_HIGHWAYS
        if is_major:
            major_ids.update(node.ref for node in way.nodes)
        if not is_walkable(way.tags):
            continue
        if way.tags.get("footway") == "crossing":
            # Crossing facilities are often tagged on the crossing way instead of the node.
            kind = crossing_kind(way.tags)
            for node in way.nodes:
                crossing_kinds[node.ref] = max(kind, crossing_kinds.get(node.ref, NO_CROSSING))
        previous = None
        for node in way.nodes:
            if not node.location.valid():
                previous = None
                continue
            index = node_index.get(node.ref)
            if index is None:
                index = len(lons)
                node_index[node.ref] = index
                lons.append(node.location.lon)
                lats.append(node.location.lat)
            if previous is not None and previous != index:
                edge_u.append(previous)
                edge_v.append(index)
            previous = index

    x, y = Transformer.from_crs("EPSG:4326", ANALYSIS_CRS, always_xy=True).transform(np.array(lons), np.array(lats))
    u, v = np.array(edge_u), np.array(edge_v)
    node_crossing = np.zeros(len(x), dtype=np.int8)
    node_major = np.zeros(len(x), dtype=bool)
    for osm_id, index in node_index.items():
        node_crossing[index] = crossing_kinds.get(osm_id, NO_CROSSING)
        node_major[index] = osm_id in major_ids
    return {
        "x": x,
        "y": y,
        "edge_u": u,
        "edge_v": v,
        "edge_length": np.hypot(x[u] - x[v], y[u] - y[v]),
        "node_major": node_major,
        "node_crossing": node_crossing,
    }


if __name__ == "__main__":
    graph = build_graph()
    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(GRAPH_PATH, **graph)
    print(
        f"nodes={len(graph['x']):,} edges={len(graph['edge_u']):,} "
        f"length_km={graph['edge_length'].sum() / 1000:,.0f} "
        f"nodes_on_main_roads={int(graph['node_major'].sum()):,} "
        f"of those marked={int((graph['node_major'] & (graph['node_crossing'] == MARKED_CROSSING)).sum()):,} "
        f"signalised={int((graph['node_major'] & (graph['node_crossing'] == SIGNAL_CROSSING)).sum()):,}"
    )
