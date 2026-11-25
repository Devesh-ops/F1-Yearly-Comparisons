# Decisions and reasoning

Every method choice in this project, why we made it, and what we rejected. Newest decisions are added at the bottom of each section. This file is the source for the write-up's methods section and for explaining the project in interviews.

Format for each entry: **decision**, then *why*, then alternatives considered.

---

## 1. Project design

### 1.1 Compare all 21 seasons, explained by the rule cycle (2026-11-24, Devesh)
**Decision:** Compare every season from 2006 to 2026 with each other, and use where each season sits in the rule cycle (years since the last reset, budget cap) to explain the differences.
*Why:* Uses all the data instead of only reset years. Answers both "which seasons were most competitive" and "how much of that is the rules."
*Alternatives:* Comparing each reset season only with the year before it (Claude's first design). Rejected as the main design because it ignores most seasons; it survives as a special case (years since reset = 0).

### 1.2 Start in 2006 (2026-11-24, Devesh)
**Decision:** Data runs 2006 to 2026. 2005 dropped.
*Why:* 2006 is when knockout qualifying (Q1/Q2/Q3) started, so qualifying is comparable across every season. The all-seasons design doesn't need a "year before" baseline for 2006.

### 1.3 Measure two sides of competitiveness: pace and outcomes (2026-11-25)
**Decision:** Track both pace (how close the cars are in speed) and outcomes (who won and scored).
*Why:* They usually move together but not always. 2023 had one of the tightest midfields in our data while Red Bull won 21 of 22 races. Outcomes are lumpy and affected by luck; pace is measured precisely every race but doesn't say who won. Where they disagree is part of the story.

### 1.4 Day 2 describes, Day 3 explains (2026-11-25)
**Decision:** Day 2 metrics are raw, unadjusted descriptions. Adjusting for tracks and the rule cycle happens in the Day 3 model.
*Why:* Lets a reader see the raw facts first and then what changes once rules and tracks are accounted for.

---

## 2. Pace measures

### 2.1 Gaps in % of the fastest time, not seconds (2026-11-24)
*Why:* A 1-second gap means something different at Monaco (~72s lap) and Spa (~105s). Percent puts every track on one scale.

### 2.2 Use each team's best car, not each driver (2026-11-24)
*Why:* The question is about teams and cars. Taking the team's faster driver also partly smooths out a team having one weaker driver.

### 2.3 Qualifying: compare teams in the last session they both ran (2026-11-25, Devesh and Claude)
**Decision:** Two teams are compared using their best laps in the **last qualifying session both took part in**. In practice: dominance margin (1st vs 2nd team) usually comes from Q3, field spread (fastest vs median team) usually from Q2.
*Why:* Devesh pointed out that the original plan (Q1 only) is flawed: top teams often don't push in Q1, since avoiding elimination matters more than a fast lap. That would make the front look slower than it really is and shrink the dominance margin. Comparing within one session also removes **track evolution** (the track gets faster from Q1 to Q3 as rubber goes down), since both teams ran on the same track at the same time.
*Alternatives:*
- **Q1 only** (original plan): every car runs it, but top teams sandbag. Kept as a robustness check.
- **Each team's best time across Q1 to Q3** (Devesh's first idea): captures full effort, but mixes sessions, so top teams' Q3 laps on a faster track get compared with backmarkers' Q1 laps, and it breaks completely in the refuelling era (2.4). Kept as a robustness check.
*Known caveat:* from 2014 to 2021, top-10 cars had to start the race on the tyres from their best Q2 lap, so some top teams ran Q2 on slower tyres on purpose. That can make the field spread look smaller in those years. Worth checking against the robustness versions.

### 2.4 2006 to 2009: Q3 is never used (2026-11-25)
**Decision:** For 2006 to 2009, the latest comparable session is Q2.
*Why:* In those years Q3 was run with race fuel: cars carried the fuel for their first race stint, so Q3 times are slower than Q2 times and depend on strategy, not just speed.

> **Note for the write-up (Devesh wants to explain this):** explain the refuelling-era Q3 limitation and why the rule existed. Points to cover, to be checked against sources before writing:
> - In-race refuelling was allowed in F1 until the end of 2009 and banned from 2010.
> - Parc fermé rules meant cars had to start the race with the fuel they qualified with, so qualifying fuel load was a strategic choice (light = better grid slot, heavy = longer first stint).
> - Why the FIA designed it that way (mixing up the grid, stopping separate qualifying-only setups) and why it ended (the refuelling ban, cost and safety).
> - What this means for our data: Q3 times in 2006 to 2009 measure fuel strategy as much as speed, so we stop at Q2.

### 2.5 Field spread uses the median team (2026-11-25)
**Decision:** Field spread = gap from the fastest team to the median team.
*Why:* Measuring to the slowest team would let one tiny backmarker (e.g. HRT, often 4 to 5% off in 2010 to 2012) make a whole season look uncompetitive. Example: gaps of 0, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0 and 4.5% give a mean of 1.29% but a median of 1.0%. The median describes the typical team.

### 2.6 Season pace = median across races (2026-11-25)
*Why:* Same logic as 2.5. One chaotic wet race shouldn't define a season. The Day 3 model still uses every race individually, so nothing is thrown away there.

### 2.7 Race pace from each team's fastest race lap (2026-11-24)
*Why:* A race-day check on the qualifying story, and the only lap data available back to 2006 without heavy downloads.
*Caveat:* noisy. From 2019 to 2024 a bonus point for fastest lap gave teams a reason to pit late just to set one.

### 2.8 Wet sessions included (2026-11-24, Devesh)
*Why:* Weather is part of racing. Medians limit the effect of any single wet session, and wet sessions are flagged in `wet_sessions.csv` so we can point out if a result leans on them.

### 2.9 Headline pace measure: not decided yet (2026-11-25, Devesh)
Devesh will choose between dominance margin and field spread after seeing the Day 2 numbers.

---

## 3. Outcome measures

### 3.1 HHI for concentration of wins and points (2026-11-24)
**What it is:** sum of each team's share squared, times 10,000. 10,000 = one team won everything. It's a measurement (like an average), not the statistical method. The statistics come in Day 3. It's the same index competition regulators use to judge market concentration.
*Why:* Captures the whole distribution, not just the top team. Squaring makes concentration count more: one team at 90% weighs far more than three at 30%.
*Examples from our data:* 2023 win HHI is about 9,130 (Red Bull 21 wins, Ferrari 1). 2012 is about 2,750 (McLaren 7, Red Bull 7, Ferrari 3, three teams with 1).
**Effective number of teams** = 10,000 / HHI. 2023 played like a 1.1-team championship, 2012 like a 3.6-team one.

### 3.2 Current FIA points system for every season (2026-11-25, Devesh)
**Decision:** Rescore every season with today's system: 25-18-15-12-10-8-6-4-2-1 for Grand Prix, 8-7-6-5-4-3-2-1 for sprints, no fastest-lap point.
*Why:* The real system kept changing: top 8 only (10-8-6-5-4-3-2-1) before 2010, double points at 2014 Abu Dhabi, a fastest-lap point from 2019 to 2024, sprint points 3-2-1 in 2021. Using each year's actual points would measure changes in the rulebook as changes in competitiveness.

### 3.3 Sessions count in proportion to the points they award (2026-11-25, Devesh)
- **Sprints: 1/3 weight** (about a third of the distance and a third of the points). Sprint qualifying isn't used for pace.
- **2021 Belgium: 1/2 weight** for wins and points (half points awarded after two laps behind the safety car). Excluded from race pace (no real racing laps). Its qualifying stays in because it ran in full.
- Robustness check: sprints at 0 weight.

### 3.4 Reliability: not measured separately for now (2026-11-25, Devesh)
**Decision:** No separate reliability metric for now.
*Why:* A breakdown scores zero points, so an unreliable team's points share drops and that already shows up in points HHI. Pace measures aren't affected by race breakdowns, so a fast but fragile car shows up as a gap between pace dominance and outcome dominance.
*Limitation to remember:* points HHI shows the *effect* of reliability but can't separate it from crashes, strategy or luck. If the write-up needs to explain a specific gap (e.g. 2026 breakdowns), a mechanical DNF rate can be added from the `status` column.
*Revisit:* when deciding how much weight each measure gets in the conclusions.

---

## 4. Teams and tracks

### 4.1 Team lineages (2026-11-24, Devesh)
**Decision:** Renamed or sold teams are linked into one lineage (e.g. Honda to Brawn to Mercedes). Every metric uses the lineage, including within a season.
*Why:* Otherwise one team counts as two, e.g. MF1 became Spyker MF1 partway through 2006.

### 4.2 Track fixed effects in the model (2026-11-24)
*Why:* The calendar changes every year. Comparing each track only with itself stops calendar changes from looking like changes in competitiveness. Redesigned layouts count as new tracks (`track_layouts.csv`). One-off tracks and a core-tracks-only version are robustness checks.

---

## 5. Data fixes

### 5.1 2025 Miami qualifying filled manually (2026-11-25)
The API had no qualifying times for 2025 round 6. All 20 drivers' Q1 to Q3 times were taken from the official F1 results page and saved in `data/raw/manual_qualifying_2025_06_miami.csv`, with source per row. Only empty values are filled.

### 5.2 Teams with no Q1 time drop out of that race's qualifying gap (2026-11-24)
Five team-race cases (e.g. Red Bull at 2014 Abu Dhabi, excluded from qualifying). The race and the other teams stay in.
