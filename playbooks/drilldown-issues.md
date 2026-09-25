# Drill-down issues — symptom → cause → fix

Recipes: `skills/metabase-reports/references/drilldowns.md`. The rule behind almost all of these: **one drill card per metric, with the metric's exact condition, dedup and filters. Then verify metric == drill rows.**

| # | Symptom | Root cause | Fix | Seen at |
|---|---|---|---|---|
| D1 | Clicking "Absent" shows **Present** students | Drill pointed to a generic list | Separate Absent and Present drill cards (users on old archived dashboard copies still saw the bug, so redirect them) | Gubbachi |
| D2 | Metric drills to the **whole** class list (54 rows) | Generic line list, no metric condition | Dedicated drill per metric | Gubbachi |
| D3 | Drill shows every form type for a session metric | Record-level all-types list | Per-metric drill, one row per session | Gubbachi |
| D4 | Clicking a program **bar** ignores which bar | No column-source mapping | `source:{type:"column",id:"Program"}` → drill tag | Gubbachi |
| D5 | Drill has **more** rows than the metric | Multi-class students duplicated | `DISTINCT ON (member_subject_id)` in the drill | Gubbachi |
| D6 | Some cards not clickable at all | No click behaviour configured | Build drills for every metric (100% coverage). Document intentional exclusions | Gubbachi |
| D7 | "Metric shows 2 but the drill shows everyone" | Generic drill | Generator: metric carries `drill_cond`, and drill = base + `drill_cond` (105 drills) | Sangwari |
| D8 | Custom-SQL cards got generic drills | Generator couldn't infer the condition | Hand-map the conditions for those cards | Sangwari |
| D9 | New cards not clickable | Created with empty `visualization_settings` | Add `click_behavior` after creation | Sangwari |
| D10 | Clicking one bar opens **all categories** | Drill has no category filter | `[[ and cat = {{category}} ]]` + column-source mapping | Sangwari |
| D11 | ANC drill shows **PNC** data | Two indicators had the same name, and upsert-by-name collided | Name drills `(drill) [KEY] name` | Sangwari |
| D12 | Drill exposed a **metric bug** | Metric used the latest row, not the latest non-null value | Fix the metric (`latest_nonnull_per_entity.sql`) | Sangwari |
| D13 | Distinct-mothers metric < drill rows | Drill is per visit | Expected. Document it on the card | Sangwari |
| D14 | Link-to-question "does nothing / opens the full list" | Build script read `dataset_query.native` (empty in pMBQL), so 0 parameter connections | Read `stages[0]`. Switched to crossfilter there | Door Step School |
| D15 | Aggregate ≠ drill count on NULL categories | NULL gender/donor on one side only | Same `coalesce(x,'(none)')` sentinel in metric **and** drill; `count(distinct)` | Door Step School |
| D16 | Crossfilter click does nothing on **scalars** | Crossfilter unreliable on scalar cards | Use link-to-question for scalars. Test both mechanisms in the browser | Khel Mel |
| D17 | Never-attended child drills to 0 rows | Correct | Document | Khel Mel |
| D18 | A **blank month** bar that can't be drilled | Undated (scheduled) follow-ups | `encounter_date_time is not null` in metric and drill | ANT |
| D19 | Drill values don't match the bar labels | Metric used sentinel CASEs (`(Not collected yet)`, HB band) and the drill didn't | Copy the same CASEs into the drill | ANT |
| D20 | Drill shows 2,000 rows but the metric says 2,357 | Metabase display cap | Expected. Verify with SQL; offer CSV download | ANT, Khel Mel, Goonj |
| D21 | Donut slice not clickable | Category missing from the CASE / no Status→category mapping | Add the category + mapping | Astitva |
| D22 | Enrolment scalars had no drill | Not built | Add `DISTINCT ON` student drills | Gubbachi |
| D23 | Superset: drill-to-detail 404 | Not available on this instance | Cross-filters scoped per chart → line list | Ekam |
| D24 | Drill ignores the dashboard filters | Filters not passed in `parameterMapping` | Pass every dashboard parameter through (`source.type:"parameter"`) | several |
| D25 | Drill errors out | Target was `type:"parameter"` / a dashboard-level id | Target `{type:"variable", id:"<drill tag slug>"}` | Gubbachi |

## The 60-second test for any drill
1. Note the metric value with a filter set (e.g. Block = X).
2. Click it and count the rows (or `select count(*)` the drill SQL with the same params).
3. Equal? ✅ Not equal? Find the difference with `except all` between the metric's base rows and the drill rows.
