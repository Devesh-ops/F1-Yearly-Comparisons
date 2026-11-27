"""Optional review printouts. Not needed to rebuild the results.

Run after 03_metrics.py. Writes two text files to outputs/tables/:
- pace_comparison.txt: how the qualifying methods and race pace correlate, and the
  races where best-lap and Q1-only disagree most.
- outcome_checks.txt: weighted wins per season, and rescored vs official points for 2008 and 2023.
Also prints the two races Claude checked by hand (Bahrain 2023, Australia 2008).
"""

from pathlib import Path

import pandas as pd

from common import load_processed

OUT = Path(__file__).resolve().parents[1] / "outputs" / "tables"
KEY = ["season", "round"]


def pace_comparison(quali, pace, races):
    lines = []
    matched = quali.merge(pace, on=KEY, suffixes=("", "_race"), validate="one_to_one")
    for metric in ("field_spread", "dominance_margin"):
        values = matched[[metric, metric + "_last_common", metric + "_q1", metric + "_race"]].dropna()
        values.columns = ["Best lap", "Last common", "Q1 only", "Race pace"]
        lines += [f"{metric} Pearson correlations ({len(values)} common races)",
                  values.corr().round(4).to_string(), ""]
    diffs = quali.merge(races[KEY + ["race_name"]], on=KEY, validate="one_to_one")
    diffs["absolute_diff_pp"] = (diffs.field_spread - diffs.field_spread_q1).abs()
    cols = KEY + ["race_name", "field_spread", "field_spread_q1", "absolute_diff_pp"]
    lines += ["Five largest field-spread differences (percentage points)",
              diffs.nlargest(5, "absolute_diff_pp")[cols].to_string(index=False)]
    return "\n".join(lines) + "\n"


def outcome_checks(outcomes, data):
    official = pd.concat([data["results"], data["sprint"]]).groupby(
        KEY + ["lineage"], as_index=False)["points"].sum().rename(columns={"points": "api_points"})
    points = outcomes.merge(official, on=KEY + ["lineage"], how="outer", validate="one_to_one",
                            indicator=True)
    if not points["_merge"].eq("both").all():
        raise ValueError("Outcome and official points rows don't match up")
    table = points.query("season in [2008, 2023]").groupby(["season", "lineage"])[
        ["rescored_points", "api_points"]].sum()
    return ("Total weighted wins by season\n"
            + outcomes.groupby("season").weighted_wins.sum().to_string()
            + "\n\nLineage points checks\n" + table.to_string() + "\n")


if __name__ == "__main__":
    data = load_processed()
    quali = pd.read_csv(OUT / "race_quali_gaps.csv")
    pace = pd.read_csv(OUT / "race_pace_gaps.csv")
    teams = pd.read_csv(OUT / "team_quali_gaps.csv")
    outcomes = pd.read_csv(OUT / "race_outcomes.csv")

    (OUT / "pace_comparison.txt").write_text(pace_comparison(quali, pace, data["races"]))
    (OUT / "outcome_checks.txt").write_text(outcome_checks(outcomes, data))
    for season in (2023, 2008):
        print(teams.query("season == @season and round == 1").to_string(index=False), "\n")
