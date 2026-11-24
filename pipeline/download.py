"""Step 1 of the pipeline: download all raw sources into data/raw/ (cached).

Usage:  python -m pipeline.download [--force] [key ...]

Existing files are kept unless --force is given. Downloads are written to a
temporary file first, so a failed download never replaces a good cached file.
"""

import json
import sys
import time
from datetime import date
from pathlib import Path

import requests

from pipeline.sources import ANALYSIS_CRS, FILE_SOURCES, WFS_SOURCES, FileSource, WfsSource

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "manifest.json"
WFS_PAGE_SIZE = 5000
TIMEOUT_SECONDS = 180
RETRIES = 3
USER_AGENT = "kindheit-berlin-pipeline (open data research)"


def get(url: str, **kwargs) -> requests.Response:
    """GET with retries and a clear error on the final failure."""
    last_error: Exception | None = None
    for attempt in range(RETRIES):
        try:
            response = requests.get(url, timeout=TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Download failed after {RETRIES} attempts: {url}\n{last_error}")


def wfs_params(source: WfsSource, **extra) -> dict:
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": f"{source.service}:{source.layer}",
        **extra,
    }
    if source.cql_filter:
        params["cql_filter"] = source.cql_filter
    if source.properties and "resultType" not in extra:
        params["propertyName"] = source.properties
    return params


def download_wfs(source: WfsSource, target: Path) -> int:
    """Fetch all features of a layer as GeoJSON in EPSG:25833, page by page."""
    hits = get(source.url, params=wfs_params(source, resultType="hits")).text
    expected = int(hits.split('numberMatched="')[1].split('"')[0])

    features: list[dict] = []
    while len(features) < expected:
        page = get(
            source.url,
            params=wfs_params(
                source,
                outputFormat="application/json",
                srsName=ANALYSIS_CRS,
                count=WFS_PAGE_SIZE,
                startIndex=len(features),
            ),
        ).json()["features"]
        if not page:
            break
        features.extend(page)

    if len(features) != expected:
        raise RuntimeError(f"{source.key}: got {len(features)} features, server reported {expected}")

    collection = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": f"urn:ogc:def:crs:{ANALYSIS_CRS.replace(':', '::')}"}},
        "features": features,
    }
    write_atomically(target, json.dumps(collection).encode())
    return expected


def download_file(source: FileSource, target: Path) -> int:
    content = get(source.url).content
    # The statistics office answers missing files with its HTML start page (HTTP 200).
    if content.lstrip()[:15].lower().startswith(b"<!doctype html"):
        raise RuntimeError(f"{source.key}: server returned an HTML page instead of the file ({source.url})")
    write_atomically(target, content)
    return len(content)


def write_atomically(target: Path, content: bytes) -> None:
    temporary = target.with_suffix(target.suffix + ".part")
    temporary.write_bytes(content)
    temporary.replace(target)


def main(arguments: list[str]) -> None:
    force = "--force" in arguments
    wanted = {a for a in arguments if not a.startswith("--")}
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else {}
    failures = []

    jobs = [(s, RAW_DIR / s.file_name, download_wfs) for s in WFS_SOURCES]
    jobs += [(s, RAW_DIR / s.file_name, download_file) for s in FILE_SOURCES]

    for source, target, download in jobs:
        if wanted and source.key not in wanted:
            continue
        if target.exists() and not force:
            print(f"cached   {target.name}")
            continue
        try:
            size = download(source, target)
            manifest[source.key] = {
                "url": source.url,
                "layer": getattr(source, "layer", None),
                "license": source.license,
                "provider": source.provider,
                "retrieved": date.today().isoformat(),
                "size": size,  # feature count for WFS layers, bytes for files
            }
            print(f"fetched  {target.name}  ({size})")
        except RuntimeError as error:
            failures.append(source.key)
            print(f"FAILED   {target.name}: {error}", file=sys.stderr)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    if failures:
        sys.exit(f"{len(failures)} download(s) failed: {', '.join(failures)}")


if __name__ == "__main__":
    main(sys.argv[1:])
