"""Download race results, qualifying and sprint results from the Jolpica F1 API.

Each season and endpoint is saved untouched as data/raw/<endpoint>_<season>.json
(a list of the API's pages, kept exactly as received), and logged in data/raw/manifest.csv.

Usage:
    python src/01_download.py                        # all seasons, skip files already saved
    python src/01_download.py --seasons 2026 --force # re-download 2026
"""

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = "https://api.jolpi.ca/ergast/f1"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
MANIFEST = RAW / "manifest.csv"
ENDPOINTS = {"results": "Results", "qualifying": "QualifyingResults", "sprint": "SprintResults"}
PAGE_SIZE = 100  # the API's maximum rows per request


def get_page(url, offset):
    """One page of results as (parsed JSON, original text). Pauses between requests and retries if busy."""
    for attempt in range(5):
        time.sleep(1)
        try:
            response = requests.get(url, params={"limit": PAGE_SIZE, "offset": offset}, timeout=30)
            if response.status_code != 429:  # 429 = too many requests
                response.raise_for_status()
                return response.json(), response.text
        except requests.Timeout:
            pass
        print(f"  API busy or slow, waiting 30s (attempt {attempt + 1} of 5)")
        time.sleep(30)
    raise RuntimeError(f"Gave up on {url} at offset {offset}")


def download(url, row_key):
    """All pages for one season and endpoint. Returns the original page texts and the row count.

    The API pages by driver rows, so one race can be split across two pages. If the data
    changes while downloading (offset or total shifts), stop rather than save a mixed archive.
    """
    texts, rows, total = [], 0, None
    while total is None or rows < total:
        page, text = get_page(url, rows)
        meta = page["MRData"]
        count = sum(len(race[row_key]) for race in meta["RaceTable"]["Races"])
        total = int(meta["total"]) if total is None else total
        if int(meta["offset"]) != rows or int(meta["total"]) != total or count == 0:
            raise RuntimeError(f"Unexpected page at offset {rows} of {total}: {url}. Rerun.")
        texts.append(text)
        rows += count
    if rows != total:
        raise RuntimeError(f"Got {rows} rows, expected {total}: {url}. Rerun.")
    return texts, rows


def save_manifest(manifest):
    with MANIFEST.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["file_name", "url", "retrieved_at_utc", "rows"])
        writer.writeheader()
        writer.writerows(manifest[name] for name in sorted(manifest))


def main(seasons, force):
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = {}
    if MANIFEST.exists():
        with MANIFEST.open(newline="") as file:
            manifest = {row["file_name"]: row for row in csv.DictReader(file)}

    for season in seasons:
        for endpoint, row_key in ENDPOINTS.items():
            if endpoint == "sprint" and season < 2021:
                continue  # sprints started in 2021
            path = RAW / f"{endpoint}_{season}.json"
            if path.exists() and not force:
                print(f"Already saved: {path.name}")
                continue
            url = f"{BASE_URL}/{season}/{endpoint}/"
            print(f"Downloading {url}")
            texts, rows = download(url, row_key)
            # Keep the API's original text. Write to a temporary file first, so an
            # interrupted run never leaves a half-written archive behind.
            temporary = path.with_suffix(".tmp")
            temporary.write_text("[\n" + ",\n".join(texts) + "\n]\n")
            temporary.replace(path)
            manifest[path.name] = {"file_name": path.name, "url": url, "rows": rows,
                                   "retrieved_at_utc": datetime.now(timezone.utc).isoformat()}
            save_manifest(manifest)  # after every file, so the manifest always matches the data
            print(f"Saved {path.name}: {rows} rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download F1 data from the Jolpica API.")
    parser.add_argument("--seasons", nargs="+", type=int, default=list(range(2006, 2027)))
    parser.add_argument("--force", action="store_true", help="re-download files already saved")
    args = parser.parse_args()
    main(args.seasons, args.force)
