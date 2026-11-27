"""Turn the raw Jolpica pages into clean race, results, qualifying and sprint tables.

Reads data/raw/, writes four CSVs to data/processed/ and prints a per-season check.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
SEASONS = range(2006, 2027)

COLUMNS = {
    "races": ["season", "round", "race_name", "date", "circuit_id", "circuit_name", "track_layout_id"],
    "results": ["season", "round", "driver", "constructor", "grid", "finishing_position",
                "position_text", "status", "points", "fastest_lap_seconds"],
    "qualifying": ["season", "round", "driver", "constructor", "q1_seconds", "q2_seconds", "q3_seconds"],
}
COLUMNS["sprint"] = COLUMNS["results"]
QUALI_SEGMENTS = {"Q1": "q1_seconds", "Q2": "q2_seconds", "Q3": "q3_seconds"}


def to_seconds(text, where):
    """'1:26.870' or '55.404' -> '86.870' (3 decimals, as in the source). Empty -> None.

    `where` names the race, driver and session, so a bad value can be found.
    """
    if not text:
        return None
    minutes, _, secs = text.rpartition(":")
    try:
        seconds = float(secs)
        total = int(minutes or 0) * 60 + seconds
    except ValueError:
        raise ValueError(f"Unreadable lap time {text!r} ({where})") from None
    if not 0 < total < 1000 or (minutes and not 0 <= seconds < 60):  # also rejects nan, inf, 1:99
        raise ValueError(f"Impossible lap time {text!r} ({where})")
    return f"{total:.3f}"


def saved_races(endpoint, season):
    """Every race in a season's saved pages. A race split across two pages appears twice."""
    for page in json.loads((RAW / f"{endpoint}_{season}.json").read_bytes()):
        yield from page["MRData"]["RaceTable"]["Races"]


def layout_id(layouts, circuit, season, round_number):
    """Look up the layout version in track_layouts.csv. Circuits with no listed change are _v1.

    A row applies from first_season to last_season (blank = still in use), and to every
    round unless the row names one. If several rows apply, a round-specific row wins,
    then the most recent change.
    """
    matches = [row for row in layouts
               if row["circuit_id"] == circuit
               and int(row["first_season"]) <= season <= int(row["last_season"] or 9999)
               and row["round"] in ("", str(round_number))]
    if not matches:
        return f"{circuit}_v1"
    best = max(matches, key=lambda row: (row["round"] != "", int(row["first_season"])))
    return best["layout_id"]


def driver_row(race, entry, endpoint):
    """One driver's row in the results, sprint or qualifying table."""
    row = {"season": int(race["season"]), "round": int(race["round"]),
           "driver": entry["Driver"]["driverId"], "constructor": entry["Constructor"]["constructorId"]}
    where = f"{endpoint} {row['season']} round {row['round']} {row['driver']}"
    if endpoint == "qualifying":
        for segment, column in QUALI_SEGMENTS.items():
            row[column] = to_seconds(entry.get(segment), f"{where} {segment}")
    else:
        row.update(grid=entry["grid"], finishing_position=entry["position"],
                   position_text=entry["positionText"], status=entry["status"], points=entry["points"],
                   fastest_lap_seconds=to_seconds(entry.get("FastestLap", {}).get("Time", {}).get("time"),
                                                  f"{where} fastest lap"))
    return row


def apply_manual_qualifying(qualifying):
    """Fill gaps in the API data from data/raw/manual_qualifying_*.csv.

    Only empty times are filled; a time from the API is never overwritten.
    Each manual file lists its source URL on every row.
    """
    filled = 0
    for path in sorted(RAW.glob("manual_qualifying_*.csv")):
        with path.open(encoding="utf-8", newline="") as file:
            for manual in csv.DictReader(file):
                key = (int(manual["season"]), int(manual["round"]), manual["driver"])
                row = qualifying[key]  # KeyError here means a typo in the manual file
                if row["constructor"] != manual["constructor"]:
                    raise ValueError(f"Constructor mismatch in {path.name}: {key}")
                for segment, column in QUALI_SEGMENTS.items():
                    if row[column] is None and manual[segment]:
                        row[column] = to_seconds(manual[segment], f"{path.name} {key} {segment}")
                        filled += 1
    return filled


def main():
    with (PROCESSED / "track_layouts.csv").open(encoding="utf-8", newline="") as file:
        layouts = list(csv.DictReader(file))
    tables = {name: {} for name in COLUMNS}

    for season in SEASONS:
        for endpoint, entries in [("results", "Results"), ("qualifying", "QualifyingResults"),
                                  ("sprint", "SprintResults")]:
            if endpoint == "sprint" and season < 2021:
                continue  # sprints started in 2021
            for race in saved_races(endpoint, season):
                race_key = (int(race["season"]), int(race["round"]))
                if endpoint == "results":
                    circuit = race["Circuit"]["circuitId"]
                    tables["races"][race_key] = {
                        "season": race_key[0], "round": race_key[1], "race_name": race["raceName"],
                        "date": race["date"], "circuit_id": circuit,
                        "circuit_name": race["Circuit"]["circuitName"],
                        "track_layout_id": layout_id(layouts, circuit, *race_key)}
                for entry in race[entries]:
                    row = driver_row(race, entry, endpoint)
                    key = (*race_key, row["driver"])
                    if key in tables[endpoint]:
                        raise ValueError(f"Duplicate driver row in {endpoint}: {key}")
                    tables[endpoint][key] = row

    filled = apply_manual_qualifying(tables["qualifying"])

    for name, rows in tables.items():
        with (PROCESSED / f"{name}.csv").open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=COLUMNS[name])
            writer.writeheader()
            writer.writerows(rows[key] for key in sorted(rows))
        print(f"{name}.csv: {len(rows):,} rows")
    print(f"Qualifying times filled from manual files: {filled}")

    # Per-season check: races in each table, every race has qualifying, one classified winner each.
    print("\nSeason  Races  Qualifying  Sprints")
    for season in SEASONS:
        counts = [len({key[:2] for key in tables[name] if key[0] == season})
                  for name in ("results", "qualifying", "sprint")]
        print(f"{season}  {counts[0]:>5}  {counts[1]:>10}  {counts[2]:>7}")
    qualified = {key[:2] for key in tables["qualifying"]}
    no_qualifying = sorted(key for key in tables["races"] if key not in qualified)
    print(f"Races without qualifying data: {no_qualifying or 'none'}")
    winners = {}
    for row in tables["results"].values():
        if row["position_text"] == "1":
            key = (row["season"], row["round"])
            winners[key] = winners.get(key, 0) + 1
    problems = sorted(key for key in tables["races"] if winners.get(key) != 1)
    print(f"Races without exactly one winner: {problems or 'none'}")

if __name__ == "__main__":
    main()
