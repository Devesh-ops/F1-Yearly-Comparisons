"""Shared inputs and scoring conventions for the F1 metrics scripts."""

from pathlib import Path

import pandas as pd

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
GP_POINTS = (25, 18, 15, 12, 10, 8, 6, 4, 2, 1)
SPRINT_POINTS = (8, 7, 6, 5, 4, 3, 2, 1)
ERAS = {
    2006: "V8",
    2009: "Aero overhaul",
    2014: "Early hybrid",
    2017: "Wide cars",
    2022: "Ground effect",
    2026: "2026 rules",
}


def load_processed(directory=PROCESSED):
    """Load the analysis inputs and attach lineage to every driver row."""
    tables = {name: pd.read_csv(directory / f"{name}.csv")
              for name in ("races", "team_lineage", "wet_sessions", "track_layouts")}
    lineage = tables["team_lineage"].set_index("constructor_id", verify_integrity=True)["lineage"]
    for name in ("results", "sprint", "qualifying"):
        frame = pd.read_csv(directory / f"{name}.csv", dtype={"position_text": "string"})
        frame["lineage"] = frame["constructor"].map(lineage)
        if frame["lineage"].isna().any():
            missing = frame.loc[frame["lineage"].isna(), "constructor"].unique()
            raise ValueError(f"Missing lineage in {name}: {missing}")
        tables[name] = frame
    return tables


def session_weight(season, round_number, session):
    """Outcome weight for wins. Sprint points already have their own scale."""
    if session == "sprint":
        return 1 / 3
    if session != "race":
        raise ValueError("Expected race or sprint")
    return 0.5 if (season, round_number) in {(2009, 2), (2021, 12)} else 1


def rescored_points(season, round_number, session, position_text):
    """Award points only for a numeric classified position."""
    weight = session_weight(season, round_number, session)
    position = str(position_text)
    if not position.isascii() or not position.isdecimal():
        return 0
    scale = SPRINT_POINTS if session == "sprint" else GP_POINTS
    rank = int(position)
    if not 1 <= rank <= len(scale):
        return 0
    points = scale[rank - 1]
    return points if session == "sprint" else points * weight


def season_tags():
    """One row per project season, with ordered cycle-age categories."""
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
