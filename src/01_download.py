"""Download Jolpica race, qualifying and sprint results, preserving each raw page."""

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests

BASE = "https://api.jolpi.ca/ergast/f1"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
ROW_KEYS = {"results": "Results", "qualifying": "QualifyingResults", "sprint": "SprintResults"}
FIELDS = ["file_name", "url", "retrieved_at_utc", "rows"]
LIMIT = 100


def fetch(session, url, offset):
    for attempt in range(5):
        time.sleep(1)
        delay = 10 * 2**attempt
        try:
            response = session.get(url, params={"limit": LIMIT, "offset": offset}, timeout=30)
            if response.status_code != 429:
                response.raise_for_status()
                return response.content
            reason = "HTTP 429"
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                if retry_after.isdigit():
                    delay = max(delay, int(retry_after))
                else:
                    until = parsedate_to_datetime(retry_after)
                    delay = max(delay, (until - datetime.now(timezone.utc)).total_seconds())
        except requests.Timeout:
            reason = "timeout"
        if attempt == 4:
            raise RuntimeError(f"{reason} after five attempts at {url}, offset {offset}")
        print(f"  {reason} at offset {offset}. Retrying in {delay:.0f}s.", flush=True)
        time.sleep(delay)


def page_counts(page, key, offset, expected):
    # Pagination counts driver rows inside each race.
    meta = page["MRData"]
    total = int(meta["total"])
    count = sum(len(race[key]) for race in meta["RaceTable"]["Races"])
    if int(meta["offset"]) != offset or (expected is not None and total != expected):
        raise ValueError(f"Pagination changed at offset {offset}. Rerun this download.")
    if count > LIMIT or offset + count > total or (count == 0 and offset < total):
        raise ValueError(f"Unexpected page size {count} at offset {offset} of {total}")
    return count, total


def download(session, url, key, path):
    offset, total = 0, None
    pages = []
    while total is None or offset < total:
        body = fetch(session, url, offset)
        count, total = page_counts(json.loads(body), key, offset, total)
        pages.append(body)
        offset += count

    # A JSON array keeps the original bytes of each page, including its metadata.
    with NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        tmp.write(b"[\n" + b",\n".join(pages) + b"\n]\n")
    Path(tmp.name).replace(path)
    return total


def cached_count(path, key):
    pages = json.loads(path.read_bytes())
    if not isinstance(pages, list) or not pages:
        raise ValueError(f"Invalid page archive: {path.name}. Use --force to refresh.")
    offset, total = 0, None
    for page in pages:
        count, total = page_counts(page, key, offset, total)
        offset += count
    if offset != total:
        raise ValueError(f"Incomplete archive: {path.name}. Use --force to refresh.")
    return offset


def run(seasons, force):
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = RAW / "manifest.csv"
    records = {}
    if manifest.exists():
        with manifest.open(newline="") as source:
            records = {row["file_name"]: row for row in csv.DictReader(source)}

    with requests.Session() as session:
        for season in sorted(set(seasons)):
            for endpoint, key in ROW_KEYS.items():
                if endpoint == "sprint" and season < 2021:
                    continue
                path = RAW / f"{endpoint}_{season}.json"
                url = f"{BASE}/{season}/{endpoint}/"
                if path.exists() and not force:
                    rows = cached_count(path, key)
                    action = "Cached"
                else:
                    print(f"Fetching {url}", flush=True)
                    rows = download(session, url, key, path)
                    action = "Saved"

                # File completion time also recovers a missing manifest entry.
                stamp = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
                records[path.name] = dict(zip(FIELDS, (path.name, url, stamp, rows)))
                with NamedTemporaryFile(mode="w", newline="", dir=RAW, delete=False) as tmp:
                    writer = csv.DictWriter(tmp, fieldnames=FIELDS)
                    writer.writeheader()
                    writer.writerows(records[name] for name in sorted(records))
                Path(tmp.name).replace(manifest)
                print(f"{action} {path.name}: {rows} rows", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", nargs="+", type=int, default=range(2006, 2027),
                        help="Space-separated years (default: 2006 through 2026)")
    parser.add_argument("--force", action="store_true", help="Refresh existing archives")
    args = parser.parse_args()
    try:
        run(args.seasons, args.force)
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        sys.exit(f"Download failed: {error}")
