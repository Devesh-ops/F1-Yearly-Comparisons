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

## 2026-11-24 · GPT · Jolpica downloader

Added `src/01_download.py`. Offline checks passed for two-page downloads, pre-2021 sprint exclusion, manifest entries, cache reuse, forced refresh, and recovery from HTTP 429 and timeout. Each archive contains the original response pages in request order. Devesh will run `.venv/bin/python src/01_download.py --seasons 2026` for the first live check. Claude can verify the manifest totals against the saved driver rows and API metadata afterward.

## 2026-11-24 · GPT · Download coverage checker

Added src/check_download.py to count unique rounds with driver records, combining split pages, and flag missing qualifying or invalid GP winner counts. Tested on the local 2026 snapshot. Run `.venv/bin/python src/01_download.py` followed by `.venv/bin/python src/check_download.py` for full-period review.

## 2026-11-24 · GPT · Clean driver and race tables

Run `.venv/bin/python src/02_clean.py` to rebuild the four CSVs in data/processed/. DATA_DICTIONARY.md documents the original driver/constructor IDs, points, timing units, and keys. Verified driver counts against manifest.csv for every season and endpoint. Produced 420 races, 8,851 GP results, 8,826 qualifying entries and 612 sprint results. All supplied times parsed, including seconds-only times in 2020 round 16. Missing times remain empty. Ready for Claude's independent review.

## 2026-11-24 · GPT · Constructor lineage inventory and review

Observed seasons by constructor ID in results.csv, before grouping:

- alfa: 2019, 2020, 2021, 2022, 2023
- alphatauri: 2020, 2021, 2022, 2023
- alpine: 2021, 2022, 2023, 2024, 2025, 2026
- aston_martin: 2021, 2022, 2023, 2024, 2025, 2026
- audi: 2026
- bmw_sauber: 2006, 2007, 2008, 2009
- brawn: 2009
- cadillac: 2026
- caterham: 2012, 2013, 2014
- ferrari: 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- force_india: 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018
- haas: 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- honda: 2006, 2007, 2008
- hrt: 2010, 2011, 2012
- lotus_f1: 2012, 2013, 2014, 2015
- lotus_racing: 2010, 2011
- manor: 2015, 2016
- marussia: 2012, 2013, 2014
- mclaren: 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- mercedes: 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- mf1: 2006
- racing_point: 2019, 2020
- rb: 2024, 2025, 2026
- red_bull: 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- renault: 2006, 2007, 2008, 2009, 2010, 2011, 2016, 2017, 2018, 2019, 2020
- sauber: 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2024, 2025
- spyker: 2007
- spyker_mf1: 2006
- super_aguri: 2006, 2007, 2008
- toro_rosso: 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019
- toyota: 2006, 2007, 2008, 2009
- virgin: 2010, 2011
- williams: 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026

Created data/processed/team_lineage.csv. Reviewed coverage against results.csv and names from raw results. Operational continuity determines lineage. All 33 IDs have one match across 16 lineages. Claude should check the midseason Silverstone transitions, separate Lotus teams, and gaps in Renault and Sauber ID usage. Recheck coverage after refreshing 2026.

## 2026-11-24 · GPT · Track layouts

Added the sourced track_layouts.csv and updated src/02_clean.py and DATA_DICTIONARY.md. Rebuild with `.venv/bin/python src/02_clean.py`. Verified all 420 race keys and the before/after boundary of every listed change, including the two Bahrain rounds in 2020 and return to the standard course. Claude should review the medium-confidence inclusions at Sepang, Jeddah and Singapore (2015), where corner geometry changed but the whole-lap impact is less certain.

## 2026-11-24 · GPT · Session weather inventory and Day 1 reproduction

- Created `data/processed/wet_sessions.csv` with 121 unique flags through the 2026 Las Vegas round (61 qualifying sessions and 60 races). Each has an event source. Updated `data/processed/DATA_DICTIONARY.md` with the weather definitions and `README.md` with the commands for the completed steps.
- Research method: use historical wet-event lists to identify candidates, consult qualifying and race accounts independently, and check suspicious qualifying times against reports. Consider reports of local damp patches and drizzle separately from evidence of meaningful wet running. Never infer actual conditions from a forecast. Leave unlisted sessions unknown.
- Reproduce from this checkout with `.venv/bin/python src/check_download.py` then `.venv/bin/python src/02_clean.py`. The weather table is a manual input. Visit each row’s URL to audit the classification. Rebuilding preserved 420 Grands Prix and returned zero download flags and zero timing conversion failures.
- Validated the six weather columns, allowed categories, nonempty HTTPS sources, unique session keys and matching season/round keys in races.csv. Claude can review the 11 uncertain flags first, then look for omitted sessions and independently check whether a qualifying flag applies specifically to Q1 if needed. Coverage is a positive inventory, not an exhaustive dry-session audit.

## 2026-11-24 · Claude · Day 1 review

**Verified (independently recomputed from `data/processed/`):**
- Races per season match the official calendars (2006: 18 ... 2024 and 2025: 24, 2026: 21 so far), 420 total. Every race has exactly one winner.
- Wins per lineage per season match known history on spot checks (e.g. 2006 Ferrari 9, Renault 8, Honda 1; 2016 Mercedes 19 of 21; 2023 Red Bull 21 of 22; 2020 Racing Point and AlphaTauri wins mapped to the right lineages).
- `team_lineage.csv`: all 33 constructor IDs map to 16 lineages and every mapping is correct, including the two separate Lotus teams and the Renault and Sauber ID gaps.
- `wet_sessions.csv`: 35 of 35 well-known wet or mixed sessions I checked are present.
- `track_layouts.csv`: entries and resulting layout IDs look right. Sepang reappears in 2026 for the Bahrain GP held in Malaysia, correctly as sepang_v2.
- Q1 lap times are plausible (fastest Q1 per race between 53.9s at the 2020 Sakhir outer loop and 127.1s at Spa).

**Discrepancies to fix (GPT):**
1. **2025 Miami (round 6): no Q1 times at all** (20 entries, 0 Q1 times). Gap in the API. Fill from FastF1 official timing with the source noted, or exclude that race from qualifying metrics and log it.
2. **`catalunya` 2007 source** points to a 2023 article. Replace with a source about the 2007 chicane.
3. Not committed: none of the Day 1 work (scripts, raw data, processed data) is committed or pushed yet. Only the setup commits exist.

**Handle in Day 2 (not bugs, but must be decided in code):**
4. **2021 Belgium:** no fastest laps (race run behind the safety car, half points). Exclude from race pace metrics. For points, rescoring from finishing positions would give full points, so it needs an explicit rule. Proposal: half weight, like the official result.
5. **2014 Abu Dhabi double points** and the pre-2010 points system: both disappear once points are rescored from positions, as the README says. Raw `points` totals per race range from 19.5 to 202, so the raw column must not be used.
6. **Missing team Q1 times** in 5 races (e.g. 2014 Abu Dhabi, Red Bull excluded from qualifying). Those teams just drop out of that race's qualifying gap. Fine, but note it in the data dictionary.

**README change:** every metric uses the lineage, including within a season (MF1 became Spyker MF1 during 2006).

**Status:** Day 1 is good to go once items 1 to 3 are done.

## 2026-11-25 · Claude · 2025 Miami qualifying times added

- Devesh's PDF of the official F1 results page printed blank (the table loads with JavaScript), so Claude read the same page directly: https://www.formula1.com/en/results/2025/races/1259/miami/qualifying
- Saved all 20 drivers' Q1, Q2 and Q3 times to `data/raw/manual_qualifying_2025_06_miami.csv`, using the same driver and constructor IDs as `qualifying.csv`, with source URL and retrieval date per row.
- **For GPT:** merge this file in `02_clean.py` to fill the empty 2025 round 6 times (don't overwrite any non-empty API value), and note the manual source in `DATA_DICTIONARY.md`. Fixes review item 1.

## 2026-11-24 · GPT · Day 1 review fixes

Updated src/02_clean.py to fill empty 2025 Miami qualifying cells from Claude’s official F1 supplement. Rebuilt data/processed/qualifying.csv with `.venv/bin/python src/02_clean.py`: 45 times added (20 Q1, 15 Q2, 10 Q3), zero conversion failures. Compared every populated raw API segment time with the rebuilt CSV and verified all were preserved. Documented provenance and the five teams without Q1 times at individual rounds in DATA_DICTIONARY.md. Replaced the 2007 Catalunya source in track_layouts.csv with Autosport’s contemporary Spanish GP technical review. Ready for Claude to recheck.
