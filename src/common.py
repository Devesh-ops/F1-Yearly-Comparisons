"""Shared data loading, scoring rules and season tags for the metric scripts."""

from pathlib import Path

import pandas as pd

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"

# Current FIA points systems, applied to every season (DECISIONS.md 3.2).
GP_POINTS = (25, 18, 15, 12, 10, 8, 6, 4, 2, 1)
SPRINT_POINTS = (8, 7, 6, 5, 4, 3, 2, 1)

# Races where only half points were awarded count at half weight (DECISIONS.md 3.3).
HALF_POINTS_RACES = {(2009, 2): "Malaysia 2009", (2021, 12): "Belgium 2021"}

# First season of each rule era (README, "The rule eras").
ERAS = {2006: "V8", 2009: "Aero overhaul", 2014: "Early hybrid",
        2017: "Wide cars", 2022: "Ground effect", 2026: "2026 rules"}


def load_processed(directory=PROCESSED):
    """Load the processed tables and add each row's team lineage."""
    tables = {name: pd.read_csv(directory / f"{name}.csv")
              for name in ("races", "team_lineage", "wet_sessions")}
    lineage = tables["team_lineage"].set_index("constructor_id", verify_integrity=True)["lineage"]
    for name in ("results", "sprint", "qualifying"):
        frame = pd.read_csv(directory / f"{name}.csv", dtype={"position_text": "string"})
        frame["lineage"] = frame["constructor"].map(lineage)
        missing = frame.loc[frame["lineage"].isna(), "constructor"].unique()
        if len(missing):
            raise ValueError(f"No lineage for {missing} in {name}.csv")
        tables[name] = frame
    return tables


def session_weight(season, round_number, session):
    """How much a win counts: Grand Prix 1, half-points race 1/2, sprint 1/3."""
    if session == "sprint":
        return 1 / 3
    if session != "race":
        raise ValueError(f"Session must be 'race' or 'sprint', not {session!r}")
    return 0.5 if (season, round_number) in HALF_POINTS_RACES else 1


def rescored_points(season, round_number, session, position_text):
    """Points under the current FIA system. Only classified finishers (numeric position) score.

    Sprint points aren't weighted again: the sprint table is already smaller.
    """
    position = str(position_text)
    if not position.isdigit():
        return 0
    weight = session_weight(season, round_number, session)  # also rejects a mistyped session
    scale = SPRINT_POINTS if session == "sprint" else GP_POINTS
    rank = int(position)
    if not 1 <= rank <= len(scale):
        return 0
    if session == "sprint":
        return scale[rank - 1]
    return scale[rank - 1] * weight


def season_tags():
    """One row per season: rule era, years since the last reset (0, 1, 2, 3+) and budget cap."""
    rows = []
    for season in range(2006, 2027):
        reset = max(year for year in ERAS if year <= season)
        age = season - reset
        rows.append((season, ERAS[reset], age, str(age) if age < 3 else "3+", season >= 2021))
    tags = pd.DataFrame(rows, columns=["season", "era", "years_since_reset_numeric",
                                       "years_since_reset", "budget_cap"])
    tags["years_since_reset"] = pd.Categorical(tags["years_since_reset"],
                                               categories=["0", "1", "2", "3+"], ordered=True)
    return tags
