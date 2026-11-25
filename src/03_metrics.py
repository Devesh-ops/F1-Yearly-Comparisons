"""Build qualifying and race-pace gap tables from the cleaned timing data."""

from pathlib import Path

import pandas as pd

from common import load_processed, rescored_points, session_weight

OUT = Path(__file__).resolve().parents[1] / "outputs" / "tables"
KEY = ["season", "round"]
SEGMENTS = ["Q1", "Q2", "Q3"]


def lap_summary(times):
    """Summarize a Series indexed by season, round and lineage (seconds)."""
    laps = times.dropna().sort_values()
    fastest = laps.groupby(level=KEY).transform("min")
    gaps = 100 * (laps - fastest) / fastest
    grouped = gaps.groupby(level=KEY)
    summary = grouped.agg(n_teams="size", field_spread="median")
    runner_up = gaps[grouped.cumcount() == 1].droplevel("lineage")
    summary["dominance_margin"] = runner_up
    return summary


def qualifying_tables(data):
    quali = data["qualifying"].rename(columns={f"{s.lower()}_seconds": s for s in SEGMENTS})
    quali.loc[quali.season <= 2009, "Q3"] = float("nan")
    best = quali.groupby(KEY + ["lineage"], as_index=False)[SEGMENTS].min().dropna(subset=["Q1"])
    team_rows, race_rows = [], []
    for (season, round_number), group in best.groupby(KEY):
        # Missing times sort last, so a Q3 time outranks any Q2-only team.
        teams = group.sort_values(["Q3", "Q2", "Q1", "lineage"], na_position="last")
        leader = teams.iloc[0]
        comparisons = []
        for rank, (_, team) in enumerate(teams.iterrows(), start=1):
            segment = next(s for s in reversed(SEGMENTS) if pd.notna(team[s]) and pd.notna(leader[s]))
            gap = 100 * (team[segment] - leader[segment]) / leader[segment]
            comparisons.append((gap, segment))
            team_rows.append((season, round_number, rank, team.lineage, *team[SEGMENTS],
                              segment, leader[segment], gap))
        margin, margin_session = comparisons[1] if len(comparisons) >= 2 else (None, None)
        spread = pd.Series([gap for gap, _ in comparisons]).median()
        race_rows.append((season, round_number, len(teams), spread, margin, margin_session))

    team_table = pd.DataFrame(team_rows, columns=KEY + [
        "rank_last_common", "lineage", *SEGMENTS, "session_last_common",
        "leader_seconds_last_common", "gap_pct_last_common"])
    team_table["best_seconds"] = team_table[SEGMENTS].min(axis=1)
    team_table["best_session"] = team_table[SEGMENTS].idxmin(axis=1)
    team_table = team_table.sort_values(KEY + ["best_seconds", "rank_last_common"])
    grouped = team_table.groupby(KEY)
    team_table["rank"] = grouped.cumcount() + 1
    team_table["leader_seconds"] = grouped["best_seconds"].transform("min")
    team_table["gap_pct"] = 100 * (team_table.best_seconds - team_table.leader_seconds) / team_table.leader_seconds

    summaries = pd.DataFrame(race_rows, columns=KEY + [
        "n_teams", "field_spread_last_common", "dominance_margin_last_common",
        "margin_session_last_common"])
    spreads = grouped["gap_pct"].median().rename("field_spread")
    margins = team_table.query("rank == 2").set_index(KEY)["gap_pct"].rename("dominance_margin")
    summaries = summaries.join(spreads, on=KEY).join(margins, on=KEY)
    q1 = lap_summary(best.set_index(KEY + ["lineage"])["Q1"])
    summaries = summaries.join(q1.drop(columns="n_teams").add_suffix("_q1"), on=KEY)
    weather = data["wet_sessions"].query("session == 'qualifying'").rename(
        columns={"condition": "wet_flag", "confidence": "wet_confidence"})
    races = data["races"][KEY + ["track_layout_id"]].merge(summaries, on=KEY, how="left",
                                                          validate="one_to_one")
    races["n_teams"] = races["n_teams"].fillna(0).astype(int)
    races = races.merge(weather[KEY + ["wet_flag", "wet_confidence"]], on=KEY, how="left",
                        validate="one_to_one")
    races["wet_flag"] = races["wet_flag"].fillna("unknown")
    return races, team_table


def race_pace_table(data):
    races = data["races"].set_index(KEY)[["track_layout_id"]].drop(index=(2021, 12), errors="ignore")
    times = data["results"].groupby(KEY + ["lineage"])["fastest_lap_seconds"].min()
    pace = races.join(lap_summary(times))
    pace["n_teams"] = pace["n_teams"].fillna(0).astype(int)
    return pace.reset_index()


def print_checks(quali, pace, races):
    matched = quali.merge(pace, on=KEY, suffixes=("", "_race"), validate="one_to_one")
    for metric in ("field_spread", "dominance_margin"):
        cols = [metric, metric + "_last_common", metric + "_q1", metric + "_race"]
        values = matched[cols].dropna()
        values.columns = ["Best lap", "Last common", "Q1 only", "Race pace"]
        print(f"\n{metric} Pearson correlations ({len(values)} common races)")
        print(values.corr().round(4).to_string())

    diffs = quali.merge(races[KEY + ["race_name"]], on=KEY, validate="one_to_one")
    diffs["absolute_diff_pp"] = (diffs.field_spread - diffs.field_spread_q1).abs()
    cols = KEY + ["race_name", "field_spread", "field_spread_q1", "absolute_diff_pp"]
    print("\nFive largest field-spread differences (percentage points)")
    print(diffs.nlargest(5, "absolute_diff_pp")[cols].to_string(index=False))


def race_outcomes(data):
    sessions = []
    for source, session in [("results", "race"), ("sprint", "sprint")]:
        rows = data[source].copy()
        winners = rows.position_text.eq("1")
        counts = winners.groupby([rows.season, rows["round"]]).sum()
        if not counts.eq(1).all():
            raise ValueError(f"Expected one classified winner per {session}")
        rows["weighted_wins"] = 0.0
        rows.loc[winners, "weighted_wins"] = [
            session_weight(r.season, r.round, session) for r in rows[winners].itertuples()]
        rows["rescored_points"] = [
            rescored_points(r.season, r.round, session, r.position_text) for r in rows.itertuples()]
        rows["gp_winning_driver"] = rows.driver.where(winners & (session == "race"))
        rows["gp_started"] = ((session == "race") & rows.position_text.ne("W")
                              & ~rows.status.isin(["Did not start", "Withdrew"]))
        sessions.append(rows)
    return pd.concat(sessions).groupby(KEY + ["lineage"], as_index=False).agg(
        weighted_wins=("weighted_wins", "sum"), rescored_points=("rescored_points", "sum"),
        api_points=("points", "sum"), gp_started=("gp_started", "any"),
        gp_winning_driver=("gp_winning_driver", "first"))


if __name__ == "__main__":
    data = load_processed()
    races, teams = qualifying_tables(data)
    pace = race_pace_table(data)
    OUT.mkdir(parents=True, exist_ok=True)
    races.to_csv(OUT / "race_quali_gaps.csv", index=False)
    teams.to_csv(OUT / "team_quali_gaps.csv", index=False)
    pace.to_csv(OUT / "race_pace_gaps.csv", index=False)
    print(f"{len(races)} races, {len(teams)} eligible team entries")
    for season in (2023, 2008):
        print(teams.loc[(teams.season == season) & (teams["round"] == 1)].to_string(index=False))
    print_checks(races, pace, data["races"])

    outcomes = race_outcomes(data)
    outcomes.to_csv(OUT / "race_outcomes.csv", index=False)
    print("\nTotal weighted wins by season")
    print(outcomes.groupby("season").weighted_wins.sum().to_string())
    print("\nLineage points checks")
    print(outcomes.query("season in [2008, 2023]").groupby(["season", "lineage"])[
        ["rescored_points", "api_points"]].sum().to_string())
