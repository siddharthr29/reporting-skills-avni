# Metabase drill-downs — making "click the number" show exactly those rows

## Principle
Every clickable number gets its **own drill card**: the base line-list SQL + **that metric's condition** + the same dedup + the same filters. Verify **metric value == drill row count** for every metric and every bar segment.
A shared generic line list is the #1 source of "the drill shows everyone" tickets.

## Generating drill cards (pattern from the Sangwari build)
Keep each metric as `{sql, base, drill_cond}`. `drill_cond` is the numerator condition AND the denominator scope. The drill card is:
```sql
with base as (<same base CTE as the metric>)
select <line-list columns> from base
where <drill_cond>
[[ and "Category" = {{category}} ]]      -- receives the clicked bar value
order by 1
limit 2000
```
Any sentinel the metric uses must appear in the drill too: `coalesce(gender,'(none)')`, `'(Not collected yet)'`, HB bands, `to_char(month)`.

## Option A — link-to-question (works on scalars, bars, tables)
On the metric dashcard, `visualization_settings.click_behavior`:
```json
{"type":"link","linkType":"question","targetId":<DRILL_CARD_ID>,
 "parameterMapping":{
   "<dash_param_id>":{"id":"<dash_param_id>",
       "source":{"type":"parameter","id":"<dash_param_id>","name":"Block"},
       "target":{"type":"variable","id":"block"}},
   "category":{"id":"category",
       "source":{"type":"column","id":"Category","name":"Category"},
       "target":{"type":"variable","id":"category"}}}}
```
- Target type is **`variable`** with the drill card's **tag slug**. `type:"parameter"` or a dashboard-level target makes the drill query error.
- Pass through **every** dashboard filter, or the drill ignores it.
- For a bar chart, map the clicked dimension (`source.type:"column"`).

## Option B — crossfilter (click sets a dashboard filter, and a line list on the same dashboard reacts)
Column-level: `visualization_settings.column_settings["[\"name\",\"Block\"]"].click_behavior = {"type":"crossfilter","parameterMapping":{…}}`.
- The key must be exactly `["name","<col>"]` with **no spaces**: `json.dumps(["name",col], separators=(",",":"))`.
- Attach it to **every** column. One click can set several parameters.
- The line list listens through its normal `parameter_mappings` (`["variable",["template-tag","block"]]`).

## Which one?
The two behaved differently across dashboards on this instance: link-to-question "did nothing" at one org (the root cause was reading `.native` → 0 parameter connections), and crossfilter did nothing on scalars at another. **Build one, click it in the browser, count the rows, then decide.** Don't trust the JSON alone.

## Known, correct "mismatches" (document them on the card)
- Line list > 2,000 rows shows 2,000, but the count is right. Verify with SQL.
- A distinct-people metric < drill visit rows is expected when the drill is per visit.
- A child who never attended drills to 0 rows. That is correct.
- Org-wide cards with no filters may have an empty `parameterMapping` by design.

## Superset equivalent
No native drill-to-detail here (`/datasource/…/samples` returns 404). Use cross-filters scoped per chart. See `skills/superset-reports`.
