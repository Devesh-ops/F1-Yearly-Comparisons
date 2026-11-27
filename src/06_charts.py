"""Reproduce the seven Day 3 figures from the Day 2–3 tables."""
from importlib import import_module

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import t

from common import ERAS

model = import_module("05_model")
TABLES = model.TABLES
CHARTS = TABLES.parent / "charts"
BLUE, ORANGE = "#126783", "#ac491d"
LABELS = ["Field spread", "Dominance margin"]


def save(fig, name):
    fig.savefig(CHARTS / (name + ".png"), dpi=180, bbox_inches="tight")
    plt.close(fig)


def timeline(card, cols, labels, title, unit, name):
    fig, ax = plt.subplots(figsize=(10, 4.5), layout="constrained")
    for year in ERAS:
        ax.axvspan(year - .45, year + .45, color="#e7e7d9", zorder=0,
                   label="Reset year" if year == 2006 else None)
    for col, label, color in zip(cols, labels, [BLUE, ORANGE]):
        ax.plot(card.season, card[col], ".-", color=color, label=label)
    ax.set(title=title, xlabel="Season  ·  2026 provisional (21 rounds)", ylabel=unit,
           xticks=range(2006, 2027, 2), xlim=(2005.5, 2026.5))
    ax.set_ylim(0, 10000 if name == "win_hhi" else None)
    if name == "qualifying_timeline":
        ax.axvspan(2005.5, 2009.5, facecolor="none", hatch="//", edgecolor="#b3bfca",
                   linewidth=0, zorder=0, label="Q3 not used (race fuel)")
        ax.set_title("")
        fig.suptitle(title)
        ax.legend(loc="lower center", bbox_to_anchor=(.5, 1), ncol=4, frameon=False)
    else:
        ax.legend(ncol=3)
    save(fig, name)


def model_charts(data):
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    for i, (outcome, label) in enumerate(zip(model.GAPS, LABELS)):
        fit = model.clustered_fit(data, outcome, model.YEAR_TERM + " + cap")
        estimates = fit.params[model.YEAR_COLS].to_numpy()
        bounds = fit.conf_int().loc[model.YEAR_COLS].to_numpy()
        ax.errorbar(np.arange(3) + (i - .5) * .15, estimates,
                    yerr=[estimates - bounds[:, 0], bounds[:, 1] - estimates],
                    fmt="o", capsize=4, color=[BLUE, ORANGE][i], label=label)
    ax.axhline(0, color="gray", lw=1)
    ax.set(xticks=range(3), xticklabels=["1", "2", "3+"], xlabel="Years since reset",
           ylabel="Difference from reset year (pp)", title="Model A · Cycle-year estimates and 95% intervals")
    ax.legend()
    save(fig, "cycle_year_coefficients")

    fit = model.clustered_fit(data, "field_spread", "ysr_num + cap + cap:ysr_num")
    fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
    for cap, label, color in [(0, "Before cap", BLUE), (1, "Cap era", ORANGE)]:
        years = sorted(data.loc[data.cap == cap, "ysr_num"].unique())
        means, widths = [], []
        for year in years:
            # Standardize both lines to the same observed race mix. The contrast
            # of mean design rows uses the full season-clustered covariance.
            x = pd.Series(fit.model.exog.mean(axis=0), index=fit.params.index)
            x["cap"], x["ysr_num"], x["cap:ysr_num"] = cap, year, cap * year
            means.append(x @ fit.params)
            widths.append(t.ppf(.975, fit.df_resid_inference) * np.sqrt(x @ fit.cov_params() @ x))
        ax.plot(years, means, "o-", color=color, label=label)
        ax.fill_between(years, np.subtract(means, widths), np.add(means, widths), color=color, alpha=.15)
    ax.set(ylim=(0, None), xticks=range(5), xlabel="Years since reset", ylabel="Predicted field spread (%)",
           title="Model B · Field spread at a common mix of race conditions")
    ax.legend(title="Pointwise 95% intervals")
    save(fig, "predicted_field_spread")


def ranking_chart():
    ranks = pd.read_csv(TABLES / "rule_adjusted_ranking.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9, 7), sharex=True, layout="constrained")
    for ax, col, label, color in zip(axes, model.GAPS, LABELS, [BLUE, ORANGE]):
        ordered = ranks.sort_values(col)
        years = [str(y) + ("*" if y == 2026 else "") for y in ordered.season]
        ax.barh(years, ordered[col], color=color)
        ax.axvline(0, color="black", lw=.8)
        ax.set(title=label, xlabel="Mean observed minus predicted gap (pp)")
    fig.suptitle("Rule-adjusted season rankings  ·  *2026 provisional")
    save(fig, "adjusted_rankings")


def round_chart(data):
    reset = data[data.ysr_num == 0]
    current = reset[reset.season == 2026].set_index("round").sort_index()
    past = reset[reset.season < 2026].groupby("round").field_spread.agg(["mean", "count"])
    fig, ax = plt.subplots(figsize=(10, 4.8), layout="constrained")
    ax.plot(past.index, past["mean"].rolling(3, center=True).mean(), "o-", color=BLUE, label="Earlier reset years · round mean")
    ax.plot(current.index, current.field_spread.rolling(3, center=True).mean(), "o-", color=ORANGE, label="2026 · provisional")
    ax.set(ylim=(0, None), ylabel="Field spread (%)", xticks=past.index.union(current.index),
           xlabel="Round (earlier reset seasons at that round in parentheses)\n\nThe same round can take place at different tracks across seasons.",
           title="Exploratory · Qualifying field spread through a reset season\nCentred three-round means · complete windows only")
    ax.set_xticklabels([f"{r}\n({past['count'].get(r, 0)})" for r in ax.get_xticks()])
    ax.legend()
    save(fig, "reset_year_rounds")


def robustness_chart():
    runs = pd.read_csv(TABLES / "robustness.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 6), sharey=True, layout="constrained")
    for ax, term, title, unit in zip(axes, ["beta1", "phi"], ["Year 1 minus reset year (β₁)",
                                    "Cap-era change in cycle slope (φ)"], ["Gap difference (pp)", "Slope difference (pp/year)"]):
        for i, (outcome, label) in enumerate(zip(model.GAPS, LABELS)):
            rows = runs[runs.outcome == outcome]
            ax.errorbar(rows[term], np.arange(len(rows)) + (i - .5) * .24,
                        xerr=[rows[term] - rows[term + "_low"], rows[term + "_high"] - rows[term]],
                        fmt="o", markersize=4, capsize=2, color=[BLUE, ORANGE][i], label=label)
        ax.axvline(0, color="gray", lw=1)
        ax.set(title=title, xlabel=unit, yticks=range(len(rows)), yticklabels=rows.run)
    axes[0].invert_yaxis()
    axes[1].legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False)
    fig.suptitle("Main and sensitivity estimates · season-clustered 95% intervals")
    save(fig, "robustness_intervals")


if __name__ == "__main__":
    CHARTS.mkdir(parents=True, exist_ok=True)
    card = pd.read_csv(TABLES / "season_scorecard.csv")
    data = pd.read_csv(TABLES / "model_data.csv")
    timeline(card, [c + "_best_lap" for c in model.GAPS], LABELS, "Season median qualifying gaps",
             "Gap to fastest lineage (%)", "qualifying_timeline")
    timeline(card, ["win_hhi"], ["Weighted win HHI"], "Season concentration of wins",
             "Win HHI (0–10,000)", "win_hhi")
    model_charts(data)
    ranking_chart()
    round_chart(data)
    robustness_chart()
