"""Build the season scorecard from the weekend outcome and pace tables."""

from pathlib import Path

import pandas as pd

from common import season_tags

OUT = Path(__file__).resolve().parents[1] / "outputs" / "tables"
PACE = ["field_spread", "dominance_margin"]


def season_scorecard():
    outcomes = pd.read_csv(OUT / "race_outcomes.csv")
    quali = pd.read_csv(OUT / "race_quali_gaps.csv")
    pace = pd.read_csv(OUT / "race_pace_gaps.csv")
    card = season_tags().set_index("season")
    totals = outcomes.groupby(["season", "lineage"])[["weighted_wins", "rescored_points"]].sum()
    for col, name in [("weighted_wins", "win"), ("rescored_points", "points")]:
        shares = totals[col] / totals[col].groupby(level="season").transform("sum")
        hhi = 10000 * shares.pow(2).groupby(level="season").sum()
        card[name + "_hhi"] = hhi
        card[name + "_effective_teams"] = 10000 / hhi

    starters = outcomes[outcomes.gp_started]
    winners = outcomes.dropna(subset=["gp_winning_driver"])
    card["starting_lineages"] = starters.groupby("season").lineage.nunique()
    card["gp_winning_lineages"] = winners.groupby("season").lineage.nunique()
    card["gp_winning_drivers"] = winners.groupby("season").gp_winning_driver.nunique()
    card["wet_qualifying_sessions"] = quali.wet_flag.isin(["wet", "mixed"]).groupby(quali.season).sum()
    for suffix, label in [("", "best_lap"), ("_q1", "q1"), ("_last_common", "last_common")]:
        cols = [m + suffix for m in PACE]
        medians = quali.groupby("season")[cols].median()
        medians.columns = [m + "_" + label for m in PACE]
        card = card.join(medians)
    return card.join(pace.groupby("season")[PACE].median().add_suffix("_race")).sort_index()


if __name__ == "__main__":
    card = season_scorecard()
    card.to_csv(OUT / "season_scorecard.csv")
    print(card.round(4).to_string())
    print("\nWin HHI benchmarks")
    print(card.loc[[2012, 2023], "win_hhi"].to_string())
    for metric in PACE:
        paired = card[[metric + "_best_lap", metric + "_race"]].dropna()
        print(f"{metric} season-median Pearson r ({len(paired)} seasons): {paired.corr().iloc[0, 1]:.6f}")
