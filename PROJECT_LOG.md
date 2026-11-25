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

## 2026-11-25 · Claude · Day 1 fixes verified

- 2025 Miami: all 20 drivers now have Q1 times in `qualifying.csv`, matching the official page (e.g. Verstappen 86.870s, Bearman 87.999s). Q2 and Q3 filled where they exist.
- Catalunya 2007 now cites a contemporary 2007 source.
- `DATA_DICTIONARY.md` documents the manual supplement and the five team-race cases with no Q1 time.
- Day 1 is committed and the local branch is in sync with origin/main.
- **Day 1 closed.** Open items 4 and 5 from the review carry into Day 2.

## 2026-11-25 · Claude · Day 2 method decisions

- Created `DECISIONS.md`: every method decision so far with its reasoning and rejected alternatives. Keep adding to it as decisions are made.
- **Qualifying method changed:** teams compared in the last session they both ran (not Q1 only). 2006 to 2009 Q3 never used (race fuel). Q1-only and best-across-sessions kept as robustness checks.
- **Points:** current FIA system for every season. **Weights:** sprints 1/3, 2021 Belgium 1/2 (excluded from race pace, qualifying kept).
- **Reliability:** no separate metric for now (shows up through points HHI). Revisit later.
- README method sections updated to match.

## 2026-11-25 · Claude · Response to GPT's Day 2 plan

- **Agreed and recorded in `DECISIONS.md`:** 2009 Malaysia at 1/2 weight (pending Devesh's approval), signed gaps, even-number median as the average of the two middle teams' gaps, sprint points not reweighted, "reduces" track evolution (not "removes"), mechanical retirements can affect race pace.
- **Changed:** team order. Not the official order: teams are ordered by the latest *usable* session reached, then time (2006 to 2009 order from Q2, since Q3 was fuel-affected). See DECISIONS 2.10.
- **Claude will hand-check** 2009, 2021 and 2023 (GPT's suggestion) plus 2008 R1 and 2023 R1.

## 2026-11-25 · GPT · Day 2 foundations

Rebuild results.csv and sprint.csv with `.venv/bin/python src/02_clean.py`. Both preserve position_text. Documented eligibility in DECISIONS.md and the data dictionary. src/common.py loads team lineages, defines outcome weights and points eligibility, and produces season_tags(). Grouping numeric position_text by season and round yielded two GPs below ten classified drivers: 2006 R10 (9), 2008 R1 (8). All numeric classification strings agreed with finishing_position. Checked Belgium's 12.5-point win, an 8-point sprint win and zero points for R. Claude can verify these and the six era boundaries. Malaysia 2009 remains an open decision and currently receives the ordinary GP weight.

## 2026-11-25 · Claude · Prompt 1 review

- Recomputed from `results.csv`: only 2006 R10 (USA, 9 classified) and 2008 R1 (Australia, 8 classified) have fewer than 10 classified finishers. Matches GPT. Rescored totals 100 and 98 are right for 9 and 8 scorers.
- Every numeric `position_text` equals `finishing_position`. Disqualifications score zero (e.g. both McLarens at 2025 Las Vegas, position_text D).
- `common.py`: points tables, session weights and season tags checked line by line. Tags match the README eras.
- **Still open:** 2009 Malaysia weight (currently 1, pending Devesh).

## 2026-11-25 · GPT · Per-race qualifying gaps

Run `.venv/bin/python src/03_metrics.py` to regenerate outputs/tables/race_quali_gaps.csv and outputs/tables/team_quali_gaps.csv and print Bahrain 2023 and Australia 2008. Verified 420 race rows, 4,424 eligible team rows, zero leader gaps and all pre-2010 Q3 values excluded. The prompt specifies a numerical median of signed gaps. It differs from taking the middle qualifying ranks at 294 races. Eight team entries tie an earlier-ranked team on the ordering segment and time. The preceding-segment tie convention is documented in DECISIONS.md for Claude to review. Wet flags describe the whole qualifying session and retain source confidence. Malaysia's outcome weight remains pending and does not enter these files.

## 2026-11-25 · Claude · Prompt 2 review: qualifying method changed

- GPT's arithmetic checked and correct (e.g. Ferrari Bahrain 2023: 90.000 / 89.708 = 0.3255%).
- **Method flaw found:** with the last-common-session method, teams knocked out early were compared with the leader's Q1/Q2 laps where it wasn't pushing. Bahrain 2023: Williams 0.18% vs Ferrari 0.33%; field spread 0.70% instead of about 1.29%.
- **Decision (Devesh):** main method is now each lineage's best lap from any session (Q3 excluded 2006 to 2009). Last-common-session kept as a robustness version. Refuelling-era control added to the Day 3 plan. Full write-up in DECISIONS.md 2.12; 2.3 and 2.10 marked superseded.
- **2009 Malaysia:** half weight approved by Devesh (DECISIONS 3.3).

## 2026-11-25 · GPT · Best-lap qualifying rerun

Ran `.venv/bin/python src/03_metrics.py` to rebuild both qualifying tables under decision 2.12. Verified monotonic primary gaps and zero leader gaps across 420 races (4,424 lineage entries). The previous ranks, gaps, spreads and margins reproduce under the last-common columns. Claude can hand-check Bahrain 2023 and Australia 2008 from the script output. Q1-only follows in Prompt 3. Applied decision 3.3 in src/common.py: Malaysia 2009 counts as half a win and awards 12.5 winner points. The weight applies only to outcomes; Malaysia remains eligible for race pace.

## 2026-11-25 · Claude · Prompt 2 rerun verified

- Independently recomputed best-lap field spread and dominance margin for all 420 races from `qualifying.csv`. Dominance margin matches GPT exactly in every race. Field spread matches in 419 of 420.
- The one difference (2024 R15, Netherlands) is intended: Williams is excluded because Albon's Q1 time is missing (qualifying deleted), even though the API still holds his Q2 and Q3 times. Recorded in DECISIONS 5.2.
- Bahrain 2023 matches the hand calculation: field spread 1.286%, dominance margin 0.326%. Ready for Prompt 3.

## 2026-11-25 · GPT · Q1-only qualifying and race pace

Ran `.venv/bin/python src/03_metrics.py` to update [qualifying](outputs/tables/race_quali_gaps.csv) and generate [race pace](outputs/tables/race_pace_gaps.csv) under decisions 2.7, 2.12 and 3.3. Independently recomputed both spreads and margins from sorted lineage lap times for all 420 qualifying sessions and 419 races. Belgium 2021 contributes only to qualifying. Malaysia 2009 contributes to both. Claude can review the [printed comparisons](outputs/tables/pace_comparison.txt): Pearson correlations use 419 common races, and the top five absolute qualifying differences use all 420. Brazil 2010 has the largest difference (3.803 percentage points).

## 2026-11-25 · Claude · Prompt 3 review

- **All five races where best-lap and Q1-only disagree most are wet or mixed qualifying sessions** (all flagged high confidence in `wet_sessions.csv`): Brazil 2010, Belgium 2023, Malaysia 2010, Hungary 2016, Australia 2013. When the track dries or gets wetter between Q1 and Q3, best laps from different sessions aren't comparable. The method behaves well in dry sessions; weather is its weak spot.
- **Race pace (fastest race lap) is a weak measure at race level:** r = 0.32 with best-lap field spread, 0.10 for dominance margin. Expected, since fastest race laps depend on tyre age, fuel load, traffic and (2019 to 2024) the fastest-lap point. Treat it as supporting evidence only; check again at season level, where noise averages out.
- Best lap correlates most with race pace of the three qualifying methods, a small extra point in its favour.
- **Proposed for Devesh:** keep wet sessions in (his decision), but add a wet-qualifying control in the Day 3 model and a robustness run without wet qualifying. Season-level race pace correlation added to Prompt 5.

## 2026-11-25 · GPT · Weekend outcomes and season scorecard

Run `.venv/bin/python src/03_metrics.py` and `.venv/bin/python src/04_scorecard.py`. Review [weekend outcomes](outputs/tables/race_outcomes.csv), [season scorecard](outputs/tables/season_scorecard.csv), [points and win checks](outputs/tables/outcome_checks.txt) and [full printout](outputs/tables/season_scorecard_printout.txt). Verified unique weekend-lineage keys and all 21 weighted win totals against GP and sprint counts, including half-weight Malaysia and Belgium. Claude can check the 2012 HHI of 2,750 and the 2023 weighted HHI of 8,939.04 against the GP-only benchmark of 9,132.23. Best-lap versus race-pace median correlations are 0.580637 for spread and 0.214409 for margin.

## 2026-11-25 · Claude · Prompts 4 and 5 review

- **Independently recomputed** win HHI and points HHI for all 21 seasons from `results.csv` and `sprint.csv` (current FIA points, classified finishers only, sprints 1/3 for wins, Belgium 2021 and Malaysia 2009 at 1/2): match GPT to rounding in every season. Season medians of best-lap field spread and dominance margin also match exactly.
- 2023 win HHI 8,939 is right. Claude's earlier ~9,130 was Grand Prix wins only; sprints (Red Bull 5 of 6, McLaren 1) bring it down slightly.
- Season-level correlation between qualifying and race pace: 0.58 field spread, 0.21 dominance margin. Race pace agrees reasonably on the midfield, not on the gap at the front.
- **Things to flag for Devesh (first look, not conclusions):**
  1. Points HHI has a narrow range (about 1,600 to 2,300) because points go 10 deep and each team has two cars, so even 2023 only scores 2,074. It separates seasons much less than win HHI. Worth deciding whether it earns a place in the conclusions.
  2. 2009 to 2010 field spread jumps from 0.60% to 1.48%. 2010 isn't a reset, but it's when Q3 comes back into our measure and three new backmarker teams arrived. This is the measurement effect the refuelling-era control is meant to absorb.
  3. 2023: Red Bull won 21 of 22 but its qualifying dominance margin was only 0.19%. Its edge was on race day, not one-lap pace.

## 2026-11-25 · GPT · Day 2 wrap-up

- Built the classification-aware cleaner, [shared helpers](src/common.py), [weekend metrics](src/03_metrics.py) and [season scorecard](src/04_scorecard.py). The [tables folder](outputs/tables/) contains five analysis CSVs and three review printouts. [README](README.md#how-to-reproduce) now covers the run order and printout commands. [DECISIONS 2.13](DECISIONS.md) records exact ties, missing laps and comparison samples.
- To reproduce from the snapshot, activate the environment and run `python src/02_clean.py`, `python src/03_metrics.py`, then `python src/04_scorecard.py`. For this wrap-up, reran both Day 2 scripts from the processed inputs and verified all eight output files matched their previous checksums.
- Claude has verified both HHIs and the main qualifying season medians across all 21 seasons. Ready for final review: starter and distinct-winner counts, wet/mixed session counts, the tie and missing-time conventions, and the README commands.
- Open for Devesh before Day 3: Claude proposed a wet-qualifying control and a sensitivity run excluding flagged sessions. Unflagged weather is unknown. The 2026 snapshot ends at round 21, and the interpretation of the 2009–10 change remains uncertain because the qualifying measurement and team field both changed.
