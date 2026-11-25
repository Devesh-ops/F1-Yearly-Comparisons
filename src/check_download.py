"""Check round coverage and Grand Prix winners in the saved Jolpica pages."""

import json
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def read_rounds(season, endpoint, row_key):
    path = RAW / f"{endpoint}_{season}.json"
    rounds = {}
    for page in json.loads(path.read_bytes()):
        for race in page["MRData"]["RaceTable"]["Races"]:
            # A round can span two API pages. Keep every driver's row.
            number = int(race["round"])
            name, rows = rounds.setdefault(number, (race["raceName"], []))
            rows.extend(race[row_key])
    return rounds


def main():
    print("Season  Results  Qualifying  Sprints")
    flags = 0
    for season in range(2006, 2027):
        issues = []
        data = {}
        for endpoint, key in (("results", "Results"), ("qualifying", "QualifyingResults"),
                              ("sprint", "SprintResults")):
            if endpoint == "sprint" and season < 2021:
                data[endpoint] = {}
                continue
            try:
                data[endpoint] = read_rounds(season, endpoint, key)
            except (OSError, ValueError, KeyError, TypeError) as error:
                data[endpoint] = None
                issues.append(f"Cannot check {endpoint}: {error}")

        results, qualifying, sprints = (data[k] for k in ("results", "qualifying", "sprint"))
        counts = ["?" if races is None else str(sum(bool(rows) for _, rows in races.values()))
                  for races in (results, qualifying, sprints)]
        print(f"{season}  {counts[0]:>7}  {counts[1]:>10}  {counts[2]:>7}")
        for number, (name, rows) in sorted((results or {}).items()):
            label = f"Round {number} ({name})"
            if qualifying is not None and (number not in qualifying or not qualifying[number][1]):
                issues.append(f"{label}: missing qualifying data")
            winners = sum(str(row.get("position")) == "1" for row in rows)
            if winners != 1:
                issues.append(f"{label}: {'no winner' if winners == 0 else 'multiple winners'}")
        for issue in issues:
            print(f"  FLAG  {issue}")
        flags += len(issues)
    print(f"Total flags: {flags}")


if __name__ == "__main__":
    main()
