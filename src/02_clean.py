"""Flatten the project's Jolpica page archives into race and driver tables."""

import csv
import json
import re
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

DATA = Path(__file__).resolve().parents[1] / "data"
RACE = ["season", "round", "race_name", "date", "circuit_id", "circuit_name", "track_layout_id"]
DRIVER = ["season", "round", "driver", "constructor"]
RESULT = DRIVER + ["grid", "finishing_position", "status", "points", "fastest_lap_seconds"]
QUALIFYING = DRIVER + ["q1_seconds", "q2_seconds", "q3_seconds"]
SCHEMAS = {"races": RACE, "results": RESULT, "qualifying": QUALIFYING, "sprint": RESULT}


def seconds(raw, location, failures):
    if raw is None or raw == "":
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?", str(raw).strip()):
        return Decimal(str(raw).strip())
    match = re.fullmatch(r"(\d+):([0-5]\d(?:\.\d+)?)", str(raw).strip())
    if match:
        minutes, remainder = match.groups()
        return int(minutes) * 60 + Decimal(remainder)
    failures.append(f"{location}: {raw!r}")
    return None


def read_layout_changes(path):
    changes = {}
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            circuit = row["circuit_id"]
            year = int(row["change_season"])
            years = changes.setdefault(circuit, set())
            if year in years:
                raise ValueError(f"Duplicate layout change: {circuit} {year}")
            years.add(year)
    return changes


def layout_id(circuit, season, round_number, changes):
    # Sakhir reused the standard GP layout and tried two temporary alternatives.
    years = changes.get(circuit, set())
    if circuit == "bahrain":
        if season == 2010 and season in years:
            return "bahrain_v2"
        if (season, round_number) == (2020, 16) and season in years:
            return "bahrain_v3"
        years = years - {2010, 2012, 2020}
    version = 1 + sum(year <= season for year in years)
    return f"{circuit}_v{version}"


def fill_miami_times(path, qualifying, failures):
    filled = 0
    seen = set()
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            key = (int(row["season"]), int(row["round"]), row["driver"])
            if key[:2] != (2025, 6) or key not in qualifying or key in seen:
                raise ValueError(f"Unexpected manual qualifying key: {key}")
            seen.add(key)
            result = list(qualifying[key])
            if result[3] != row["constructor"]:
                raise ValueError(f"Constructor mismatch for {key}")
            for index, segment in enumerate(("Q1", "Q2", "Q3"), start=4):
                if result[index] is None and row[segment].strip():
                    result[index] = seconds(row[segment], f"{path.name} {key} {segment}", failures)
                    filled += int(result[index] is not None)
            qualifying[key] = tuple(result)
    return filled


def main():
    raw_dir = DATA / "raw"
    out = DATA / "processed"
    out.mkdir(exist_ok=True)
    tables = {name: {} for name in SCHEMAS}
    changes = read_layout_changes(out / "track_layouts.csv")
    failures = []
    for season in range(2006, 2027):
        for name, field in (("results", "Results"), ("qualifying", "QualifyingResults"),
                            ("sprint", "SprintResults")):
            if name == "sprint" and season < 2021:
                continue
            path = raw_dir / f"{name}_{season}.json"
            for page in json.loads(path.read_bytes()):
                for race in page["MRData"]["RaceTable"]["Races"]:
                    race_key = (int(race["season"]), int(race["round"]))
                    if name == "results":
                        circuit = race["Circuit"]
                        layout = layout_id(circuit["circuitId"], *race_key, changes)
                        tables["races"][race_key] = (*race_key, race["raceName"], race["date"],
                                                    circuit["circuitId"], circuit["circuitName"], layout)
                    for entry in race[field]:
                        key = (*race_key, entry["Driver"]["driverId"])
                        if key in tables[name]:
                            raise ValueError(f"Duplicate driver row in {name}: {key}")
                        common = (*key, entry["Constructor"]["constructorId"])
                        location = f"{path.name} round {race_key[1]} driver {key[2]}"
                        if name == "qualifying":
                            values = [seconds(entry.get(q), f"{location} {q}", failures)
                                      for q in ("Q1", "Q2", "Q3")]
                        else:
                            lap = entry.get("FastestLap", {}).get("Time", {}).get("time")
                            values = [entry["grid"], entry["position"], entry["status"],
                                      entry["points"], seconds(lap, f"{location} FastestLap", failures)]
                        tables[name][key] = (*common, *values)

    filled = fill_miami_times(raw_dir / "manual_qualifying_2025_06_miami.csv",
                              tables["qualifying"], failures)

    # Finish writing every CSV before replacing any previous output.
    with TemporaryDirectory(dir=out) as staging:
        for name, rows in tables.items():
            with (Path(staging) / f"{name}.csv").open("w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(SCHEMAS[name])
                writer.writerows(rows[key] for key in sorted(rows))
        for path in Path(staging).iterdir():
            path.replace(out / path.name)

    for name, rows in tables.items():
        print(f"{name}.csv: {len(rows):,} rows")
    print(f"Miami 2025 qualifying times filled from manual source: {filled}")
    print(f"Time conversion failures: {len(failures)}")
    for failure in failures:
        print(failure)


if __name__ == "__main__":
    main()
