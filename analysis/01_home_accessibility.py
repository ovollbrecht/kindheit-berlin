"""Network distances from children's homes to the facilities they use.

"Homes" are the model of where children live: the residents of each statistical
block (with age groups, 31.12.2025) are distributed over the block's residential
buildings (ALKIS) in proportion to floor area, and each building is attached to
the nearest walkable network node. One row = one (block, node) pair with the
(fractional) number of residents and children assigned to it.

Writes data/interim/homes.csv, playgrounds.csv and sparse distance matrices.

Run:  python -m analysis.01_home_accessibility
"""

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import scipy.sparse as sp

from pipeline.accessibility import WalkGraph, facility_distance_matrix, nearest_facility_distance, straight_line_distance
from pipeline.sources import ANALYSIS_CRS

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

PLAYGROUND_MATRIX_LIMIT_M = 1500.0
YOUTH_MATRIX_LIMIT_M = 2500.0
# Berlin's own criterion for a "wohnungsnahe Grünanlage" (Umweltatlas 06.05): at least 0.5 ha.
MIN_GREEN_SPACE_M2 = 5000.0
# ALKIS building functions that house (almost) no children: homes for the elderly, student halls.
BUILDING_FUNCTIONS_WITHOUT_CHILDREN = {1022, 1024}
OSM_NOT_PUBLIC_ACCESS = {"private", "customers", "no", "permit", "residents"}
POPULATION_COLUMNS = ["residents", "age_0_5", "age_6_9", "age_10_17", "children"]


def read(name: str) -> gpd.GeoDataFrame:
    return gpd.read_file(RAW / f"{name}.geojson")


def load_blocks() -> gpd.GeoDataFrame:
    blocks = read("blocks_population_2025")
    blocks = blocks[blocks["ew2025"] > 0].copy()
    blocks = blocks.rename(columns={"schluessel": "block_id", "ew2025": "residents", "alter_u6": "age_0_5", "alter_6_u10": "age_6_9", "alter_10_u18": "age_10_17"})
    blocks["children"] = blocks[["age_0_5", "age_6_9", "age_10_17"]].sum(axis=1)
    # Planning area by representative point (blocks nest into planning areas).
    points = blocks.set_geometry(blocks.representative_point())
    joined = gpd.sjoin(points, read("lor_plr")[["plr_id", "geometry"]], predicate="within", how="left")
    blocks["plr_id"] = joined["plr_id"].values
    return blocks[["block_id", "plr_id", *POPULATION_COLUMNS, "typklar", "geometry"]].reset_index(drop=True)


def load_residential_buildings() -> gpd.GeoDataFrame:
    """Building centre (from the bounding box) and floor area = footprint x storeys above ground."""
    features = json.loads((RAW / "residential_buildings.geojson").read_text())["features"]
    attributes = pd.DataFrame([feature["properties"] for feature in features])
    bbox = np.array([feature["bbox"] for feature in features])
    buildings = gpd.GeoDataFrame(
        {"floor_area": attributes["shape_area"] * attributes["aog"].fillna(1).clip(lower=1), "function": attributes["gfk"]},
        geometry=gpd.points_from_xy((bbox[:, 0] + bbox[:, 2]) / 2, (bbox[:, 1] + bbox[:, 3]) / 2),
        crs=ANALYSIS_CRS,
    )
    return buildings[~buildings["function"].isin(BUILDING_FUNCTIONS_WITHOUT_CHILDREN)]


def build_homes(blocks: gpd.GeoDataFrame, graph: WalkGraph) -> pd.DataFrame:
    buildings = gpd.sjoin(load_residential_buildings(), blocks[["block_id", "geometry"]], predicate="within")[["block_id", "floor_area", "geometry"]]
    # Blocks with residents but without a residential building: one home at the representative point.
    without_building = blocks[~blocks["block_id"].isin(buildings["block_id"])]
    fallback = gpd.GeoDataFrame({"block_id": without_building["block_id"], "floor_area": 1.0}, geometry=without_building.representative_point(), crs=ANALYSIS_CRS)
    locations = pd.concat([buildings, fallback], ignore_index=True)
    print(f"blocks: {len(blocks):,}, of those without residential building: {len(without_building):,} ({without_building['children'].sum():,.0f} children)")

    xy = np.column_stack([locations.geometry.x, locations.geometry.y])
    locations["node"], locations["snap_m"] = graph.snap(xy, exclude=graph.node_major)
    locations["weight"] = locations["floor_area"] / locations.groupby("block_id")["floor_area"].transform("sum")
    locations["weighted_snap"] = locations["snap_m"] * locations["weight"]
    homes = locations.groupby(["block_id", "node"], as_index=False).agg(weight=("weight", "sum"), weighted_snap=("weighted_snap", "sum"))
    homes["snap_m"] = homes["weighted_snap"] / homes["weight"]
    homes = homes.merge(blocks.drop(columns="geometry"), on="block_id")
    for column in POPULATION_COLUMNS:
        homes[column] = homes[column] * homes["weight"]
    homes["x"], homes["y"] = graph.xy[homes["node"], 0], graph.xy[homes["node"], 1]
    return homes.drop(columns=["weight", "weighted_snap"])


def main() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    graph = WalkGraph.load()
    blocks = load_blocks()
    homes = build_homes(blocks, graph)
    assert abs(homes["children"].sum() - blocks["children"].sum()) < 1e-6, "children were lost while distributing blocks to homes"
    home_nodes = homes["node"].values
    home_xy = homes[["x", "y"]].values

    playgrounds = read("playgrounds")
    playgrounds = playgrounds[playgrounds["widmung"].str.strip() != "entwidmet"].reset_index(drop=True)
    schools = read("schools")
    green = read("green_spaces")
    osm_playgrounds = gpd.read_file(INTERIM / "osm_playgrounds.geojson")
    osm_playgrounds = osm_playgrounds[~osm_playgrounds["access"].isin(OSM_NOT_PUBLIC_ACCESS)]
    facilities = {
        "playground": playgrounds.geometry,
        # Sensitivity variant: official public playgrounds plus those known to OSM and not tagged private.
        "playground_incl_osm": pd.concat([playgrounds.geometry, osm_playgrounds.geometry], ignore_index=True),
        "youth": read("youth_facilities").geometry,
        "primary_school": schools[(schools["schulart"] == "Grundschule") & (schools["traeger"] == "oeffentlich")].geometry,
        "daycare": read("daycare").geometry,
        "green": green[green["katasterfl"] >= MIN_GREEN_SPACE_M2].geometry,
        "sports": read("sports_sites").geometry,
        "library": gpd.read_file(INTERIM / "osm_libraries.geojson").geometry,
    }
    entrances = {}
    for name, geometries in facilities.items():
        entrances[name] = graph.entrance_nodes(geometries)
        connected = [nodes for nodes in entrances[name] if len(nodes) > 0]
        homes[f"{name}_net_m"] = nearest_facility_distance(graph, connected, home_nodes)
        # A walking route can never be shorter than the straight line. The few exceptions are
        # facilities without a mapped path closer than the entrance tolerance, whose route ends
        # at the nearest path instead; there the straight line is capped at the walking distance.
        homes[f"{name}_air_m"] = np.minimum(straight_line_distance(home_xy, geometries), homes[f"{name}_net_m"])
        print(f"{name}: {len(geometries)} facilities, {len(geometries) - len(connected)} not connected to the network")

    # Playgrounds reachable without crossing a main road / only via secured crossings.
    playground_entrances = [nodes for nodes in entrances["playground"] if len(nodes) > 0]
    for column, allow_secured in [("playground_no_main_road_m", False), ("playground_secured_crossings_m", True)]:
        homes[column] = nearest_facility_distance(graph.without_main_road_crossings(allow_secured), playground_entrances, home_nodes)

    limits = {"playground": PLAYGROUND_MATRIX_LIMIT_M, "youth": YOUTH_MATRIX_LIMIT_M, "primary_school": PLAYGROUND_MATRIX_LIMIT_M, "daycare": PLAYGROUND_MATRIX_LIMIT_M}
    for name, limit in limits.items():
        matrix = facility_distance_matrix(graph, entrances[name], home_nodes, limit)
        sp.save_npz(INTERIM / f"{name}_matrix.npz", matrix)
        print(f"{name} matrix: {matrix.nnz:,} facility-home pairs within {limit:.0f} m")

    playgrounds.drop(columns="geometry").to_csv(INTERIM / "playgrounds.csv", index=False)
    homes.to_csv(INTERIM / "homes.csv", index=False)
    print(f"homes: {len(homes):,}, children: {homes['children'].sum():,.0f}, median snap distance: {homes['snap_m'].median():.0f} m")


if __name__ == "__main__":
    main()
