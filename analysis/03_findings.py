"""Compute every published finding from the prepared tables.

Writes data/processed/findings.json (all numbers quoted in docs/FINDINGS.md and
docs/ANALYSIS_REPORT.md) plus case lists as CSV under data/processed/.

Run:  python -m analysis.03_findings
"""

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import scipy.sparse as sp
import shapely
from scipy.stats import spearmanr

from pipeline.accessibility import WalkGraph, facility_distance_matrix
from pipeline.catchment import greedy_max_coverage, within
from pipeline.sources import ANALYSIS_CRS

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"

NEAR_M = 400.0
SMALL_CHILD_M = 200.0
TEEN_M = 1000.0
THRESHOLDS_M = [200, 300, 400, 500, 800, 1000]
MIN_CHILDREN_FOR_AREA_STATS = 100  # planning areas below this are too small for stable shares
# Block types (Umweltatlas "Stadtstruktur") in which homes typically have a private garden.
GARDEN_TYPES = {
    "Freistehende Einfamilienhäuser mit Gärten",
    "Reihen- und Doppelhäuser mit Gärten",
    "Villen und Stadtvillen mit parkartigen Gärten (überwiegend 1870er - 1945)",
    "Verdichtung im Einzelhausgebiet, Mischbebauung mit Garten und halbprivater Umgrünung (1870er bis heute)",
    "Dörfliche Mischbebauung",
    "Wochenendhaus- und kleingartenähnliches Gebiet",
    "Kleingartenanlage",
}
OSM_NOT_PUBLIC_ACCESS = {"private", "customers", "no", "permit", "residents"}
SCENARIO_STEPS = 25
CANDIDATE_MIN_M2 = 2000.0  # smallest green space considered as a site for a new playground
SCHOOL_SURROUNDINGS_M = 250.0
SCHOOL_RUN_HOURS = {7, 8, 13, 14, 15, 16}
STATUS_ORDER = ["hoch", "mittel", "niedrig", "sehr niedrig"]


def share(weights: pd.Series, mask) -> float:
    return round(float(weights[mask].sum() / weights.sum()), 4)


def weighted_quantiles(values, weights, quantiles=(0.1, 0.25, 0.5, 0.75, 0.9)) -> list[float]:
    values, weights = np.asarray(values), np.asarray(weights)
    order = np.argsort(values)
    cumulative = np.cumsum(weights[order]) / weights.sum()
    return [round(float(values[order][min(np.searchsorted(cumulative, q), len(values) - 1)]), 2) for q in quantiles]


def read_raw(name: str) -> gpd.GeoDataFrame:
    return gpd.read_file(RAW / f"{name}.geojson")


def lon_lat(points: gpd.GeoSeries) -> tuple[np.ndarray, np.ndarray]:
    """Representative points of the geometries in WGS84, rounded to about 1 m."""
    wgs = gpd.GeoSeries(points.representative_point(), crs=ANALYSIS_CRS).to_crs("EPSG:4326")
    return wgs.x.round(5).values, wgs.y.round(5).values


# --------------------------------------------------------------------------- findings


def straight_line_versus_walking(homes: pd.DataFrame) -> dict:
    children = homes["children"]
    rows = {}
    for threshold in THRESHOLDS_M:
        rows[threshold] = {
            "straight_line": share(children, homes["playground_air_m"] <= threshold),
            "walking": share(children, homes["playground_net_m"] <= threshold),
            "walking_only_secured_main_road_crossings": share(children, homes["playground_secured_crossings_m"] <= threshold),
            "walking_without_main_road": share(children, homes["playground_no_main_road_m"] <= threshold),
        }
    lost = (homes["playground_air_m"] <= NEAR_M) & (homes["playground_net_m"] > NEAR_M)
    return {
        "share_of_children_within_threshold": rows,
        "children_within_400_straight_but_not_walking": int(children[lost].sum()),
        "children_needing_main_road_crossing_for_400": int(children[(homes["playground_net_m"] <= NEAR_M) & (homes["playground_no_main_road_m"] > NEAR_M)].sum()),
        "children_needing_unsecured_main_road_crossing_for_400": int(children[(homes["playground_net_m"] <= NEAR_M) & (homes["playground_secured_crossings_m"] > NEAR_M)].sum()),
        "walking_distance_quantiles_m": dict(zip(["p10", "p25", "p50", "p75", "p90"], weighted_quantiles(homes["playground_net_m"], children))),
        "straight_distance_quantiles_m": dict(zip(["p10", "p25", "p50", "p75", "p90"], weighted_quantiles(homes["playground_air_m"], children))),
    }


def barriers_between_children_and_playgrounds(homes: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """For children who have a playground within 400 m straight-line but not on foot:
    which linear barrier lies on the straight line to that playground?"""
    playgrounds = read_raw("playgrounds")
    barriers = gpd.read_file(INTERIM / "osm_barriers.geojson")
    lost = homes[(homes["playground_air_m"] <= NEAR_M) & (homes["playground_net_m"] > NEAR_M)].copy()
    origins = shapely.points(lost[["x", "y"]].values)
    tree = shapely.STRtree(playgrounds.geometry.values)
    nearest = tree.nearest(origins)
    target_points = shapely.shortest_line(origins, playgrounds.geometry.values[nearest])
    lost["playground"] = playgrounds["namenr"].values[nearest]
    lost["playground_pitid"] = playgrounds["pitid"].values[nearest]
    barrier_tree = shapely.STRtree(barriers.geometry.values)
    line_index, barrier_index = barrier_tree.query(target_points, predicate="intersects")
    kinds = pd.DataFrame({"line": line_index, "kind": barriers["kind"].values[barrier_index]}).drop_duplicates()
    for kind in ["railway", "motorway", "water"]:
        lost[kind] = False
        lost.iloc[kinds.loc[kinds["kind"] == kind, "line"].unique(), lost.columns.get_loc(kind)] = True
    lost["no_linear_barrier"] = ~lost[["railway", "motorway", "water"]].any(axis=1)
    lost["detour_factor"] = lost["playground_net_m"] / lost["playground_air_m"].clip(lower=50)
    children = lost["children"]
    summary = {
        "children_affected": int(children.sum()),
        "share_by_barrier_on_straight_line": {kind: share(children, lost[kind]) for kind in ["railway", "motorway", "water", "no_linear_barrier"]},
        "children_with_walk_over_800_despite_400_straight": int(children[lost["playground_net_m"] > 800].sum()),
    }
    # Playgrounds that are close to many children as the crow flies but not on foot.
    cases = (
        lost.groupby(["playground_pitid", "playground"])
        .agg(children_cut_off=("children", "sum"), home_locations=("children", "size"), median_walk_m=("playground_net_m", "median"), median_straight_m=("playground_air_m", "median"),
             railway=("railway", "max"), motorway=("motorway", "max"), water=("water", "max"), plr_id=("plr_id", "first"))
        .sort_values("children_cut_off", ascending=False)
        .reset_index()
    )
    return summary, cases


def supply_per_child(homes: pd.DataFrame, plr: pd.DataFrame) -> dict:
    children, residents = homes["children"], homes["residents"]
    net_area = pd.read_csv(INTERIM / "playgrounds.csv")["nettospfl"].sum()
    city_per_child = net_area / children.sum()
    return {
        "net_play_area_ha": round(net_area / 1e4, 1),
        "city_m2_per_resident": round(net_area / residents.sum(), 3),
        "city_m2_per_child": round(city_per_child, 2),
        "reachable_m2_per_child_400_quantiles": dict(zip(["p10", "p25", "p50", "p75", "p90"], weighted_quantiles(homes["play_m2_per_child_400"], children))),
        "reachable_m2_per_child_1000_quantiles": dict(zip(["p10", "p25", "p50", "p75", "p90"], weighted_quantiles(homes["play_m2_per_child_1000"], children))),
        "share_children_no_playground_within_400": share(children, homes["play_m2_per_child_400"] == 0),
        "share_children_below_1_m2_within_400": share(children, homes["play_m2_per_child_400"] < 1),
        "share_children_above_city_average_within_400": share(children, homes["play_m2_per_child_400"] >= city_per_child),
        "planning_areas_without_playground_inside": int((plr["playgrounds_inside"] == 0).sum()),
        "children_in_planning_areas_without_playground_inside": int(plr.loc[plr["playgrounds_inside"] == 0, "children"].sum()),
        "of_those_children_with_playground_within_400_walking": int(
            homes.loc[homes["plr_id"].isin(plr.index[plr["playgrounds_inside"] == 0]) & (homes["playground_net_m"] <= NEAR_M), "children"].sum()
        ),
        "spearman_per_resident_inside_vs_per_child_reachable": round(
            float(spearmanr(plr["play_m2_per_resident_inside"], plr["play_m2_per_child_1000"], nan_policy="omit").statistic), 2
        ),
    }


def by_group(plr: pd.DataFrame, column: str, order: list[str] | None = None) -> dict:
    """Child-weighted averages of planning-area indicators per category."""
    result = {}
    for key, group in plr.groupby(column):
        children, teens = group["children"], group["age_10_17"]
        result[key] = {
            "planning_areas": len(group),
            "children": int(children.sum()),
            "share_playground_400_walking": round(float(np.average(group["playground_share_400_net"], weights=children)), 3),
            "reachable_m2_per_child_400": round(float(np.average(group["play_m2_per_child_400"], weights=children)), 2),
            "reachable_m2_per_child_1000": round(float(np.average(group["play_m2_per_child_1000"], weights=children)), 2),
            "share_teens_youth_facility_1000": round(float(np.average(group["youth_share_1000_net"].fillna(0), weights=teens)), 3),
            "youth_places_per_100_teens": round(float(np.average(group["youth_places_per_100"].fillna(0), weights=teens)), 1),
            "share_green_400_walking": round(float(np.average(group["green_share_400_net"], weights=children)), 3),
            "residents_per_ha": round(float(np.average(group["residents_per_ha_populated"], weights=children)), 0),
            "children_change_2022_2025": round(float(children.sum() / group["children_2022"].sum() - 1), 3),
        }
    return {key: result[key] for key in order} if order else result


def housing_types(homes: pd.DataFrame) -> dict:
    children = homes["children"]
    garden = homes["typklar"].isin(GARDEN_TYPES)
    far = homes["playground_net_m"] > NEAR_M
    estates = homes["typklar"].str.startswith("Großsiedlung")
    return {
        "children_in_garden_housing": int(children[garden].sum()),
        "children_in_multi_storey_housing": int(children[~garden].sum()),
        "share_400_walking_garden_housing": share(children[garden], ~far[garden]),
        "share_400_walking_multi_storey": share(children[~garden], ~far[~garden]),
        "children_multi_storey_without_playground_400": int(children[~garden & far].sum()),
        "children_multi_storey_without_playground_400_incl_osm": int(children[~garden & (homes["playground_incl_osm_net_m"] > NEAR_M)].sum()),
        "children_multi_storey_without_playground_800": int(children[~garden & (homes["playground_net_m"] > 800)].sum()),
        "children_in_large_housing_estates": int(children[estates].sum()),
        "share_400_walking_large_housing_estates": share(children[estates], ~far[estates]),
        "reachable_m2_per_child_400_large_estates": round(float(np.average(homes.loc[estates, "play_m2_per_child_400"], weights=children[estates])), 2),
        "reachable_m2_per_child_400_old_dense_blocks": round(
            float(np.average(homes.loc[homes["typklar"].str.contains("Hinterhof"), "play_m2_per_child_400"], weights=children[homes["typklar"].str.contains("Hinterhof")])), 2
        ),
    }


def age_groups(homes: pd.DataFrame) -> dict:
    small, school_age, teens = homes["age_0_5"], homes["age_6_9"], homes["age_10_17"]
    return {
        "children_0_5": int(small.sum()),
        "children_6_9": int(school_age.sum()),
        "children_10_17": int(teens.sum()),
        "share_0_5_playground_within_200": share(small, homes["playground_net_m"] <= SMALL_CHILD_M),
        "share_0_5_daycare_within_400": share(small, homes["daycare_net_m"] <= NEAR_M),
        "share_6_9_playground_within_400": share(school_age, homes["playground_net_m"] <= NEAR_M),
        "share_6_9_primary_school_within_1000": share(school_age, homes["primary_school_net_m"] <= 1000),
        "median_primary_school_m": weighted_quantiles(homes["primary_school_net_m"], school_age, [0.5])[0],
        "median_library_m": weighted_quantiles(homes["library_net_m"], homes["children"], [0.5])[0],
        "share_children_library_within_1000": share(homes["children"], homes["library_net_m"] <= 1000),
        "share_10_17_youth_facility_within_1000": share(teens, homes["youth_net_m"] <= TEEN_M),
        "teens_without_youth_facility_within_1000": int(teens[homes["youth_net_m"] > TEEN_M].sum()),
        "teens_without_youth_facility_within_2000": int(teens[homes["youth_net_m"] > 2000].sum()),
        "median_youth_facility_m": weighted_quantiles(homes["youth_net_m"], teens, [0.5])[0],
        "median_playground_m": weighted_quantiles(homes["playground_net_m"], homes["children"], [0.5])[0],
        "median_daycare_m": weighted_quantiles(homes["daycare_net_m"], small, [0.5])[0],
        "median_sports_site_m": weighted_quantiles(homes["sports_net_m"], teens, [0.5])[0],
        "youth_places_per_100_teens_quantiles": dict(zip(["p10", "p25", "p50", "p75", "p90"], weighted_quantiles(homes["youth_places_per_100_1000"], teens))),
    }


def growth(plr: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    valid = plr[plr["children_2022"] >= MIN_CHILDREN_FOR_AREA_STATS].copy()
    valid["children_added"] = valid["children"] - valid["children_2022"]
    growing = valid[valid["children_change_2022_2025"] >= 0.10]
    shrinking = valid[valid["children_change_2022_2025"] <= -0.05]
    mean = lambda frame, column: round(float(np.average(frame[column], weights=frame["children"])), 3)
    summary = {
        "children_2022": int(plr["children_2022"].sum()),
        "children_2025": int(plr["children"].sum()),
        "city_change": round(float(plr["children"].sum() / plr["children_2022"].sum() - 1), 4),
        "planning_areas_growing_10pct": len(growing),
        "children_added_in_growing_areas": int(growing["children_added"].sum()),
        "share_400_walking_growing": mean(growing, "playground_share_400_net"),
        "share_400_walking_shrinking": mean(shrinking, "playground_share_400_net"),
        "reachable_m2_per_child_1000_growing": mean(growing, "play_m2_per_child_1000"),
        "reachable_m2_per_child_1000_shrinking": mean(shrinking, "play_m2_per_child_1000"),
        "spearman_change_vs_share_400": round(float(spearmanr(valid["children_change_2022_2025"], valid["playground_share_400_net"]).statistic), 2),
        "by_city_zone": {zone: round(float(g["children"].sum() / g["children_2022"].sum() - 1), 4) for zone, g in plr.groupby("stadtraum_name")},
    }
    cases = growing[growing["playground_share_400_net"] < 0.5].sort_values("children_added", ascending=False)
    columns = ["plr_name", "bez", "children_2022", "children", "children_change_2022_2025", "playground_share_400_net", "play_m2_per_child_1000", "youth_share_1000_net"]
    return summary, cases[columns]


def osm_robustness(homes: pd.DataFrame) -> dict:
    """How much does the picture change if playgrounds known to OSM but not in the
    official register of public playgrounds (e.g. on housing-estate land) are added?"""
    osm = gpd.read_file(INTERIM / "osm_playgrounds.geojson")
    osm = osm[osm.within(read_raw("lor_plr").union_all())]
    children = homes["children"]
    estates = homes["typklar"].str.startswith("Großsiedlung")
    garden = homes["typklar"].isin(GARDEN_TYPES)
    with_osm = homes["playground_incl_osm_net_m"] <= NEAR_M
    return {
        "osm_playgrounds_in_berlin": len(osm),
        "osm_playgrounds_not_marked_private": int((~osm["access"].isin(OSM_NOT_PUBLIC_ACCESS)).sum()),
        "osm_playgrounds_with_wheelchair_tag": int(osm["wheelchair"].notna().sum()),
        "osm_playgrounds_wheelchair_yes": int((osm["wheelchair"] == "yes").sum()),
        "official_public_playgrounds": len(read_raw("playgrounds")),
        "share_children_400_walking_official_only": share(children, homes["playground_net_m"] <= NEAR_M),
        "share_children_400_walking_official_plus_osm": share(children, with_osm),
        "share_children_large_estates_400_official_only": share(children[estates], homes.loc[estates, "playground_net_m"] <= NEAR_M),
        "share_children_large_estates_400_official_plus_osm": share(children[estates], with_osm[estates]),
        "children_multi_storey_without_any_playground_400": int(children[~garden & ~with_osm].sum()),
    }


def schoolyard_scenario(homes: pd.DataFrame, served_column: str = "playground_net_m") -> tuple[dict, pd.DataFrame]:
    """Hypothetical: open yards of public primary schools outside school hours.

    Greedy maximum coverage: repeatedly pick the school that brings the most children,
    who so far have no public playground within 400 m on foot, within 400 m of an open
    yard. Children are counted once (overlapping catchments are not double counted).
    """
    schools = read_raw("schools")
    schools = schools[(schools["schulart"] == "Grundschule") & (schools["traeger"] == "oeffentlich")].reset_index(drop=True)
    reach = within(sp.load_npz(INTERIM / "primary_school_matrix.npz"), NEAR_M)
    uncovered = np.where(homes[served_column].values > NEAR_M, homes["children"].values, 0.0)
    school_lon, school_lat = lon_lat(schools.geometry)
    total_without = uncovered.sum()
    all_schools_gain = float(uncovered[np.asarray(reach.sum(axis=0)).ravel() > 0].sum())
    steps = [
        {"step": step, "id": schools.loc[school, "bsn"], "name": schools.loc[school, "schulname"], "district": schools.loc[school, "bezirk"],
         "lon": school_lon[school], "lat": school_lat[school], "children_newly_reached": int(round(gain))}
        for step, (school, gain) in enumerate(greedy_max_coverage(reach, uncovered, SCENARIO_STEPS), start=1)
    ]
    table = pd.DataFrame(steps)
    table["cumulative"] = table["children_newly_reached"].cumsum()
    summary = {
        "public_primary_schools": len(schools),
        "children_without_playground_400": int(total_without),
        "newly_reached_if_all_yards_open": int(all_schools_gain),
        "newly_reached_top_10": int(table["children_newly_reached"].head(10).sum()),
        "newly_reached_top_25": int(table["children_newly_reached"].sum()),
    }
    return summary, table


def detours(homes: pd.DataFrame) -> dict:
    """Ratio of walking to straight-line distance to the nearest playground (each measured to its own nearest)."""
    factor = homes["playground_net_m"] / homes["playground_air_m"].clip(lower=50)
    children = homes["children"]
    bands = [(0, 1.25), (1.25, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, np.inf)]
    return {
        "median_detour_factor": weighted_quantiles(factor, children, [0.5])[0],
        "share_children_by_detour_factor": {f"{low}-{high}": share(children, (factor >= low) & (factor < high)) for low, high in bands},
        "children_with_factor_3_or_more": int(children[factor >= 3].sum()),
    }


def new_playground_scenario(homes: pd.DataFrame, served_column: str = "playground_net_m") -> tuple[dict, pd.DataFrame]:
    """Hypothetical: a new playground in an existing public green space that has none.

    Candidates are public green spaces of at least CANDIDATE_MIN_M2 without an official
    playground within 50 m. Greedy maximum coverage over children who currently have no
    public playground within 400 m on foot; multi-storey housing is reported separately.
    Ownership, nature protection, space and cost are unknown: this ranks where the
    question is worth asking, not where building is feasible.
    """
    graph = WalkGraph.load()
    green = read_raw("green_spaces")
    playgrounds = read_raw("playgrounds")
    near_playground = gpd.sjoin(green[["geometry"]], gpd.GeoDataFrame(geometry=playgrounds.buffer(50), crs=ANALYSIS_CRS), predicate="intersects").index.unique()
    candidates = green[(green["katasterfl"] >= CANDIDATE_MIN_M2) & ~green.index.isin(near_playground)].reset_index(drop=True)
    candidate_lon, candidate_lat = lon_lat(candidates.geometry)
    home_nodes, _ = graph.snap(homes[["x", "y"]].values, exclude=graph.node_major)
    reach = within(facility_distance_matrix(graph, graph.entrance_nodes(candidates.geometry), home_nodes, NEAR_M), NEAR_M)
    far = homes[served_column].values > NEAR_M
    multi_storey = ~homes["typklar"].isin(GARDEN_TYPES).values
    uncovered = np.where(far, homes["children"].values, 0.0)
    remaining_multi_storey = np.where(far & multi_storey, homes["children"].values, 0.0)
    steps = []
    for step, (candidate, gain) in enumerate(greedy_max_coverage(reach, uncovered, SCENARIO_STEPS), start=1):
        covered = reach[candidate].indices
        steps.append({"step": step, "id": candidates.loc[candidate, "pitid"], "name": candidates.loc[candidate, "namenr"], "district": candidates.loc[candidate, "bezirkname"],
                      "lon": candidate_lon[candidate], "lat": candidate_lat[candidate], "area_m2": candidates.loc[candidate, "katasterfl"],
                      "children_newly_reached": int(round(gain)), "of_those_in_multi_storey_housing": int(round(remaining_multi_storey[covered].sum()))})
        remaining_multi_storey[covered] = 0.0
    table = pd.DataFrame(steps)
    table["cumulative"] = table["children_newly_reached"].cumsum()
    summary = {
        "candidate_green_spaces": len(candidates),
        "children_without_playground_400": int(homes["children"][far].sum()),
        "newly_reached_top_10": int(table["children_newly_reached"].head(10).sum()),
        "newly_reached_top_25": int(table["children_newly_reached"].sum()),
        "top_25_of_those_in_multi_storey_housing": int(table["of_those_in_multi_storey_housing"].sum()),
    }
    return summary, table


def commercial_areas(homes: pd.DataFrame) -> dict:
    """Children living in blocks classified as commercial/industrial."""
    commercial = homes["typklar"].str.startswith("Gewerbe- und Industriegebiet")
    children = homes["children"]
    return {
        "children": int(children[commercial].sum()),
        "share_playground_400_walking": share(children[commercial], homes.loc[commercial, "playground_net_m"] <= NEAR_M),
        "share_playground_400_walking_incl_osm": share(children[commercial], homes.loc[commercial, "playground_incl_osm_net_m"] <= NEAR_M),
        "median_playground_m": weighted_quantiles(homes.loc[commercial, "playground_net_m"], children[commercial], [0.5])[0],
    }


def accidents_around_schools() -> tuple[dict, pd.DataFrame]:
    """Accidents with injured pedestrians/cyclists near public primary schools (2018-2024).
    The Unfallatlas has no age of those involved: this is an indicator of the traffic
    environment on school routes, not a count of child accidents."""
    import zipfile

    from pipeline.sources import UNFALLATLAS_YEARS

    frames = []
    for year in UNFALLATLAS_YEARS:
        archive = zipfile.ZipFile(RAW / f"unfallatlas_{year}.zip")
        name = next(n for n in archive.namelist() if n.lower().endswith((".csv", ".txt")) and "schema" not in n.lower())
        table = pd.read_csv(archive.open(name), sep=";", dtype=str, encoding="latin-1")
        table.columns = [c.upper() for c in table.columns]
        frames.append(table[table["ULAND"] == "11"])
    accidents = pd.concat(frames, ignore_index=True)
    accidents = accidents[(accidents["ISTFUSS"] == "1") | (accidents["ISTRAD"] == "1")]
    x = accidents["XGCSWGS84"].str.replace(",", ".").astype(float)
    y = accidents["YGCSWGS84"].str.replace(",", ".").astype(float)
    points = gpd.GeoDataFrame(accidents, geometry=gpd.points_from_xy(x, y), crs="EPSG:4326").to_crs(ANALYSIS_CRS)
    school_run = points["USTUNDE"].astype(int).isin(SCHOOL_RUN_HOURS) & points["UWOCHENTAG"].astype(int).between(2, 6)
    schools = read_raw("schools")
    schools = schools[(schools["schulart"] == "Grundschule") & (schools["traeger"] == "oeffentlich")]
    around = gpd.GeoDataFrame(schools[["bsn", "schulname", "bezirk"]], geometry=schools.buffer(SCHOOL_SURROUNDINGS_M), crs=ANALYSIS_CRS)
    joined = gpd.sjoin(points[school_run], around, predicate="within")
    counts = joined.groupby(["bsn", "schulname", "bezirk"]).size().rename("accidents_school_run_250m").reset_index().sort_values("accidents_school_run_250m", ascending=False)
    per_school = counts.set_index("bsn")["accidents_school_run_250m"].reindex(schools["bsn"]).fillna(0)
    summary = {
        "accidents_with_pedestrians_or_cyclists_2018_2024": len(points),
        "of_those_on_weekdays_at_school_run_hours": int(school_run.sum()),
        "school_run_accidents_within_250m_of_a_public_primary_school": int(joined.index.nunique()),
        "median_per_school": float(per_school.median()),
        "p90_per_school": float(per_school.quantile(0.9)),
        "max_per_school": int(per_school.max()),
        "schools_without_any": int((per_school == 0).sum()),
    }
    return summary, counts


def daycare_capacity(homes: pd.DataFrame, plr: pd.DataFrame) -> dict:
    """Licensed daycare places per child under 6 (two-step catchment, 1000 m walking).
    Licensed places are an upper bound of actual capacity; free places are not published."""
    daycare = read_raw("daycare")
    places = pd.to_numeric(daycare["e_platz"], errors="coerce")
    small = homes["age_0_5"]
    valid = plr[plr["children"] >= MIN_CHILDREN_FOR_AREA_STATS]
    return {
        "daycare_facilities": len(daycare),
        "facilities_without_capacity_value": int(places.isna().sum()),
        "licensed_places": int(places.sum()),
        "children_0_5": int(small.sum()),
        "city_places_per_child_0_5": round(float(places.sum() / small.sum()), 3),
        "reachable_places_per_child_1000_quantiles": dict(zip(["p10", "p25", "p50", "p75", "p90"], weighted_quantiles(homes["daycare_places_per_child_1000"], small))),
        "spearman_places_per_child_vs_child_poverty": round(float(spearmanr(valid["daycare_places_per_child"], valid["child_poverty_pct"], nan_policy="omit").statistic), 2),
        "places_per_child_by_status": {
            status: round(float(np.average(group["daycare_places_per_child"].fillna(0), weights=group["age_0_5"])), 2) for status, group in valid.groupby("status_index")
        },
    }


def police_statistics_2025() -> dict:
    """Polizei Berlin, traffic accidents 2025: people involved by age group.
    The file has street names but no coordinates, so it cannot be mapped to planning areas."""
    table = pd.read_csv(RAW / "accidents_berlin_2025.csv", sep=";", encoding="latin-1", low_memory=False)
    involved = table["alterjahre"].value_counts()
    with_child = table.loc[table["alterjahre"].isin(["Kinder", "Jugendliche"]), "paginiernr"].nunique()
    return {
        "people_involved": len(table),
        "accidents": int(table["paginiernr"].nunique()),
        "children_involved": int(involved.get("Kinder", 0)),
        "adolescents_involved": int(involved.get("Jugendliche", 0)),
        "accidents_with_children_or_adolescents": int(with_child),
        "has_coordinates": False,
    }


def data_gaps() -> dict:
    playgrounds = read_raw("playgrounds")
    youth = read_raw("youth_facilities")
    sports = read_raw("sports_sites")
    blank = lambda series: int((series.fillna("").str.strip() == "").sum())
    return {
        "playgrounds": len(playgrounds),
        "playgrounds_without_construction_year": blank(playgrounds["baujahr"]),
        "playgrounds_without_renovation_year": blank(playgrounds["sanierjahr"]),
        "playgrounds_net_area_zero": int((playgrounds["nettospfl"] == 0).sum()),
        "playgrounds_without_dedication_status": blank(playgrounds["widmung"]),
        "playground_attributes_on_accessibility_or_equipment": 0,
        "youth_facilities": len(youth),
        "youth_facilities_with_target_group_flag": int(youth["zielgr1"].notna().sum()),
        "sports_sites": len(sports),
        "sports_sites_without_area": int(sports["gesamtflaeche_standort_qm"].isna().sum()),
        "sports_sites_on_school_grounds": int(sports["schulnummer"].notna().sum()),
    }


def comparable_pairs(plr: pd.DataFrame) -> pd.DataFrame:
    """Pairs of planning areas that are alike in density, child share, child poverty and
    number of children, but differ strongly in reachable play area per child."""
    features = ["residents_per_ha_populated", "child_share", "child_poverty_pct", "children"]
    valid = plr[(plr["children"] >= 500)].dropna(subset=features + ["play_m2_per_child_1000"])
    z = (valid[features] - valid[features].mean()) / valid[features].std()
    distance = np.sqrt(((z.values[:, None, :] - z.values[None, :, :]) ** 2).sum(axis=2))
    supply = valid["play_m2_per_child_1000"].values
    rows = []
    for i, j in zip(*np.where((distance < 0.35) & (np.triu(np.ones_like(distance), 1) > 0))):
        low, high = (i, j) if supply[i] < supply[j] else (j, i)
        rows.append({"similarity_distance": round(float(distance[i, j]), 2), "ratio": round(float(supply[high] / max(supply[low], 0.05)), 1),
                     **{f"low_{c}": valid.iloc[low][c] for c in ["plr_name", "bez", *features, "play_m2_per_child_1000", "playground_share_400_net"]},
                     **{f"high_{c}": valid.iloc[high][c] for c in ["plr_name", "bez", *features, "play_m2_per_child_1000", "playground_share_400_net"]}})
    return pd.DataFrame(rows).sort_values("ratio", ascending=False)


def positive_outliers(plr: pd.DataFrame) -> pd.DataFrame:
    """Dense planning areas with high child poverty that are nevertheless well supplied."""
    valid = plr[plr["children"] >= 500]
    dense_poor = valid[(valid["residents_per_ha_populated"] >= valid["residents_per_ha_populated"].quantile(0.6)) & (valid["child_poverty_pct"] >= valid["child_poverty_pct"].quantile(0.75))]
    columns = ["plr_name", "bez", "children", "residents_per_ha_populated", "child_poverty_pct", "play_m2_per_child_1000", "playground_share_400_net", "youth_share_1000_net", "env_burdens"]
    return dense_poor.sort_values("play_m2_per_child_1000", ascending=False)[columns]


def multiple_disadvantage(plr: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Where several unfavourable conditions coincide (each condition is listed, no index)."""
    valid = plr[plr["children"] >= MIN_CHILDREN_FOR_AREA_STATS].copy()
    valid["low_play_supply"] = valid["play_m2_per_child_1000"] <= valid["play_m2_per_child_1000"].quantile(0.25)
    valid["high_env_burden"] = valid["env_burdens"].isin(["dreifach", "vierfach"])
    valid["high_child_poverty"] = valid["child_poverty_pct"] >= valid["child_poverty_pct"].quantile(0.75)
    valid["little_living_space"] = valid["living_space_m2_per_resident"] <= valid["living_space_m2_per_resident"].quantile(0.25)
    flags = ["low_play_supply", "high_env_burden", "high_child_poverty", "little_living_space"]
    valid["conditions"] = valid[flags].sum(axis=1)
    summary = {
        "planning_areas_considered": len(valid),
        "children_by_number_of_conditions": {int(k): int(v) for k, v in valid.groupby("conditions")["children"].sum().items()},
        "planning_areas_by_number_of_conditions": {int(k): int(v) for k, v in valid["conditions"].value_counts().sort_index().items()},
        "share_high_env_burden_areas_with_low_play_supply": round(float(valid.loc[valid["high_env_burden"], "low_play_supply"].mean()), 3),
        "share_other_areas_with_low_play_supply": round(float(valid.loc[~valid["high_env_burden"], "low_play_supply"].mean()), 3),
        "share_children_400_walking_high_env_burden": round(float(np.average(valid.loc[valid["high_env_burden"], "playground_share_400_net"], weights=valid.loc[valid["high_env_burden"], "children"])), 3),
        "share_children_400_walking_no_strong_burden": round(float(np.average(valid.loc[valid["env_burdens"] == "keine starke Belastung", "playground_share_400_net"], weights=valid.loc[valid["env_burdens"] == "keine starke Belastung", "children"])), 3),
    }
    cases = valid[valid["conditions"] >= 3].sort_values(["conditions", "children"], ascending=False)
    columns = ["plr_name", "bez", "children", "conditions", *flags, "play_m2_per_child_1000", "child_poverty_pct", "living_space_m2_per_resident", "env_burdens"]
    return summary, cases[columns]


def correlations(plr: pd.DataFrame) -> dict:
    valid = plr[plr["children"] >= MIN_CHILDREN_FOR_AREA_STATS]
    pairs = [
        ("child_poverty_pct", "playground_share_400_net"), ("child_poverty_pct", "play_m2_per_child_1000"), ("child_poverty_pct", "youth_median_m"),
        ("residents_per_ha_populated", "playground_share_400_net"), ("residents_per_ha_populated", "play_m2_per_child_1000"),
        ("living_space_m2_per_resident", "playground_share_400_net"), ("child_share", "play_m2_per_child_1000"),
        ("children_change_2022_2025", "playground_share_400_net"), ("children_change_2022_2025", "youth_median_m"),
    ]
    return {f"{a} ~ {b}": round(float(spearmanr(valid[a], valid[b], nan_policy="omit").statistic), 2) for a, b in pairs}


def main() -> None:
    homes = pd.read_csv(INTERIM / "homes_supply.csv", dtype={"block_id": str, "plr_id": str})
    plr = pd.read_csv(PROCESSED / "plr_indicators.csv", dtype={"plr_id": str}).set_index("plr_id")
    stats_plr = plr[plr["children"] >= MIN_CHILDREN_FOR_AREA_STATS]
    barrier_summary, barrier_cases = barriers_between_children_and_playgrounds(homes)
    growth_summary, growth_cases = growth(plr)
    scenario_summary, scenario_steps = schoolyard_scenario(homes)
    accident_summary, accident_schools = accidents_around_schools()
    burden_summary, burden_cases = multiple_disadvantage(plr)
    green_summary, green_steps = new_playground_scenario(homes)
    # Conservative variants: only children without ANY known playground (official or OSM) count as not yet served.
    scenario_summary_strict, scenario_steps_strict = schoolyard_scenario(homes, "playground_incl_osm_net_m")
    green_summary_strict, green_steps_strict = new_playground_scenario(homes, "playground_incl_osm_net_m")

    findings = {
        "reference": {"population": "31.12.2025 (blocks)", "residents": int(homes["residents"].sum()), "children_under_18": int(homes["children"].sum()), "populated_blocks": int(homes["block_id"].nunique()), "home_locations": len(homes), "planning_areas": len(plr)},
        "straight_line_versus_walking": straight_line_versus_walking(homes),
        "barriers": barrier_summary,
        "supply_per_child": supply_per_child(homes, plr),
        "by_social_status": by_group(stats_plr, "status_index", STATUS_ORDER),
        "by_city_zone": by_group(stats_plr, "stadtraum_name"),
        "by_district": by_group(stats_plr, "bez"),
        "by_environmental_burden": by_group(stats_plr, "env_burdens"),
        "housing_types": housing_types(homes),
        "age_groups": age_groups(homes),
        "growth_2022_2025": growth_summary,
        "osm_robustness": osm_robustness(homes),
        "detours": detours(homes),
        "commercial_areas": commercial_areas(homes),
        "schoolyard_scenario": scenario_summary,
        "schoolyard_scenario_incl_osm": scenario_summary_strict,
        "new_playground_scenario_incl_osm": green_summary_strict,
        "accidents_around_primary_schools": accident_summary,
        "daycare_capacity": daycare_capacity(homes, plr),
        "new_playground_scenario": green_summary,
        "multiple_disadvantage": burden_summary,
        "correlations_spearman": correlations(plr),
        "police_statistics_2025": police_statistics_2025(),
        "data_gaps": data_gaps(),
    }
    (PROCESSED / "findings.json").write_text(json.dumps(findings, indent=2, ensure_ascii=False))

    barrier_cases.head(50).to_csv(PROCESSED / "cases_barriers.csv", index=False)
    growth_cases.to_csv(PROCESSED / "cases_growth_low_access.csv")
    scenario_steps.to_csv(PROCESSED / "scenario_schoolyards.csv", index=False)
    green_steps.to_csv(PROCESSED / "scenario_new_playgrounds.csv", index=False)
    scenario_steps_strict.to_csv(PROCESSED / "scenario_schoolyards_incl_osm.csv", index=False)
    green_steps_strict.to_csv(PROCESSED / "scenario_new_playgrounds_incl_osm.csv", index=False)
    accident_schools.head(50).to_csv(PROCESSED / "cases_school_surroundings_accidents.csv", index=False)
    burden_cases.to_csv(PROCESSED / "cases_multiple_conditions.csv")
    comparable_pairs(plr).head(40).to_csv(PROCESSED / "cases_comparable_pairs.csv", index=False)
    positive_outliers(plr).head(25).to_csv(PROCESSED / "cases_positive_outliers.csv")
    print(f"wrote {PROCESSED / 'findings.json'}")


if __name__ == "__main__":
    main()
