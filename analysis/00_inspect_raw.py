"""Print structure and basic quality facts of every raw layer (exploration helper)."""
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
pd.set_option("display.width", 250, "display.max_columns", 60, "display.max_colwidth", 38)

for path in sorted(RAW.glob("*.geojson")):
    if len(sys.argv) > 1 and path.stem not in sys.argv[1:]:
        continue
    layer = gpd.read_file(path)
    geometry = layer.geometry
    print(f"\n=== {path.stem}: {len(layer)} rows, crs={layer.crs.to_epsg()}, types={geometry.geom_type.value_counts().to_dict()}")
    print(f"    empty/missing geometry: {int(geometry.isna().sum() + geometry.is_empty.sum())}, invalid: {int((~geometry.is_valid).sum())}, duplicated geometry: {int(geometry.to_wkb().duplicated().sum())}")
    for column in layer.columns.drop("geometry"):
        values = layer[column]
        sample = values.dropna().unique()[:4].tolist()
        print(f"    {column:28s} {str(values.dtype):10s} null={int(values.isna().sum()):5d} unique={values.nunique():6d}  {str(sample)[:110]}")
