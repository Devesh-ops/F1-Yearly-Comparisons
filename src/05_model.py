"""Assemble the Day 3 race table and fit the pre-registered pace models."""

from pathlib import Path

from matplotlib.figure import Figure
from scipy.stats import probplot
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import t
from statsmodels.stats.outliers_influence import variance_inflation_factor

from common import season_tags, session_weight

TABLES = Path(__file__).resolve().parents[1] / "outputs" / "tables"
KEY = ["season", "round"]
GAPS = ["field_spread", "dominance_margin"]


def build_model_data():
    quali = pd.read_csv(TABLES / "race_quali_gaps.csv")
    pace = pd.read_csv(TABLES / "race_pace_gaps.csv")
    data = quali[KEY + ["track_layout_id", "n_teams"]].copy()
    for suffix in ("", "_q1", "_last_common"):
        for gap in GAPS:
            data[gap + suffix] = quali[gap + suffix]

    # A zero means no wet/mixed flag was recorded. Weather confidence is unrestricted.
    data["wet"] = quali["wet_flag"].isin(["wet", "mixed"]).astype(int)
    data["refuel"] = data["season"].between(2006, 2009).astype(int)

    # Keep Belgium 2021's qualifying row even though it has no race-pace observation.
    pace = pace[KEY + GAPS].rename(columns={gap: gap + "_race" for gap in GAPS})
    data = data.merge(pace, on=KEY, how="left", validate="one_to_one")
    tags = season_tags().rename(columns={"years_since_reset": "ysr",
                                         "years_since_reset_numeric": "ysr_num",
                                         "budget_cap": "cap"})
    data = data.merge(tags[["season", "ysr", "ysr_num", "cap"]], on="season",
                      how="left", validate="many_to_one")
    data["cap"] = data["cap"].astype(int)
    return data.sort_values(KEY).reset_index(drop=True)


def model_a_vifs(data):
    # Dummy columns compare each category with the omitted first category (reset year for ysr).
    years = pd.get_dummies(data["ysr"], prefix="ysr", drop_first=True, dtype=float)
    tracks = pd.get_dummies(data["track_layout_id"], prefix="track", drop_first=True, dtype=float)
    predictors = pd.concat([years, data[["cap", "wet", "refuel", "round"]]], axis=1)
    # Each VIF measures overlap with all other Model A predictors, including layout effects.
    design = pd.concat([predictors, tracks], axis=1)
    design.insert(0, "intercept", 1.0)
    matrix = design.to_numpy(dtype=float)
    return pd.Series({col: variance_inflation_factor(matrix, design.columns.get_loc(col))
                      for col in predictors}, name="VIF")


def significance(p):
    if p < 0.05 / 6:
        return "both"
    if p < 0.05:
        return "5% only"
    return "neither"


YEAR_TERM = "C(ysr, Treatment(reference='0'))"
YEAR_COLS = [f"{YEAR_TERM}[T.{year}]" for year in ("1", "2", "3+")]
CONTROLS = "wet + refuel + round + C(track_layout_id)"


def clustered_fit(data, outcome, terms):
    controls = CONTROLS if data["wet"].nunique() > 1 else "refuel + round + C(track_layout_id)"
    formula = f"{outcome} ~ {terms} + {controls}"
    fit = smf.ols(formula, data=data, missing="raise").fit(
        cov_type="cluster", cov_kwds={"groups": data["season"], "use_correction": True,
                                      "df_correction": True}, use_t=True)
    df = data["season"].nunique() - 1
    if fit.df_resid_inference != df:
        raise ValueError("Unexpected cluster degrees of freedom")

    return fit


def coefficient_table(fit, cols):
    ci = fit.conf_int()
    return pd.DataFrame({"coef_pp": fit.params, "SE": fit.bse, "CI_low": ci[0],
                         "CI_high": ci[1], "p_two_sided": fit.pvalues}).loc[cols]


def cycle_test(fit):
    # Each restriction selects one cycle-year coefficient for the joint test.
    restrictions = np.eye(len(fit.params))[fit.params.index.get_indexer(YEAR_COLS)]
    joint = fit.f_test(restrictions)
    if (joint.df_num, joint.df_denom) != (3, fit.df_resid_inference):
        raise ValueError("Unexpected H1 test degrees of freedom")
    return joint


def report_model_a(data, outcome):
    fit = clustered_fit(data, outcome, YEAR_TERM + " + cap")
    df = fit.df_resid_inference
    cols = YEAR_COLS + ["cap", "wet", "refuel", "round"]
    table = coefficient_table(fit, cols)
    table.index = ["year 1", "year 2", "year 3+", *cols[3:]]
    joint = cycle_test(fit)
    statistic = fit.tvalues[YEAR_COLS[0]]
    p_left = t.cdf(statistic, df)  # H2 predicts a negative year-1 coefficient.
    report = (f"{outcome} (percentage points)\n{table.to_string(float_format='{:.5g}'.format)}"
              f"\nH1: F(3, {df}) = {joint.fvalue:.5g}, p = {joint.pvalue:.6g}, {significance(joint.pvalue)}"
              f"\nH2: t({df}) = {statistic:.5g}, lower-tail p = {p_left:.6g}, {significance(p_left)}")
    (TABLES / f"model_A_{outcome}.txt").write_text(fit.summary().as_text() + "\n\n" + report + "\n")
    print("\n" + report)
    return fit


def report_model_b(data, outcome):
    fit = clustered_fit(data, outcome, "ysr_num + cap + cap:ysr_num")
    table = coefficient_table(fit, ["ysr_num", "cap", "cap:ysr_num"])
    statistic = fit.tvalues["cap:ysr_num"]
    df = fit.df_resid_inference
    p_left = t.cdf(statistic, df)
    # In cap seasons both the base slope and the interaction apply.
    cap_slope = fit.t_test("ysr_num + cap:ysr_num = 0")
    low, high = cap_slope.conf_int()[0]
    report = (f"{outcome} (percentage points)\n{table.to_string(float_format='{:.5g}'.format)}"
              f"\nCap-era slope = {cap_slope.effect.item():.5g}, 95% CI [{low:.5g}, {high:.5g}]"
              f"\nH3: t({df}) = {statistic:.5g}, lower-tail p = {p_left:.6g}, {significance(p_left)}")
    (TABLES / f"model_B_{outcome}.txt").write_text(fit.summary().as_text() + "\n\n" + report + "\n")
    print("\n" + report)

    return fit


def diagnostics(data, outcome, fit, names):
    fig = Figure(figsize=(10, 4), layout="constrained")
    scatter, qq = fig.subplots(1, 2)
    scatter.scatter(fit.fittedvalues, fit.resid, s=12, alpha=0.55)
    scatter.axhline(0, color="black", linewidth=1)
    scatter.set(xlabel="Fitted gap (percentage points)", ylabel="Residual (percentage points)",
                title="Residuals vs fitted")
    probplot(fit.resid, plot=qq)
    qq.set(title="Normal Q–Q plot", xlabel="Theoretical normal quantile",
           ylabel="Ordered residual (percentage points)")
    fig.suptitle("Model A · " + outcome.replace("_", " ").capitalize())
    charts = TABLES.parent / "charts"
    charts.mkdir(exist_ok=True)
    fig.savefig(charts / f"diagnostics_{outcome}.png", dpi=160)

    singleton = data.groupby("track_layout_id")["season"].transform("size").eq(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        distances = fit.get_influence().cooks_distance[0]
    races = data[KEY + ["track_layout_id", "wet"]].join(names, on=KEY, validate="one_to_one")
    races["cooks_distance"] = distances
    top = races.loc[~singleton & np.isfinite(distances)].nlargest(10, "cooks_distance")
    trimmed = clustered_fit(data.drop(index=top.index), outcome, YEAR_TERM + " + cap")
    comparison = pd.DataFrame(
        [(model.nobs, model.params[YEAR_COLS[0]], cycle_test(model).pvalue)
         for model in (fit, trimmed)], index=["Original", "Drop ten"],
        columns=["races", "year_1_pp", "H1_p"])
    report = (f"{outcome}: ten largest Cook's distances\n{top.to_string(index=False)}"
              f"\n\nSingleton layouts (excluded from influence ranking)\n"
              + races.loc[singleton, KEY + ["race_name", "track_layout_id"]].to_string(index=False)
              + "\n\n" + comparison.to_string())
    (TABLES / f"diagnostics_{outcome}.txt").write_text(report + "\n")
    print("\n" + report)
    return top.index


def robustness_row(run, outcome, a, b):
    return dict(run=run, outcome=outcome, races=int(a.nobs), beta1=a.params[YEAR_COLS[0]],
                H2_p=t.cdf(a.tvalues[YEAR_COLS[0]], a.df_resid_inference),
                H1_p=cycle_test(a).pvalue, phi=b.params["cap:ysr_num"],
                H3_p=t.cdf(b.tvalues["cap:ysr_num"], b.df_resid_inference),
                cap_A=a.params["cap"], cap_A_p_two_sided=a.pvalues["cap"],
                beta1_low=a.conf_int().loc[YEAR_COLS[0], 0], beta1_high=a.conf_int().loc[YEAR_COLS[0], 1],
                phi_low=b.conf_int().loc["cap:ysr_num", 0], phi_high=b.conf_int().loc["cap:ysr_num", 1])


def robustness_rows(data, outcome, influential, main_a, main_b):
    frequency = data.groupby("track_layout_id")["season"].transform("size")
    rows = [robustness_row("main", outcome, main_a, main_b)]
    # Each run changes only the indicated sample, outcome or predictor.
    runs = [
        ("Q1 only", data, "_q1", ""),
        ("last common", data, "_last_common", ""),
        ("race pace", data, "_race", ""),
        ("drop flagged wet", data[data.wet == 0], "", ""),
        ("layouts >=10", data[frequency >= 10], "", ""),
        ("layouts >=3", data[frequency >= 3], "", ""),
        ("linear trend", data.assign(trend=data.season - 2006), "", " + trend"),
        ("team count", data, "", " + n_teams"),
        ("drop 2026", data[data.season != 2026], "", ""),
        ("drop influential", data.drop(index=influential), "", ""),
    ]
    for label, sample, suffix, extra in runs:
        target = outcome + suffix
        sample = sample.dropna(subset=[target])
        a = clustered_fit(sample, target, YEAR_TERM + " + cap" + extra)
        b = clustered_fit(sample, target, "ysr_num + cap + cap:ysr_num" + extra)
        rows.append(robustness_row(label, outcome, a, b))
    return rows


def write_rankings(residuals, seasons):
    ranking = pd.DataFrame(residuals).groupby(seasons).mean()
    for outcome in GAPS:
        ranking[outcome + "_rank"] = ranking[outcome].rank(ascending=False, method="min").astype(int)
        print(f"\nAdjusted {outcome}, widest to closest (percentage points)")
        print(ranking[outcome].sort_values(ascending=False).to_string())
    ranking.sort_values("field_spread", ascending=False).to_csv(TABLES / "rule_adjusted_ranking.csv")


def outcome_side():
    seasons = pd.read_csv(TABLES / "season_scorecard.csv").rename(columns={
        "years_since_reset": "ysr", "years_since_reset_numeric": "ysr_num", "budget_cap": "cap"})
    seasons["cap"] = seasons.cap.astype(int)
    means = seasons.groupby("ysr")[["win_hhi", "win_effective_teams"]].mean()
    fit = smf.ols("win_hhi ~ ysr_num + cap", data=seasons, missing="raise").fit(cov_type="HC3", use_t=True)

    weekends = pd.read_csv(TABLES / "race_outcomes.csv")
    winners = weekends.dropna(subset=["gp_winning_driver"]).copy()
    winners["wins"] = [session_weight(r.season, r.round, "race") for r in winners.itertuples()]
    wins = winners.groupby(["season", "lineage"]).wins.sum()
    shares = wins / wins.groupby(level="season").transform("sum")
    comparison = seasons.set_index("season")[["win_hhi"]].copy()
    comparison["win_hhi_zero_sprint"] = 10000 * shares.pow(2).groupby(level="season").sum()
    report = ("Descriptive season outcomes: equal weight per season\n" + means.to_string()
              + "\n\n" + fit.summary().as_text() + "\n\n" + comparison.to_string())
    (TABLES / "outcome_side.txt").write_text(report + "\n")
    print(report)


def exploratory(data, outcome):
    sample = data.assign(reset=data.ysr_num.eq(0).astype(int))
    # The cycle-year categories already account for the reset-year main effect.
    fit = clustered_fit(sample, outcome, YEAR_TERM + " + cap + round:reset")
    report = ("EXPLORATORY: round-by-reset interaction, " + outcome + "\n"
              + fit.summary().as_text())
    (TABLES / f"exploratory_{outcome}.txt").write_text(report + "\n")


def leader_turnover(data):
    teams = pd.read_csv(TABLES / "team_quali_gaps.csv")
    fastest = teams[teams.best_seconds == teams.leader_seconds]
    counts = fastest.groupby(["season", "lineage"]).size()
    weekends = data.groupby("season").size()
    resets = data.groupby("season").ysr_num.first().eq(0)
    previous = set()
    rows = []
    for season, group in counts.groupby(level="season"):
        leaders = set(group[group == group.max()].index.get_level_values("lineage"))
        # Continuity requires at least one returning co-leader.
        rows.append(dict(season=season, qualifying_sessions=weekends[season],
                         fastest_lineages=" | ".join(sorted(leaders)),
                         sessions_fastest_per_leader=group.max(), reset_year=resets[season],
                         changed=None if not previous else previous.isdisjoint(leaders)))
        previous = leaders
    result = pd.DataFrame(rows)
    result.to_csv(TABLES / "exploratory_leader_turnover.csv", index=False)
    print("EXPLORATORY leader turnover by reset status")
    print(result.dropna(subset=["changed"]).groupby("reset_year").changed.agg(["sum", "count"]))


if __name__ == "__main__":
    data = build_model_data()
    data.to_csv(TABLES / "model_data.csv", index=False)
    print(f"Races: {len(data)}")
    print("\nRaces by years since reset")
    print(data["ysr"].value_counts(sort=False).to_string())
    print("\nRaces with indicator equal to 1")
    print(data[["cap", "wet", "refuel"]].sum().to_string())
    print("\nModel A predictor VIFs (including layout effects in the design)")
    print(model_a_vifs(data).to_string(float_format="{:.4f}".format))
    names = pd.read_csv(TABLES.parents[1] / "data/processed/races.csv").set_index(KEY)["race_name"]
    residuals = {}
    rows = []
    for outcome in GAPS:
        fit = report_model_a(data, outcome)
        model_b = report_model_b(data, outcome)
        influential = diagnostics(data, outcome, fit, names)
        residuals[outcome] = fit.resid
        rows.extend(robustness_rows(data, outcome, influential, fit, model_b))
        exploratory(data, outcome)
    write_rankings(residuals, data.season)
    outcome_side()
    robustness = pd.DataFrame(rows)
    # Print the main specifications together, followed by each paired sensitivity run.
    robustness["run"] = pd.Categorical(robustness.run, robustness.run.unique(), ordered=True)
    robustness = robustness.sort_values("run", kind="stable")
    robustness.to_csv(TABLES / "robustness.csv", index=False)
    print("\nRobustness checks\n" + robustness.to_string(index=False))
    leader_turnover(data)
