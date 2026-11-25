# F1 data dictionary

The four UTF-8 CSV files come from the saved Jolpica pages in `data/raw/`. The raw manifest gives retrieval dates. Join tables on `season` and `round`, adding `driver` for driver-level comparisons. The 2026 snapshot ends at the latest downloaded Grand Prix.

| File | One row represents | Unique key |
|---|---|---|
| races.csv | One Grand Prix in the results archive | season, round |
| results.csv | One driver's Grand Prix result | season, round, driver |
| qualifying.csv | One driver's entry in the qualifying archive | season, round, driver |
| sprint.csv | One driver's sprint result | season, round, driver |

| Column | Files | Meaning | Units or format |
|---|---|---|---|
| season | All | Championship season | Calendar year |
| round | All | Grand Prix weekend number within the season, shared by sessions | Integer starting at 1 |
| race_name | races | Grand Prix name from Jolpica | Text |
| date | races | Grand Prix date | YYYY-MM-DD |
| circuit_id | races | Jolpica circuit identifier. Layout changes can share an ID. | Identifier |
| circuit_name | races | Circuit name supplied for the event | Text |
| driver | results, qualifying, sprint | Jolpica driverId | Identifier |
| constructor | results, qualifying, sprint | Original Jolpica constructorId for this entry, before lineage mapping | Identifier |
| grid | results, sprint | Starting grid position as recorded, including any source value of 0 | Grid slot |
| position_text | results, sprint | Original Jolpica positionText. A numeric string denotes a classified position eligible for rescoring. Letter codes receive zero points. | Text |
| finishing_position | results, sprint | Numeric result order from position. Read with status for retirements or other outcomes. | Rank, 1 = winner |
| status | results, sprint | Outcome reported by Jolpica, such as Finished or a retirement reason | Text |
| points | results, sprint | Points awarded to the driver as supplied in the original result | Championship points, can be fractional |
| fastest_lap_seconds | results, sprint | Driver's fastest recorded lap in that GP or sprint | Seconds |
| q1_seconds | qualifying | Driver's reported Q1 lap time | Seconds |
| q2_seconds | qualifying | Driver's reported Q2 lap time | Seconds |
| q3_seconds | qualifying | Driver's reported Q3 lap time | Seconds |

Lap times preserve source precision. For example, 1:23.456 becomes 83.456 seconds. An empty timing cell means the source omitted a time, supplied a blank, or supplied an unparseable value. The cleaner prints unparseable values with the source file, round, driver, and field. A driver can have a result without a qualifying entry.

## team_lineage.csv

One row per constructor ID observed in results.csv. Join driver tables by matching constructor to constructor_id.

| Column | Meaning |
|---|---|
| constructor_id | Original Jolpica identifier |
| constructor_name | Jolpica constructor display name in the latest observed results archive |
| lineage | Latest team name in the sample for the same racing operation, including documented changes of ownership |
| first_season | Earliest season with this ID in results.csv |
| last_season | Latest season with this ID in results.csv. Intervening years may have another ID. |
| source | Reference URL supporting the assignment. Multiple references are separated by a vertical bar. |
| certainty | Certain means the assignment is supported under the operational definition. Uncertain would identify an unresolved link for review. |

Force India and its 2018 successor share a lineage under the operational definition despite the FIA accepting a new entrant. Use the original IDs and official standings for questions about championship entry identity. Exact observed seasons per ID are listed in PROJECT_LOG.md.

## Circuit layouts

The track_layout_id column in races.csv identifies the physical GP configuration for circuit comparisons. The first observed configuration is circuit_id followed by _v1. Permanent changes increment the version in the first affected race. Bahrain uses v1 for the standard course, v2 for the 2010 endurance course, and v3 only for the 2020 Sakhir GP. Reuse of the standard course restores v1.

track_layouts.csv records material changes between observed F1 configurations. circuit_id matches races.csv. change_season is the first affected F1 season in this sample, which can follow the construction year. description explains the route change or reversion. source is the supporting URL. confidence is high for clear changes to the timed route and medium for documented reprofiling whose whole-lap importance is less certain. Resurfacing, kerb, barrier, pit-building and DRS changes alone do not qualify. The table does not estimate seconds gained or lost.

## wet_sessions.csv

Manual session-level weather flags through 2026 round 21. Join on season and round and select the matching session before joining to a driver table. An unlisted session has no documented flag in this inventory and its condition remains unknown. A qualifying flag can arise during any of Q1–Q3 and does not establish that Q1 itself was wet.

| Column | Meaning |
|---|---|
| season | Championship year |
| round | Grand Prix weekend number in races.csv |
| session | qualifying follows the main qualifying archive. race means the Grand Prix. Sprint races and separate sprint qualifying are excluded. |
| condition | wet means the session was predominantly run in wet-track conditions. mixed means appreciable dry and damp/wet running, including distinct wet sections of an otherwise dry circuit. Switching between full wets and intermediates alone still counts as wet. |
| source | Public URL reporting conditions for the indicated event and session |
| confidence | high indicates direct session evidence for the classification. uncertain indicates a borderline shower, ambiguous effect on running, or unclear wet/dry split. Keep uncertain rows separate in sensitivity checks. |

### Miami 2025 qualifying and Q1 gap coverage

For 2025 round 6, the cleaner matches the 20 existing driver rows to `data/raw/manual_qualifying_2025_06_miami.csv` by season, round and driver, checks constructor identity, and fills only missing segment times. Populated API times take precedence. The supplement records the source URL and retrieval date per driver. [Official F1 qualifying results](https://www.formula1.com/en/results/2025/races/1259/miami/qualifying)

A team's best valid Q1 time counts even if only one driver recorded a time. A team with no valid Q1 time drops out of that race's qualifying gap calculation. The other teams and the race remain eligible. The current snapshot has five such team-race cases: Ferrari (2006 round 7), HRT (2011 round 6), Red Bull (2014 round 19), and Williams (2024 round 15 and 2025 round 18).
