"""Generate the static data files the web application loads (public/data/).

Everything is written to a temporary directory, validated, and only then moved
into place, so a failed run never replaces the last valid data set.

Run:  python -m pipeline.export_frontend
"""

import json
import math
import shutil
from dataclasses import asdict
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from pipeline.sources import ALL_SOURCES

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
TARGET = ROOT / "public" / "data"

REACH_THRESHOLDS_M = [200, 300, 400, 500, 800, 1000]
CURVE_DISTANCES_M = list(range(0, 1001, 25))
MIN_CHILDREN_FOR_SHARES = 100  # below this, child-weighted values are not published
SIMPLIFY_TOLERANCE_M = 12.0
POPULATION_REFERENCE_DATE = "2025-12-31"
HOUSING_TYPES_SHOWN = 9
GARDEN_TYPE_MARKERS = ("mit Gärten", "parkartigen Gärten", "Einzelhausgebiet")


def clean(value, digits: int):
    """JSON-safe number: None for missing values, rounded otherwise."""
    if value is None or (isinstance(value, float) and not math.isfinite(value)) or pd.isna(value):
        return None
    return round(float(value), digits) if digits > 0 else int(round(float(value)))


def weighted_share(values: pd.Series, weights: pd.Series, threshold: float) -> float | None:
    total = weights.sum()
    return float(weights[values <= threshold].sum() / total) if total > 0 else None


def weighted_median(values: pd.Series, weights: pd.Series) -> float | None:
    if weights.sum() <= 0:
        return None
    order = np.argsort(values.values)
    cumulative = np.cumsum(weights.values[order])
    return float(values.values[order][np.searchsorted(cumulative, cumulative[-1] / 2)])


def reach_by_threshold(homes: pd.DataFrame) -> dict:
    children = homes["children"]
    columns = {"walking": "playground_net_m", "straight": "playground_air_m", "withOsm": "playground_incl_osm_net_m"}
    return {name: [clean(weighted_share(homes[column], children, t), 3) for t in REACH_THRESHOLDS_M] for name, column in columns.items()}


# (output field, table column, digits, needs enough children to be meaningful)
AREA_FIELDS = [
    ("residents", "residents", 0, False),
    ("children", "children", 0, False),
    ("age0to5", "age_0_5", 0, False),
    ("age6to9", "age_6_9", 0, False),
    ("age10to17", "age_10_17", 0, False),
    ("childShare", "child_share", 3, False),
    ("childrenChange", "children_change_2022_2025", 3, True),
    ("densityPerHa", "residents_per_ha_populated", 0, False),
    ("playgroundsInside", "playgrounds_inside", 0, False),
    ("playM2PerResidentInside", "play_m2_per_resident_inside", 2, False),
    ("playgroundMedianM", "playground_median_m", 0, True),
    ("playM2PerChild", "play_m2_per_child_1000", 2, True),
    ("shareNoMainRoad400", "playground_share_400_no_main_road", 3, True),
    ("smallChildren200", "playground_share_200_small_children", 3, True),
    ("youthShare1000", "youth_share_1000_net", 3, True),
    ("youthMedianM", "youth_median_m", 0, True),
    ("youthPlacesPer100", "youth_places_per_100", 1, True),
    ("daycareMedianM", "daycare_median_m", 0, True),
    ("daycarePlacesPerChild", "daycare_places_per_child", 2, True),
    ("primarySchoolMedianM", "primary_school_median_m", 0, True),
    ("greenShare400", "green_share_400_net", 3, True),
    ("sportsMedianM", "sports_median_m", 0, True),
    ("libraryMedianM", "library_median_m", 0, True),
    ("childPoverty", "child_poverty_pct", 1, False),
    ("singleParent", "children_single_parent_pct", 1, False),
    ("livingSpace", "living_space_m2_per_resident", 1, False),
    ("accidentsSchoolRun", "accidents_foot_bike_school_run", 0, False),
]
TEXT_FIELDS = [("statusIndex", "status_index"), ("envBurdens", "env_burdens"), ("envNoise", "env_noise"), ("envAir", "env_air"), ("envHeat", "env_heat"), ("envGreen", "env_green")]


def area_records(table: pd.DataFrame, homes: pd.DataFrame) -> list[dict]:
    records = []
    homes_by_area = dict(tuple(homes.groupby("plr_id")))
    for plr_id, row in table.iterrows():
        enough = row["children"] >= MIN_CHILDREN_FOR_SHARES
        record = {"id": plr_id, "name": row["plr_name"], "region": row["bzr_name"], "district": row["bez"].split(" - ", 1)[1], "zone": row["stadtraum_name"], "enoughChildren": bool(enough)}
        for field, column, digits, needs_children in AREA_FIELDS:
            record[field] = clean(row[column], digits) if (enough or not needs_children) else None
        for field, column in TEXT_FIELDS:
            record[field] = None if pd.isna(row[column]) else row[column]
        area_homes = homes_by_area.get(plr_id)
        record["reach"] = reach_by_threshold(area_homes) if enough and area_homes is not None else None
        records.append(record)
    return records


def city_record(table: pd.DataFrame, homes: pd.DataFrame) -> dict:
    """Berlin as a whole, computed like a single planning area (reference values)."""
    children, small, school_age, teens = homes["children"], homes["age_0_5"], homes["age_6_9"], homes["age_10_17"]
    valid = table[table["children_single_parent_pct"].notna()]
    return {
        "residents": clean(homes["residents"].sum(), 0),
        "children": clean(children.sum(), 0),
        "age0to5": clean(small.sum(), 0),
        "age6to9": clean(school_age.sum(), 0),
        "age10to17": clean(teens.sum(), 0),
        "childShare": clean(children.sum() / homes["residents"].sum(), 3),
        "childrenChange": clean(table["children"].sum() / table["children_2022"].sum() - 1, 3),
        "densityPerHa": clean(table["residents"].sum() / table["populated_block_area_ha"].sum(), 0),
        "playM2PerResidentInside": clean(table["play_area_inside_m2"].sum() / table["residents"].sum(), 2),
        "playgroundMedianM": clean(weighted_median(homes["playground_net_m"], children), 0),
        "playM2PerChild": clean(np.average(homes["play_m2_per_child_1000"], weights=children), 2),
        "shareNoMainRoad400": clean(weighted_share(homes["playground_no_main_road_m"], children, 400), 3),
        "smallChildren200": clean(weighted_share(homes["playground_net_m"], small, 200), 3),
        "youthShare1000": clean(weighted_share(homes["youth_net_m"], teens, 1000), 3),
        "youthMedianM": clean(weighted_median(homes["youth_net_m"], teens), 0),
        "youthPlacesPer100": clean(np.average(homes["youth_places_per_100_1000"], weights=teens), 1),
        "daycareMedianM": clean(weighted_median(homes["daycare_net_m"], small), 0),
        "daycarePlacesPerChild": clean(np.average(homes["daycare_places_per_child_1000"], weights=small), 2),
        "primarySchoolMedianM": clean(weighted_median(homes["primary_school_net_m"], school_age), 0),
        "greenShare400": clean(weighted_share(homes["green_net_m"], children, 400), 3),
        "sportsMedianM": clean(weighted_median(homes["sports_net_m"], children), 0),
        "libraryMedianM": clean(weighted_median(homes["library_net_m"], children), 0),
        # Child-weighted means of the planning-area values (the official city figures differ slightly).
        "childPoverty": clean(np.average(valid["child_poverty_pct"], weights=valid["children"]), 1),
        "singleParent": clean(np.average(valid["children_single_parent_pct"], weights=valid["children"]), 1),
        "livingSpace": clean(np.average(valid["living_space_m2_per_resident"], weights=valid["residents"]), 1),
        "reach": reach_by_threshold(homes),
    }


def distance_curves(homes: pd.DataFrame) -> dict:
    children = homes["children"]
    columns = {
        "straight": "playground_air_m",
        "walking": "playground_net_m",
        "securedCrossings": "playground_secured_crossings_m",
        "noMainRoad": "playground_no_main_road_m",
        "withOsm": "playground_incl_osm_net_m",
    }
    return {"distancesM": CURVE_DISTANCES_M, "series": {name: [clean(weighted_share(homes[column], children, d), 4) for d in CURVE_DISTANCES_M] for name, column in columns.items()}}


def housing_types(homes: pd.DataFrame) -> list[dict]:
    rows = []
    for name, group in homes.groupby("typklar"):
        children = group["children"]
        rows.append({
            "name": name.split(" (")[0].split(",")[0],
            "fullName": name,
            "children": clean(children.sum(), 0),
            "hasGardens": any(marker in name for marker in GARDEN_TYPE_MARKERS),
            "shareOfficial": clean(weighted_share(group["playground_net_m"], children, 400), 3),
            "shareWithOsm": clean(weighted_share(group["playground_incl_osm_net_m"], children, 400), 3),
        })
    return sorted(rows, key=lambda row: -row["children"])[:HOUSING_TYPES_SHOWN]


def scenario_steps(file_name: str) -> list[dict]:
    table = pd.read_csv(PROCESSED / file_name)
    steps = []
    for _, row in table.iterrows():
        step = {"step": int(row["step"]), "id": str(row["id"]), "name": row["name"].strip(), "district": row["district"], "lon": float(row["lon"]), "lat": float(row["lat"]),
                "childrenReached": int(row["children_newly_reached"]), "cumulative": int(row["cumulative"])}
        if "area_m2" in row:
            step["areaM2"] = clean(row["area_m2"], 0)
        steps.append(step)
    return steps


def geometries() -> tuple[dict, dict]:
    """Planning areas (shared borders preserved while simplifying) and district outlines, in WGS84."""
    areas = gpd.read_file(RAW / "lor_plr.geojson")[["plr_id", "plr_name", "bez", "geometry"]]
    areas["geometry"] = shapely.coverage_simplify(areas.geometry.values, SIMPLIFY_TOLERANCE_M)
    districts = areas.assign(name=areas["bez"].str.split(" - ").str[1]).dissolve("name").reset_index()[["name", "geometry"]]
    label_points = gpd.GeoSeries(districts.representative_point(), crs=areas.crs).to_crs("EPSG:4326")
    districts["labelLon"], districts["labelLat"] = label_points.x.round(5), label_points.y.round(5)
    areas = areas.rename(columns={"plr_id": "id", "plr_name": "name"})[["id", "name", "geometry"]]
    to_geojson = lambda frame: json.loads(shapely.set_precision(frame.to_crs("EPSG:4326").geometry, 0.00001).to_frame("geometry").join(frame.drop(columns="geometry")).to_json())
    return to_geojson(areas), to_geojson(districts)


def source_records() -> list[dict]:
    manifest = json.loads((RAW / "manifest.json").read_text())
    records = []
    for source in ALL_SOURCES:
        record = {k: v for k, v in asdict(source).items() if k in {"key", "title", "provider", "license", "reference_date", "used_for", "dataset_page", "attribution"}}
        record["retrieved"] = manifest.get(source.key, {}).get("retrieved")
        records.append(record)
    # The seven yearly Unfallatlas files are one source for readers.
    merged, seen_unfallatlas = [], False
    for record in records:
        if record["key"].startswith("unfallatlas_"):
            if seen_unfallatlas:
                continue
            seen_unfallatlas = True
            record = {**record, "key": "unfallatlas", "title": "Unfallatlas – Unfallorte 2018 bis 2024", "reference_date": "2018–2024"}
        merged.append(record)
    return merged


def write_sources_document(records: list[dict]) -> None:
    """docs/DATA_SOURCES.md is generated from the registry, so it cannot drift from the code."""
    lines = [
        "# Datenquellen",
        "",
        "Diese Datei wird von `pipeline/export_frontend.py` aus `pipeline/sources.py` erzeugt. Bitte nicht von Hand ändern.",
        "",
        "| Datensatz | Anbieter | Lizenz | Datenstand | Abruf | Verwendet für | Namensnennung |",
        "|---|---|---|---|---|---|---|",
    ]
    for record in records:
        lines.append(
            f"| [{record['title']}]({record['dataset_page']}) | {record['provider']} | {record['license']} | {record['reference_date']} "
            f"| {record['retrieved'] or 'unbekannt'} | {record['used_for']} | {record['attribution'] or 'nicht vorgeschrieben'} |"
        )
    lines += [
        "",
        "## Verwendete Attribute",
        "",
        "| Datensatz | Attribute |",
        "|---|---|",
        "| LOR-Planungsräume | `plr_id`, `plr_name`, `bzr_name`, `bez`, `stadtraum_name`, Geometrie |",
        "| Einwohnerdichte 2025 / 2022 | `schluessel`, `ew2025`, `alter_u6`, `alter_6_u10`, `alter_10_u18`, `typklar`, Geometrie |",
        "| ALKIS Gebäude | `gfk` (Gebäudefunktion, Filter `< 1300`), `aog` (oberirdische Geschosse), `shape_area`, Lage aus der Bounding Box |",
        "| Spielplätze | `pitid`, `namenr`, `nettospfl`, `widmung`, `baujahr`, `sanierjahr`, Geometrie |",
        "| Grünanlagen | `pitid`, `namenr`, `bezirkname`, `katasterfl`, Geometrie |",
        "| Jugendfreizeiteinrichtungen, Kindertagesstätten | `e_platz` (Plätze), Geometrie |",
        "| Schulen | `bsn`, `schulname`, `schulart`, `traeger`, `bezirk`, Geometrie |",
        "| Sportanlagen | Geometrie |",
        "| MSS 2025 | `s2` (Kinder in alleinerziehenden Haushalten), `s4` (Kinderarmut), `ki_15` (Wohnfläche), `si_v` (Status-Index), `kom` (Gültigkeit) |",
        "| Umweltgerechtigkeit | `kategorie`, `laerm`, `luft`, `bioklima`, `gruenvers` |",
        "| Unfallatlas | `ULAND`, `USTUNDE`, `UWOCHENTAG`, `ISTFUSS`, `ISTRAD`, Koordinaten |",
        "| Polizei Berlin 2025 | `alterjahre`, `paginiernr` |",
        "| OpenStreetMap | `highway`, `foot`, `access`, `area`, `footway`, `crossing`, `crossing:signals`, `crossing:markings`, `leisure=playground`, `amenity=library`, `wheelchair`, `railway`, `waterway`, `tunnel` |",
        "",
        "## Geprüft, aber nicht verwendet",
        "",
        "- **Einwohnerregisterstatistik je Planungsraum** (Statistischer Bericht A I 16): nur zur Plausibilitätsprüfung der Blocksummen; die verlinkten CSV-Dateien waren nicht abrufbar.",
        "- **Verkehrsmengen DTVw 2023, Tempolimits:** für eine spätere Verfeinerung der Hauptstraßen-Definition vorgesehen.",
        "- **Einschulbereiche:** erst für eine Schulweg-Auswertung nach Zuständigkeit nötig.",
        "- **Klimaanalyse 2022, Versiegelung, Baumbestand, Zensus-Gitter, Öffentliche Toiletten, Landesgrundvermögen:** kein zusätzlicher Erkenntnisgewinn für die gewählten Fragen.",
        "",
    ]
    (ROOT / "docs" / "DATA_SOURCES.md").write_text("\n".join(lines))


def write_json(directory: Path, name: str, content) -> None:
    # allow_nan=False makes a stray NaN fail loudly instead of producing invalid JSON.
    (directory / name).write_text(json.dumps(content, ensure_ascii=False, allow_nan=False, separators=(",", ":")))


def validate(directory: Path) -> None:
    indicators = json.loads((directory / "indicators.json").read_text())
    areas = json.loads((directory / "planning-areas.geojson").read_text())
    ids = {record["id"] for record in indicators["areas"]}
    assert len(indicators["areas"]) == 542 and len(ids) == 542, "expected 542 planning areas"
    assert {feature["properties"]["id"] for feature in areas["features"]} == ids, "geometry and indicator ids differ"
    assert sum(record["children"] for record in indicators["areas"]) == indicators["city"]["children"], "children do not add up to the city total"
    for record in indicators["areas"]:
        if record["reach"]:
            for series in record["reach"].values():
                assert all(0 <= value <= 1 for value in series), f"share outside 0..1 in {record['id']}"
                assert series == sorted(series), f"reach must not decrease with distance in {record['id']}"
            assert all(w <= s + 1e-9 for w, s in zip(record["reach"]["walking"], record["reach"]["straight"])), f"walking beats straight line in {record['id']}"
    scenarios = json.loads((directory / "scenarios.json").read_text())
    for scenario in scenarios["scenarios"].values():
        for steps in scenario["variants"].values():
            assert [step["step"] for step in steps] == list(range(1, len(steps) + 1))
            assert steps[-1]["cumulative"] == sum(step["childrenReached"] for step in steps)


def main() -> None:
    homes = pd.read_csv(INTERIM / "homes_supply.csv", dtype={"block_id": str, "plr_id": str})
    table = pd.read_csv(PROCESSED / "plr_indicators.csv", dtype={"plr_id": str}).set_index("plr_id")
    findings = json.loads((PROCESSED / "findings.json").read_text())
    # Two planning areas have no residents at all: real zeros, not missing values.
    count_columns = ["residents", "children", "age_0_5", "age_6_9", "age_10_17"]
    table[count_columns] = table[count_columns].fillna(0)

    staging = TARGET.with_name("data.staging")
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)

    planning_areas, districts = geometries()
    write_json(staging, "planning-areas.geojson", planning_areas)
    write_json(staging, "districts.geojson", districts)
    write_json(staging, "indicators.json", {
        "generated": date.today().isoformat(),
        "populationReferenceDate": POPULATION_REFERENCE_DATE,
        "reachThresholdsM": REACH_THRESHOLDS_M,
        "minChildrenForShares": MIN_CHILDREN_FOR_SHARES,
        "city": city_record(table, homes),
        "areas": area_records(table, homes),
    })
    write_json(staging, "story.json", {"distanceCurves": distance_curves(homes), "housingTypes": housing_types(homes), "findings": findings})
    write_json(staging, "scenarios.json", {
        "scenarios": {
            "greenSpace": {"summary": {"official": findings["new_playground_scenario"], "withOsm": findings["new_playground_scenario_incl_osm"]},
                           "variants": {"official": scenario_steps("scenario_new_playgrounds.csv"), "withOsm": scenario_steps("scenario_new_playgrounds_incl_osm.csv")}},
            "schoolyard": {"summary": {"official": findings["schoolyard_scenario"], "withOsm": findings["schoolyard_scenario_incl_osm"]},
                           "variants": {"official": scenario_steps("scenario_schoolyards.csv"), "withOsm": scenario_steps("scenario_schoolyards_incl_osm.csv")}},
        }
    })
    sources = source_records()
    write_json(staging, "sources.json", sources)
    write_sources_document(sources)
    table.round(4).to_csv(staging / "planning-area-indicators.csv")

    validate(staging)
    shutil.rmtree(TARGET, ignore_errors=True)
    staging.rename(TARGET)
    sizes = {path.name: f"{path.stat().st_size / 1024:.0f} kB" for path in sorted(TARGET.iterdir())}
    print(f"exported to {TARGET}: {sizes}")


if __name__ == "__main__":
    main()
