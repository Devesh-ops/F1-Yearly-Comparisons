# Project log

Newest entries at the bottom. Each entry: date, who, what was done, files, decisions, what's ready for review or waiting on Devesh.

## 2026-11-24 · Claude · Kickoff and scope

- **Done:** Project picked with Devesh: "Do rule resets break F1 dominance?", with the budget cap as a second question. Scope, metrics, plan and open decisions written in `README.md`.
- **Data check:** `https://api.jolpi.ca/ergast/f1/2026/results/1.json` returned 21 completed 2026 rounds (Australia, 2026-03-08, to Las Vegas, 2026-11-22). Qatar and Abu Dhabi still to come.
- **Note for GPT:** Claude's shell on this machine couldn't reach the API (network allowlist), so downloads should run from Devesh's own Python environment.
- **Waiting on Devesh:** the four open decisions in `README.md`.
- **Next (GPT, Day 1):** `src/01_download.py` and `src/02_clean.py`, raw JSON for 2005 to 2026 in `data/raw/`, clean CSVs in `data/processed/`, data dictionary, then a log entry for review.

## 2026-11-24 · Claude · Decisions recorded, method written

- **Decisions (Devesh):** wet sessions included; start 2006 (2005 kept for race metrics only, as the 2006 baseline); team renames linked into lineages; sprints included at 1/3 weight with a 0-weight robustness check.
- **Method added to `README.md`:** per-race measures (Q1 gap, fastest race lap gap, results), season roll-ups (HHI, effective teams, median gaps), and three comparisons: A (reset vs year before, benchmarked against normal-season changes), B (race-by-race convergence slopes), C (pre- vs post-cap resets). Robustness checks listed.
- **Next (GPT, Day 1):** as in README plan. Also needs the `/sprint` endpoint and the team lineage table.

## 2026-11-24 · Claude · Method redesigned (all seasons compared)

- **Decision (Devesh):** compare all 21 seasons 2006 to 2026 against each other, using the rule cycle to explain the differences. Replaces the reset-vs-year-before design.
- **Changes in `README.md`:** new question and sub-questions (including the year-after-reset response), rule eras table, years-since-reset tags (0, 1, 2, 3+ as categories), race-level regression with track fixed effects and round in season, rule-adjusted ranking from residuals, track handling (layout changes as new track IDs, one-off and core-track checks), time-trend robustness check. 2005 dropped.
- **New manual table needed:** track layout changes (in addition to lineages and wet sessions).
- **Next (GPT, Day 1):** as in README plan.

## 2026-11-24 · GPT · Repository setup

Created the README folder structure with Git placeholders, listed the four Python dependencies in requirements.txt, and extended .gitignore. Raw data is eligible for tracking. The existing main branch already tracks origin/main. Git metadata is read-only in the assistant shell, so staging and committing require the local terminal.
