# How do rule resets shape F1 dominance? Every season from 2006 to 2026

*Status: Day 2 complete through the season scorecard. Kickoff 2026-11-24. See `PROJECT_LOG.md` for progress, `DECISIONS.md` for the reasoning behind every method choice, and `AGENTS.md` for how we work.*

## The question

**Main question:** Comparing every F1 season from 2006 to 2026, how much of the difference in competitiveness between years is explained by where each season sits in the rule cycle?

**Sub-questions:**
1. How competitive is a reset year, and how much tighter does the field get each year after?
2. How does F1 respond in the year right after a reset: does the new leader's dominance grow, hold, or get competed away?
3. Did the 2021 budget cap make the field catch up faster?
4. Once the rule cycle is accounted for, which seasons were unusually dominant or unusually close?

## Why it matters

A big rule change is a regulator resetting a market. Every team starts again on a new design, and the open question is whether that levels the field or hands dominance to whoever reads the new rules best, and how long that edge lasts. This is the same question economists ask about regulation and market power, applied to a sport with very clean data.

How it maps to target roles:

- **Economic / litigation consulting:** a panel regression that separates the effect of policy (rule resets, the budget cap) from other differences between years, using HHI, the concentration measure regulators use in merger reviews.
- **Strategy consulting:** how long a first-mover advantage lasts after a market reset, and when a challenger should go all in.
- **Quant:** testable hypotheses, a model with a clear baseline, and a "vs expected" ranking from model residuals.
- **Business analyst:** clearly defined metrics, what drives them, and a recommendation.

**Decision it informs:** for a team (or the FIA), how big an edge a reset creates and how long it lasts, which tells you how much to prioritize early development on the new rules.

## Hypotheses

- **H1:** The field is most spread out in reset years and tightens each year into a rule cycle.
- **H2:** The year after a reset is when teams respond: dominance shrinks as rivals copy the leader's concept.
- **H3:** Tightening is faster with the budget cap (2021 on) than without it.

## The rule eras

| Era | Seasons | Reset year changes |
|---|---|---|
| V8 | 2006 to 2008 | 2.4L V8 engines replace V10s |
| Aero overhaul | 2009 to 2013 | New aero rules, slick tyres return, KERS |
| Early hybrid | 2014 to 2016 | 1.6L V6 turbo hybrid power units |
| Wide cars | 2017 to 2021 | Wider cars and tyres, more downforce |
| Ground effect | 2022 to 2025 | Ground effect aero, 18-inch wheels |
| 2026 rules | 2026 | New power units with a much bigger electric share, sustainable fuel, active aero, smaller and lighter cars |

The budget cap starts in 2021, the last year of the wide-car era. That's useful: it means the cap and the 2022 reset don't start in the same year, so the model can tell them apart a bit.

## Method

### Step 1. Measure every race weekend the same way

Each race weekend produces three numbers per team. All gaps are in **% of the fastest time**, not seconds, so short and long tracks are comparable.

1. **Qualifying gap:** each team's **best lap from any qualifying session** vs the best team's best lap, in %. Every team is measured at its best effort, the leader included, so early-round sandbagging by top teams doesn't distort the gaps. **2006 to 2009: Q3 is never used**, because it was run with race fuel in the refuelling era. Full reasoning, including an earlier method that failed, in `DECISIONS.md` (2.12).
2. **Race pace gap:** each team's fastest lap in the race, from the results data.
3. **Results:** who won, and points under one fixed points system (below).

From these, every weekend gets:
- **Field spread:** gap from the fastest team to the median team. How bunched up is the grid?
- **Dominance margin:** gap from the fastest team to the second-fastest. How far ahead is the leader?

### Step 2. A scorecard for every season

All 21 seasons get the same scorecard:
- **Win HHI (constructors):** sum of each team's share of wins squared, times 10,000. 10,000 means one team won everything.
- **Points HHI:** same idea on points shares, to capture depth below the winner.
- **Effective number of teams:** 10,000 / HHI ("this season played like a 1.8-team championship"), shown next to the actual number of teams.
- **Distinct winners:** different winning teams and drivers.
- **Season pace gaps:** the **median** across races of field spread and dominance margin.

Output: one timeline of all 21 seasons with resets marked, and a straight ranking from most to least competitive.

### Step 3. Tag every season with its place in the rule cycle

- **Era** (table above).
- **Years since reset:** 0 in a reset year, then 1, 2, 3+. These are treated as separate categories, not a straight line, so the model shows each step on its own. The step from 0 to 1 is the "year after" response in sub-question 2.
- **Budget cap:** yes from 2021.

### Step 4. Explain the differences between seasons (the core model)

A race-level regression, one row per race (about 420 races):

> field spread = years since reset (0, 1, 2, 3+) + budget cap + cap × years since reset + track + round in season

What each piece tells us:
- **Years since reset:** how much tighter the field gets in each year of a rule cycle, averaged over every cycle. Answers sub-questions 1 and 2.
- **Cap × years since reset:** whether the cap changed that pattern. Answers sub-question 3.
- **Track:** each track is compared with itself (see "Tracks" below).
- **Round in season:** race-by-race tightening within a season. We also let this slope differ in reset years, which compares how 2026 developed race by race with earlier first years.

The same model is run for dominance margin. The season-level scorecard (HHI etc.) only has 21 data points, so those get simple charts by years since reset and at most a two or three variable regression.

### Step 5. Rule-adjusted ranking

The model gives an "expected" competitiveness for each season based on its place in the rule cycle. The difference between what actually happened and what was expected (the residual) gives a second ranking: which seasons were far more dominant, or far closer, than their position in the rule cycle predicts.

### Tracks

The calendar changes a lot: tracks come and go (Korea, India, Portimao, Las Vegas), and some get redesigned (Barcelona's final chicane removed in 2023, Abu Dhabi and Melbourne reworked in 2021 and 2022). How we handle it:

1. **Gaps in %, not seconds.** Takes care of track length.
2. **Track fixed effects.** Every track gets its own baseline, so a race is only ever compared with other races at the same place. If Monaco always has a wide spread, a wide spread at Monaco isn't read as a dominant season. Season comparisons then come only from the *change* at each track.
3. **Redesigned layouts count as new tracks.** A short manual table (in `data/processed/`) lists major layout changes, and the race after the change gets a new track ID.
4. **One-off tracks** (raced in only 1 or 2 seasons) barely inform the comparison, since there's nothing to compare them with. They stay in the main model, and get dropped in a robustness check.
5. **Core-tracks check:** rerun using only tracks raced in most seasons (e.g. Monza, Silverstone, Spa, Hungaroring, Suzuka, Montreal, Interlagos). If the answer holds there, track changes aren't driving it.

### Sprint races and shortened races

Rule: **a session counts in proportion to the points it awarded.**

Sprints count at **1/3 weight**: a sprint is about a third of a Grand Prix distance and offers about a third of the points (8 for a win vs 25).

**2021 Belgium counts at 1/2 weight** for wins and points, since half points were awarded after two laps behind the safety car. It's left out of race pace (no real racing laps), but its qualifying stays in because that ran in full. **2009 Malaysia also counts at 1/2 weight** (stopped in rain, half points awarded; approved by Devesh), but stays in race pace since its laps were real racing. Sprint points come straight from the sprint table and aren't weighted again.
- A sprint win counts as 1/3 of a win in win HHI.
- In points HHI, sprints are rescored on 8-7-6-5-4-3-2-1 for every season, including 2021 when the real system was 3-2-1.
- Sprint qualifying isn't used for the qualifying gap, so that metric means the same in 2006 and 2026.

### Fixed points system

Every season is rescored with the **current FIA system**: 25-18-15-12-10-8-6-4-2-1 for Grand Prix, 8-7-6-5-4-3-2-1 for sprints, no fastest-lap point. The real system changed over time (top 8 only before 2010, double points at 2014 Abu Dhabi, a fastest-lap point 2019 to 2024), so using actual points would measure changes in the rulebook instead of changes in the racing. Raw `points` from the API are never used.

### Wet sessions

Included. They spread the field and add noise, which is why season gaps use medians. Wet sessions get flagged so we can point out if a result leans on them.

### Robustness checks

- Sprints at 0 weight vs 1/3.
- Without one-off tracks, and core tracks only.
- With a simple time trend added. F1 may have gotten tighter over time for reasons other than rules (reliability, simulation tools), and this checks that the rule-cycle effect isn't just that trend.
- Qualifying gap vs race pace gap: if both tell the same story, the finding is solid.
- Qualifying method: best lap from any session (main) vs Q1 only vs last common session.
- Day 3 model includes a refuelling-era qualifying control (2006 to 2009), since Q3 isn't used in those years.

## Data

- **Source:** [Jolpica F1 API](https://api.jolpi.ca/ergast/f1/), the free, community-maintained successor to the Ergast API. No key needed. Endpoints: `/{season}/results` (includes each driver's fastest race lap and the circuit ID), `/{season}/qualifying`, `/{season}/sprint`.
- **Optional:** FastF1 (Python library) wraps the same API with caching.
- **Coverage:** 2006 to 2026 (21 seasons).
- **Check on 2026-11-24:** the 2026 results endpoint returns 21 completed rounds (Australia to Las Vegas). Qatar and Abu Dhabi are still to come, so everything gets rerun after the final round.
- **Manual tables** (built by us, sources noted in each): team lineages, wet sessions, track layout changes.
- **Rule:** raw API responses are saved untouched in `data/raw/` with the retrieval date. Nothing in there gets edited.

## Decisions made (2026-11-24, Devesh)

- **Design:** compare all 21 seasons, using the rule cycle to explain the differences (replaces the earlier "each reset vs the year before" design, which is now just the years-since-reset = 0 case).
- **Start year:** 2006. 2005 dropped, since the model no longer needs a year-before baseline.
- **Wet sessions:** included.
- **Team renames:** linked into lineages (e.g. BAR to Honda to Brawn to Mercedes; Minardi to Toro Rosso to AlphaTauri to RB/Racing Bulls; Jordan to Midland to Spyker to Force India to Racing Point to Aston Martin). Every metric uses the lineage, including within a season, since MF1 became Spyker MF1 partway through 2006 and would otherwise count as two teams.
- **Sprints:** included at 1/3 weight, with a 0-weight robustness check.

## Plan (about 24 hours)

| Day | Work | Claude checks |
|---|---|---|
| 1 | Download results, qualifying and sprints (2006 to 2026) to `data/raw/`, flatten into clean CSVs, build the three manual tables (lineages, wet sessions, layout changes), write a short data dictionary | Race counts per season, every race has a winner, Q1 and fastest-lap times parse, manual tables right, spot-check against official records |
| 2 | Per-race metrics, season scorecards, rule-cycle tags, saved to `outputs/tables/` | Recompute HHI and gaps independently for 2 to 3 seasons, tags correct |
| 3 | Core regression, rule-adjusted ranking, robustness checks, charts. Devesh picks the headline finding | Model specified as written, results reproduce, charts match tables, nothing cherry-picked |
| 4 | Write-up, GitHub repo, resume bullet | Every number in the report traces to a saved output |
| 5 to 7 | Buffer. Rerun everything after Abu Dhabi | Final numbers updated everywhere |

## Folder structure

```
Quantitative/
  AGENTS.md          how the AIs and Devesh work together
  README.md          this file
  PROJECT_LOG.md     dated progress notes, decisions, review findings
  DECISIONS.md       every method decision and the reasoning behind it
  data/raw/          untouched API responses
  data/processed/    clean CSVs and the three manual tables
  src/               01_download.py, 02_clean.py, 03_metrics.py, 04_model.py, 05_charts.py
  outputs/tables/
  outputs/charts/
  report/            the 2 to 4 page write-up
```

## How to reproduce

From the repository root, set up Python once:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The repository includes the raw API pages (`data/raw/`) and the hand-built tables (`data/processed/team_lineage.csv`, `track_layouts.csv`, `wet_sessions.csv`), so everything can be rebuilt without downloading. Run from the repository root:

```bash
python src/02_clean.py        # raw pages -> races, results, qualifying, sprint CSVs, plus a per-season check
python src/03_metrics.py      # per-race qualifying gaps, race pace gaps and outcomes -> outputs/tables/
python src/04_scorecard.py > outputs/tables/season_scorecard_printout.txt   # one row per season -> season_scorecard.csv
python src/review_checks.py   # optional: correlation and points check printouts
```

To refresh data (e.g. after the last race of 2026), download first: `python src/01_download.py --seasons 2026 --force`. Without `--force` it skips files already saved. Then rerun the steps above. Gaps in the API can be filled with a `data/raw/manual_qualifying_<season>_<round>_<race>.csv` file (same columns as the Miami 2025 one); the cleaner picks it up automatically and only fills empty times. Check the weather of any new rounds by hand in `wet_sessions.csv`.

## Known limitations

- Six rule cycles, one of them only one season long. The race-level model has plenty of rows, but the cycle-level conclusions rest on a handful of cycles.
- Resets aren't random. Rules sometimes change partly *because* one team is dominating, so a reset isn't a clean experiment.
- The cap overlaps with the start of the ground effect era (one year apart), so the cap effect is the least certain result.
- Pace gaps mix car and driver. A dominant driver can make a car look better than it is.
- Fastest race lap is noisy. From 2019 to 2024 a bonus point for fastest lap gave teams a reason to pit late just to set one.
- Other changes happened around some resets (refuelling ban in 2010, tyre supplier changes, testing limits).

## Resume bullet (draft, numbers to come)

> Built a Python panel regression on 21 seasons and ~420 F1 races (2006 to 2026) to separate the effect of regulation resets and the budget cap on competitive balance, controlling for track; found [verified result].
