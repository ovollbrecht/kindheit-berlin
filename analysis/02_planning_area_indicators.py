"""Aggregate home-level results and context data to the 542 planning areas (LOR-PLR).

Writes data/processed/plr_indicators.csv and data/interim/homes_supply.csv.

Run:  python -m analysis.02_planning_area_indicators
"""

import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import scipy.sparse as sp

from pipeline.catchment import two_step_supply, within
from pipeline.sources import ANALYSIS_CRS, UNFALLATLAS_YEARS

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"

# Walking distances by age group follow DIN 18034 (play areas): 200 m for under-6,
# 400 m for 6-11, 1000 m for 12 and older. 400 m is the default "near home" threshold.
NEAR_M = 400.0
FAR_M = 1000.0
BERLIN_STATE_CODE = "11"
SCHOOL_RUN_HOURS = {7, 8, 13, 14, 15, 16}
WEEKDAYS_MON_FRI = {2, 3, 4, 5, 6}  # Unfallatlas: 1 = Sunday ... 7 = Saturday


def read(name: str) -> gpd.GeoDataFrame:
    return gpd.read_file(RAW / f"{name}.geojson")


def weighted_median(values: pd.Series, weights: pd.Series) -> float:
    if weights.sum() == 0:
        return np.nan
    order = np.argsort(values.values)
    cumulative = np.cumsum(weights.values[order])
    return float(values.values[order][np.searchsorted(cumulative, cumulative[-1] / 2)])


def child_population_2022() -> pd.Series:
    blocks_2022 = read("blocks_population_2022")
    blocks_2022["children_2022"] = blocks_2022[["alter_u6", "alter_6_u10", "alter_10_u18"]].sum(axis=1)
    points = blocks_2022.set_geometry(blocks_2022.representative_point())
    joined = gpd.sjoin(points, read("lor_plr")[["plr_id", "geometry"]], predicate="within", how="left")
    return joined.groupby("plr_id")["children_2022"].sum()


def accidents_by_planning_area(areas: gpd.GeoDataFrame) -> pd.DataFrame:
    """Accidents with personal injury involving pedestrians or cyclists, 2018-2024."""
    frames = []
    for year in UNFALLATLAS_YEARS:
        archive = zipfile.ZipFile(RAW / f"unfallatlas_{year}.zip")
        name = next(n for n in archive.namelist() if n.lower().endswith((".csv", ".txt")) and "schema" not in n.lower())
        table = pd.read_csv(archive.open(name), sep=";", decimal=",", dtype=str, encoding="latin-1")
        table.columns = [c.upper() for c in table.columns]
        frames.append(table[table["ULAND"] == BERLIN_STATE_CODE])
    accidents = pd.concat(frames, ignore_index=True)
    for column in ["XGCSWGS84", "YGCSWGS84"]:
        accidents[column] = accidents[column].str.replace(",", ".").astype(float)
    vulnerable = accidents[(accidents["ISTFUSS"] == "1") | (accidents["ISTRAD"] == "1")].copy()
    vulnerable["school_run"] = vulnerable["USTUNDE"].astype(int).isin(SCHOOL_RUN_HOURS) & vulnerable["UWOCHENTAG"].astype(int).isin(WEEKDAYS_MON_FRI)
    points = gpd.GeoDataFrame(vulnerable, geometry=gpd.points_from_xy(vulnerable["XGCSWGS84"], vulnerable["YGCSWGS84"]), crs="EPSG:4326").to_crs(ANALYSIS_CRS)
    joined = gpd.sjoin(points, areas[["plr_id", "geometry"]], predicate="within")
    print(f"accidents Berlin 2018-2024: {len(accidents):,}, with pedestrians/cyclists: {len(vulnerable):,}, located in a planning area: {len(joined):,}")
    return joined.groupby("plr_id").agg(accidents_foot_bike=("school_run", "size"), accidents_foot_bike_school_run=("school_run", "sum"))


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    homes = pd.read_csv(INTERIM / "homes.csv", dtype={"block_id": str, "plr_id": str})
    playgrounds = pd.read_csv(INTERIM / "playgrounds.csv")
    playground_matrix = sp.load_npz(INTERIM / "playground_matrix.npz")
    youth_matrix = sp.load_npz(INTERIM / "youth_matrix.npz")
    youth = read("youth_facilities")
    daycare = read("daycare")
    daycare_matrix = sp.load_npz(INTERIM / "daycare_matrix.npz")
    areas = read("lor_plr")

    # --- home-level supply (independent of administrative borders) ---
    net_area = playgrounds["nettospfl"].values
    for threshold in (NEAR_M, FAR_M):
        tag = f"{threshold:.0f}"
        homes[f"play_m2_per_child_{tag}"] = two_step_supply(playground_matrix, net_area, homes["children"].values, threshold)
        homes[f"play_m2_per_resident_{tag}"] = two_step_supply(playground_matrix, net_area, homes["residents"].values, threshold)
    # Invariant of the two-step method: the play area handed out equals the area of all
    # playgrounds that have at least one child within the threshold.
    has_demand = (within(playground_matrix, FAR_M) @ homes["children"].values) > 0
    handed_out = (homes["play_m2_per_child_1000"] * homes["children"]).sum()
    assert abs(handed_out - net_area[has_demand].sum()) < 1.0, "two-step supply does not conserve play area"
    homes["playgrounds_within_400"] = np.asarray(within(playground_matrix, NEAR_M).sum(axis=0)).ravel()
    youth_places = pd.to_numeric(youth["e_platz"], errors="coerce").fillna(0).values
    homes["youth_places_per_100_1000"] = 100 * two_step_supply(youth_matrix, youth_places, homes["age_10_17"].values, FAR_M)
    daycare_places = pd.to_numeric(daycare["e_platz"], errors="coerce").fillna(0).values
    homes["daycare_places_per_child_1000"] = two_step_supply(daycare_matrix, daycare_places, homes["age_0_5"].values, FAR_M)
    homes.to_csv(INTERIM / "homes_supply.csv", index=False)

    # --- aggregation to planning areas ---
    def aggregate(group: pd.DataFrame) -> pd.Series:
        children, teens, small = group["children"], group["age_10_17"], group["age_0_5"]
        share = lambda mask, weights: float(weights[mask].sum() / weights.sum()) if weights.sum() > 0 else np.nan
        mean = lambda column, weights: float(np.average(group[column], weights=weights)) if weights.sum() > 0 else np.nan
        return pd.Series({
            "residents": group["residents"].sum(),
            "children": children.sum(),
            "age_0_5": small.sum(),
            "age_6_9": group["age_6_9"].sum(),
            "age_10_17": teens.sum(),
            "playground_median_m": weighted_median(group["playground_net_m"], children),
            "playground_share_400_net": share(group["playground_net_m"] <= NEAR_M, children),
            "playground_share_400_air": share(group["playground_air_m"] <= NEAR_M, children),
            "playground_share_400_no_main_road": share(group["playground_no_main_road_m"] <= NEAR_M, children),
            "playground_share_200_small_children": share(group["playground_net_m"] <= 200, small),
            "play_m2_per_child_400": mean("play_m2_per_child_400", children),
            "play_m2_per_child_1000": mean("play_m2_per_child_1000", children),
            "play_m2_per_resident_1000": mean("play_m2_per_resident_1000", group["residents"]),
            "youth_median_m": weighted_median(group["youth_net_m"], teens),
            "youth_share_1000_net": share(group["youth_net_m"] <= FAR_M, teens),
            "youth_places_per_100": mean("youth_places_per_100_1000", teens),
            "daycare_median_m": weighted_median(group["daycare_net_m"], small),
            "daycare_places_per_child": mean("daycare_places_per_child_1000", small),
            "playground_share_400_incl_osm": share(group["playground_incl_osm_net_m"] <= NEAR_M, children),
            "library_median_m": weighted_median(group["library_net_m"], children),
            "primary_school_median_m": weighted_median(group["primary_school_net_m"], group["age_6_9"]),
            "green_share_400_net": share(group["green_net_m"] <= NEAR_M, children),
            "sports_median_m": weighted_median(group["sports_net_m"], children),
        })

    table = homes.groupby("plr_id").apply(aggregate, include_groups=False)
    table = areas.set_index("plr_id")[["plr_name", "bzr_name", "bez", "stadtraum_name"]].join(table)
    table["area_ha"] = areas.set_index("plr_id").area / 1e4
    populated_area = read("blocks_population_2025").assign(area=lambda b: b.area)
    populated_area = populated_area[populated_area["ew2025"] > 0]
    block_plr = homes.drop_duplicates("block_id").set_index("block_id")["plr_id"]
    table["populated_block_area_ha"] = populated_area.groupby(populated_area["schluessel"].map(block_plr))["area"].sum() / 1e4
    table["residents_per_ha_populated"] = table["residents"] / table["populated_block_area_ha"]
    table["child_share"] = table["children"] / table["residents"]

    # Naive within-border figures (what a per-area statistic would show).
    playground_points = gpd.GeoDataFrame(playgrounds, geometry=read("playgrounds").query("widmung.str.strip() != 'entwidmet'").representative_point().values, crs=ANALYSIS_CRS)
    inside = gpd.sjoin(playground_points, areas[["plr_id", "geometry"]], predicate="within")
    table["playgrounds_inside"] = inside.groupby("plr_id").size()
    table["play_area_inside_m2"] = inside.groupby("plr_id")["nettospfl"].sum()
    table[["playgrounds_inside", "play_area_inside_m2"]] = table[["playgrounds_inside", "play_area_inside_m2"]].fillna(0)
    table["play_m2_per_resident_inside"] = table["play_area_inside_m2"] / table["residents"]
    table["play_m2_per_child_inside"] = table["play_area_inside_m2"] / table["children"]
    daycare["places"] = pd.to_numeric(daycare["e_platz"], errors="coerce")
    table["daycare_places_inside"] = gpd.sjoin(daycare, areas[["plr_id", "geometry"]], predicate="within").groupby("plr_id")["places"].sum()

    table["children_2022"] = child_population_2022()
    table["children_change_2022_2025"] = table["children"] / table["children_2022"] - 1

    # Social context (MSS 2025, reference date 31.12.2024)
    status = read("mss2025_index_indicators").set_index("plr_id")
    context = read("mss2025_context_indicators").set_index("plr_id")
    indices = read("mss2025_indices").set_index("plr_id")
    valid = status["kom"] == "gültig"
    table["child_poverty_pct"] = status["s4"].where(valid)
    table["children_single_parent_pct"] = status["s2"].where(valid)
    table["living_space_m2_per_resident"] = context["ki_15"].where(valid)
    table["status_index"] = indices["si_v"].where(valid)

    # Environment (Umweltgerechtigkeitsatlas 2023/2024)
    environment = read("envjustice_multi").set_index("plr_id")
    table["env_burdens"] = environment["kategorie"]
    table[["env_noise", "env_air", "env_heat", "env_green"]] = environment[["laerm", "luft", "bioklima", "gruenvers"]]

    accidents = accidents_by_planning_area(areas)
    table = table.join(accidents)
    table[accidents.columns] = table[accidents.columns].fillna(0)

    table.to_csv(PROCESSED / "plr_indicators.csv")
    print(f"planning areas: {len(table)}, with residents: {int((table['residents'] > 0).sum())}, children: {table['children'].sum():,.0f}")


if __name__ == "__main__":
    main()
