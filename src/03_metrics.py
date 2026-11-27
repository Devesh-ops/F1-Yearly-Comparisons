"""Per-race pace gaps and outcomes, written to outputs/tables/.

Pace (DECISIONS.md section 2): for every race, each team lineage's gap to the fastest
team in %, summarised as field spread (median gap) and dominance margin (2nd team's gap).
Main method: each team's best qualifying lap from any session. Robustness versions:
Q1 only, last session both teams ran, and fastest race lap.
Outcomes (section 3): weighted wins and rescored points per lineage per race weekend.
"""

from pathlib import Path

import pandas as pd

from common import load_processed, rescored_points, session_weight

OUT = Path(__file__).resolve().parents[1] / "outputs" / "tables"
KEY = ["season", "round"]
SEGMENTS = ["Q1", "Q2", "Q3"]


def lap_summary(times):
    """Field spread and dominance margin per race.

    `times` is a Series of lap times in seconds indexed by season, round and lineage.
    """
    laps = times.dropna().sort_values()
    fastest = laps.groupby(level=KEY).transform("min")
    gaps = 100 * (laps - fastest) / fastest
    grouped = gaps.groupby(level=KEY)
    summary = grouped.agg(n_teams="size", field_spread="median")
    summary["dominance_margin"] = gaps[grouped.cumcount() == 1].droplevel("lineage")
    return summary


def team_session_bests(data):
    """Each lineage's best lap in Q1, Q2 and Q3 per race.

    Q3 is dropped for 2006 to 2009 (run on race fuel, DECISIONS.md 2.4). Teams with no
    Q1 time had their qualifying deleted and are left out (DECISIONS.md 5.2).
    """
    quali = data["qualifying"].rename(columns={f"{s.lower()}_seconds": s for s in SEGMENTS})
    quali.loc[quali.season <= 2009, "Q3"] = float("nan")
    bests = quali.groupby(KEY + ["lineage"], as_index=False)[SEGMENTS].min()
    return bests.dropna(subset=["Q1"])


def last_common_session(bests):
    """Robustness version (DECISIONS.md 2.3, superseded as main method by 2.12).

    Each team is compared with the leader in the last session both ran.
    """
    team_rows, race_rows = [], []
    for (season, round_number), group in bests.groupby(KEY):
        # Teams reaching a later session rank higher; missing times sort last.
        teams = group.sort_values(["Q3", "Q2", "Q1", "lineage"], na_position="last")
        leader = teams.iloc[0]
        gaps, sessions = [], []
        for rank, team in enumerate(teams.itertuples(index=False), start=1):
            segment = next(s for s in reversed(SEGMENTS)
                           if pd.notna(getattr(team, s)) and pd.notna(leader[s]))
            gap = 100 * (getattr(team, segment) - leader[segment]) / leader[segment]
            gaps.append(gap)
            sessions.append(segment)
            team_rows.append((season, round_number, rank, team.lineage, team.Q1, team.Q2, team.Q3,
                              segment, leader[segment], gap))
        margin = gaps[1] if len(gaps) > 1 else None
        session = sessions[1] if len(gaps) > 1 else None
        race_rows.append((season, round_number, len(teams), pd.Series(gaps).median(), margin, session))

    teams = pd.DataFrame(team_rows, columns=KEY + [
        "rank_last_common", "lineage", *SEGMENTS, "session_last_common",
        "leader_seconds_last_common", "gap_pct_last_common"])
    races = pd.DataFrame(race_rows, columns=KEY + [
        "n_teams", "field_spread_last_common", "dominance_margin_last_common",
        "margin_session_last_common"])
    return teams, races


def qualifying_tables(data):
    """Race-level and team-level qualifying gaps for all three methods."""
    bests = team_session_bests(data)
    teams, races = last_common_session(bests)

    # Main method (DECISIONS.md 2.12): each team's best lap from any session.
    teams["best_seconds"] = teams[SEGMENTS].min(axis=1)
    teams["best_session"] = teams[SEGMENTS].idxmin(axis=1)
    # Equal best laps keep the official qualifying order.
    teams = teams.sort_values(KEY + ["best_seconds", "rank_last_common"])
    teams["rank"] = teams.groupby(KEY).cumcount() + 1
    teams["leader_seconds"] = teams.groupby(KEY)["best_seconds"].transform("min")
    teams["gap_pct"] = 100 * (teams.best_seconds - teams.leader_seconds) / teams.leader_seconds

    lineage_index = KEY + ["lineage"]
    best_lap = lap_summary(teams.set_index(lineage_index)["best_seconds"])
    q1_only = lap_summary(bests.set_index(lineage_index)["Q1"])
    races = (races.join(best_lap.drop(columns="n_teams"), on=KEY)
             .join(q1_only.drop(columns="n_teams").add_suffix("_q1"), on=KEY))

    weather = data["wet_sessions"].query("session == 'qualifying'").rename(
        columns={"condition": "wet_flag", "confidence": "wet_confidence"})
    races = (data["races"][KEY + ["track_layout_id"]]
             .merge(races, on=KEY, how="left", validate="one_to_one")
             .merge(weather[KEY + ["wet_flag", "wet_confidence"]], on=KEY, how="left",
                    validate="one_to_one"))
    races["n_teams"] = races["n_teams"].fillna(0).astype(int)
    races["wet_flag"] = races["wet_flag"].fillna("unknown")
    return races, teams


def race_pace_table(data):
    """Gaps from each lineage's fastest race lap. Belgium 2021 had no racing laps."""
    races = data["races"].set_index(KEY)[["track_layout_id"]].drop(index=(2021, 12))
    times = data["results"].groupby(KEY + ["lineage"])["fastest_lap_seconds"].min()
    pace = races.join(lap_summary(times))
    pace["n_teams"] = pace["n_teams"].fillna(0).astype(int)
    return pace.reset_index()


def race_outcomes(data):
    """Weighted wins and rescored points per lineage per race weekend (GP plus sprint)."""
    sessions = []
    for source, session in [("results", "race"), ("sprint", "sprint")]:
        rows = data[source].copy()
        winners = rows.position_text.eq("1")
        if not winners.groupby([rows.season, rows["round"]]).sum().eq(1).all():
            raise ValueError(f"Expected one classified winner per {session}")
        rows["weighted_wins"] = 0.0
        rows.loc[winners, "weighted_wins"] = [
            session_weight(r.season, r.round, session) for r in rows[winners].itertuples()]
        rows["rescored_points"] = [
            rescored_points(r.season, r.round, session, r.position_text) for r in rows.itertuples()]
        rows["gp_winning_driver"] = rows.driver.where(winners & (session == "race"))
        # Counts towards "lineages that started a race" in the scorecard.
        rows["gp_started"] = ((session == "race") & rows.position_text.ne("W")
                              & ~rows.status.isin(["Did not start", "Withdrew"]))
        sessions.append(rows)
    return pd.concat(sessions).groupby(KEY + ["lineage"], as_index=False).agg(
        weighted_wins=("weighted_wins", "sum"), rescored_points=("rescored_points", "sum"),
        gp_started=("gp_started", "any"), gp_winning_driver=("gp_winning_driver", "first"))


if __name__ == "__main__":
    data = load_processed()
    races, teams = qualifying_tables(data)
    pace = race_pace_table(data)
    outcomes = race_outcomes(data)

    OUT.mkdir(parents=True, exist_ok=True)
    races.to_csv(OUT / "race_quali_gaps.csv", index=False)
    teams.to_csv(OUT / "team_quali_gaps.csv", index=False)
    pace.to_csv(OUT / "race_pace_gaps.csv", index=False)
    outcomes.to_csv(OUT / "race_outcomes.csv", index=False)
    print(f"Qualifying: {len(races)} races, {len(teams)} team entries")
    print(f"Race pace: {len(pace)} races")
    print(f"Outcomes: {len(outcomes)} lineage-weekend rows")
