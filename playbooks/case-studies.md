# Case studies — real Avni orgs, real lessons

IDs are anonymised. Look up the live ones with `tools/mb.py` / `tools/ss.py`. Each case: **ask → what went wrong or was tricky → what fixed it → lesson**.

## Org quick facts (things you can't guess)
| Org | Tool | ETL schema | Gotcha |
|---|---|---|---|
| Durga India | Metabase | `durga_india` | Multi-select topics: use `_coded`; attendance = JSON UUID array on the session encounter; Location = `address."City"` |
| Gubbachi (GLC) | Metabase | **`glc`** (prod) | `gubbachi` schema is the **pilot**; exits void `class_student` links |
| Sangwari | Metabase | `sangwari` (UAT `sangwari_uat`) | Separate prod/UAT DBs; `"WEIGHT"`→`"Weight"` rename broke 6 cards |
| APF Odisha | **Superset** | `apfodisha` | Childline dataset had a dead 1.6M-row CTE; RLS rules per block role |
| JNPCT | **Superset** | `jnpct` | Dataset named `jnpctuat_…` actually reads prod |
| Ekam | Superset (migrated from Metabase) | `ekam` | Hidden `visit_no = 1` dedup behind headline counts |
| JSS | Metabase | `jss` | Stale phulwari concept view dropped districts; big group/permission tree |
| Khel Mel | Metabase | `khelmel` | Attendance in a JSON array; 718 sessions with NULL dates |
| Goonj | Metabase | `goonj` | Two Metabase DBs for one schema; ETL value spellings differ from Salesforce |
| Maitrayana | Metabase | `maitrayanaprod` | Table typo fixed by ETL but columns still misspelled (`attedance`) |
| Shelter | Metabase | `shelter` | One live DB and one stale since June: pick the live one |
| Shramik Bharti | Metabase | `shramikbharti` | New QG table invisible until `sync_schema`; odd concept spelling |
| Mantrana / Animedh | Metabase | **`actdnhuat`** (prod!) | Prod schema has a UAT-looking name |
| ANT | Metabase | `ant` | Many empty new fields; undated follow-ups formed a NULL month |
| Astitva | Metabase | `astitva` | Growth-monitoring `encounter_date_time` NULL on most rows |
| PHRII | Metabase | `phrii` | 1,664-column limit on wide exports; `_view`s empty |
| Calcutta Kids | Metabase | `calcutta_kids` + `public` views | Checklists only in `public`; old jsonb views very slow |
| Door Step School | Metabase | `dssuat` | School is an address level |
| RWB | **Jasper** | `rwb*` per fiscal year | Reports duplicated per level × fiscal year |

## 1. APF Odisha — "Childline list not downloading" (Superset)
- **Ask:** partner users can't download the child line list. It still failed after a permission fix.
- **Wrong turn:** the permission fix (datasource access for 7 roles) was needed but wasn't the cause. The first diagnosis ("add a composite index, escalate to infra") would have been an **unnecessary escalation**.
- **Real cause:** a `row_number()` CTE sorted 1.6M growth-monitoring rows on every load, and **none of its columns were selected**. Load 2–5 min > Superset's 60s.
- **Fix:** deleted the dead CTE. `EXCEPT ALL` = 0 both ways (68,577 rows), 0.8s through Superset.
- **Lesson:** prove a fix before escalating; check for dead CTEs first; permissions and timeouts look identical to users.

## 2. Gubbachi — drills and dropouts
- Drill "Absent" showed Present; metrics drilled to generic lists; dropouts vanished under class filters.
- Fixes: per-metric drills (100% coverage), `DISTINCT ON` membership, dropout metrics ignore the voided link, a materialised concept lookup (41s → 0.7s), and the two-level dropdown recipe (first worked out here).
- **Lesson:** the drill must reuse the metric's exact condition; exits change voided semantics.

## 3. Sangwari — 105 generated drills
- Metric-to-drill generator with `drill_cond`; name collisions (ANC/PNC) fixed with keyed names; drills exposed a latest-row vs latest-non-null metric bug (0/0/1 was really 2/1/14).
- **Lesson:** drills are also a QA tool; generate them, don't hand-build.

## 4. Durga India — multi-select exclusion logic
- Ask: exclude sessions whose topics are only Baseline/Endline/Graduation/Introduction, but include mixed ones.
- Bug: `ILIKE '%Baseline%'` excluded "Baseline, Other" (39 sessions wrong); some topic names contain commas.
- Fix: `_coded` table + `bool_and(answer in (...))`; verified on the client's own example cohort.
- Also: a heavy CTE inlined per row took 103s and slowed all of Metabase; `AS MATERIALIZED` brought it to 1.1s.
- **Lesson:** never string-match multi-selects; materialise heavy CTEs.

## 5. Khel Mel — "Raigarh has 2,000 children but the report shows 173"
- Report was attendance-driven (INNER JOIN), so children who never attended were missing.
- Fix: roster-based LEFT JOIN + Attendance Status filter; date filters moved inside the attendance CTE.
- **Lesson:** agree the grain (roster vs activity) before building.

## 6. JSS — filter dropped a whole district; users locked out of subfolders
- A stale concept-options view was INNER-joined for the Phulwari filter, so Singrauli vanished. Rejoined on the real subject table.
- Group reorg: collection permissions don't inherit into subcollections, so 973 explicit grants were needed. The first dry-run compared `"(none)"` and falsely showed success.
- **Lesson:** validate filters per area; verify permissions as the user.

## 7. Ekam — Metabase → Superset migration
- Native cards became virtual datasets and MBQL aggregates became charts; counts matched only after preserving a hidden `visit_no = 1` dedup.
- Superset needs `query_context` on charts, `override_columns` after SQL changes, and `echarts_timeseries_bar` (not `dist_bar`).
- **Lesson:** migrations must reproduce hidden dedups; verify every count.

## 8. JNPCT — native filters on Superset dashboards
- Added Block/PHC/Sub Centre/Village/Gender/Caste/Age filters by cloning `native_filter_configuration` entries; datasets needed a column resync first. "Screening done" didn't exist in the data, so we said so.

## 9. Shelter — "data not syncing to Metabase"
- Pipeline healthy end to end; an orphan ETL table from a voided form mapping looked stale; the org had a stale second Metabase DB.
- **Lesson:** follow the diagnosis order in `skills/avni-etl-data-model/references/etl-health.md`.

## 10. Goonj — replica of a Salesforce report
- Rebuilt an existing Salesforce report; row-level reconciliation (match / source-only / Avni-only) against the client export; value spellings differed ("Access Infrastructure" vs "Access_Infrastructure").

## 11. Maitrayana — typo rename and donor double-count
- ETL renamed `attedance`→`attendance` in table names but not in columns, so a blanket replace broke queries; donor pie double-counted people in several batches (switched to native SQL + `DISTINCT ON`).

## 12. RWB — Jasper column add (ticket 8420)
- See `skills/jasper-reports` worked example: SQL CTE + total change across 8 JRXMLs; a human uploaded them through the repository editor.
