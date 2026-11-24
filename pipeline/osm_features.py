"""Extract additional OpenStreetMap features used as complements to official data.

Writes to data/interim/:
  osm_playgrounds.geojson  leisure=playground (points; ways reduced to their centroid)
  osm_libraries.geojson    amenity=library
  osm_barriers.geojson     linear barriers: railways, motorways, waterways

Run:  python -m pipeline.osm_features
"""

import geopandas as gpd
import osmium
import shapely

from pipeline.sources import ANALYSIS_CRS
from pipeline.walk_network import PBF_PATH, ROOT

INTERIM = ROOT / "data" / "interim"
RAILWAY_BARRIERS = {"rail", "light_rail"}  # tram tracks and underground lines do not block pedestrians
MOTORWAY_BARRIERS = {"motorway", "motorway_link", "trunk", "trunk_link"}
WATERWAY_BARRIERS = {"river", "canal"}
POINT_TAGS = ["name", "access", "wheelchair", "operator", "min_age", "max_age"]


def barrier_kind(tags) -> str | None:
    # Bridges and tunnels are where pedestrians pass, the line itself still separates.
    if tags.get("railway") in RAILWAY_BARRIERS and tags.get("tunnel") != "yes":
        return "railway"
    if tags.get("highway") in MOTORWAY_BARRIERS and tags.get("tunnel") != "yes":
        return "motorway"
    if tags.get("waterway") in WATERWAY_BARRIERS and tags.get("tunnel") not in {"yes", "culvert"}:
        return "water"
    return None


def point_kind(tags) -> str | None:
    if tags.get("leisure") == "playground":
        return "playground"
    if tags.get("amenity") == "library":
        return "library"
    return None


def main() -> None:
    points, barriers = [], []
    processor = (
        osmium.FileProcessor(str(PBF_PATH), osmium.osm.NODE | osmium.osm.WAY)
        .with_locations()
        .with_filter(osmium.filter.KeyFilter("leisure", "amenity", "railway", "highway", "waterway"))
    )
    for item in processor:
        kind = point_kind(item.tags)
        if item.is_node():
            if kind:
                points.append({"kind": kind, **{t: item.tags.get(t) for t in POINT_TAGS}, "geometry": shapely.Point(item.location.lon, item.location.lat)})
            continue
        coordinates = [(n.location.lon, n.location.lat) for n in item.nodes if n.location.valid()]
        if len(coordinates) < 2:
            continue
        if kind:
            points.append({"kind": kind, **{t: item.tags.get(t) for t in POINT_TAGS}, "geometry": shapely.LineString(coordinates).centroid})
        barrier = barrier_kind(item.tags)
        if barrier:
            barriers.append({"kind": barrier, "geometry": shapely.LineString(coordinates)})

    INTERIM.mkdir(parents=True, exist_ok=True)
    point_frame = gpd.GeoDataFrame(points, crs="EPSG:4326").to_crs(ANALYSIS_CRS)
    for kind, name in [("playground", "osm_playgrounds"), ("library", "osm_libraries")]:
        subset = point_frame[point_frame["kind"] == kind]
        subset.to_file(INTERIM / f"{name}.geojson", driver="GeoJSON")
        print(f"{name}: {len(subset):,}")
    barrier_frame = gpd.GeoDataFrame(barriers, crs="EPSG:4326").to_crs(ANALYSIS_CRS)
    barrier_frame.to_file(INTERIM / "osm_barriers.geojson", driver="GeoJSON")
    print(barrier_frame.assign(km=barrier_frame.length / 1000).groupby("kind")["km"].sum().round(0).to_dict())


if __name__ == "__main__":
    main()
