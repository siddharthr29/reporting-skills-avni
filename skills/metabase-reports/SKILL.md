---
name: metabase-reports
description: Build, change and debug Avni reports in Metabase (reporting.avniproject.org) via the REST API — native SQL cards, template tags, searchable dropdown filters, drill-downs (link-to-question and crossfilter), dashboards, collections and permissions. Use for any Metabase card/dashboard work.
---

# Metabase for Avni

**Instance:** `https://reporting.avniproject.org`. Auth header `x-api-key: $METABASE_API_KEY`. Client: `tools/mb.py`.
Each org usually has a Metabase database pointing at the shared read DB, with SQL schema-qualified to the org schema.
An org can have **several** Metabase DBs for the same schema (live vs stale), so find the live one first (`mb.py dbs <schema>`).
Schema names can mislead, e.g. Gubbachi's prod schema is `glc` (`gubbachi` is the pilot) and Animedh's prod is `actdnhuat`.

## The 8 rules that prevent most Metabase bugs

1. **Read the card in the new shape.** `GET /api/card/<id>` returns pMBQL: SQL at `dataset_query.stages[0].native`, tags at `stages[0]["template-tags"]`. Reading `dataset_query.native` gives `KeyError` or empty, which later shows up as "0 parameter connections" and a "drill shows the full list" bug. For PUT, send the legacy shape `{type:"native", database:<DB_ID>, native:{query, "template-tags"}}`. `mb.py` does both conversions.
2. **Patch in place, and reuse tags.** On any SQL change, keep the existing `template-tags` (same `id`s) and `parameters[]` verbatim. Regenerated tag UUIDs break dashboard filter wiring. Never delete and recreate a card or dashboard.
3. **Dashboard PUTs must carry `tabs`** or the tabs are deleted. New dashcards need **distinct negative ids** (-1, -2, …).
4. **Dropdowns need two levels.** See `references/filters.md`. Without `values_query_type:"list"` at *both* the dashboard parameter and the card (tag **and** `parameters[]`), the widget is a free-text box.
5. **Drills: one drill card per metric.** The drill list reuses the metric's exact WHERE and dedup, so "metric shows 2" gives "drill shows those 2". See `references/drilldowns.md`.
6. **Metabase caches the schema.** Column in Postgres but not in the field picker or filters? `POST /api/database/<DB_ID>/sync_schema`, then `rescan_values` for dropdown values. `is_full_sync=false` DBs never discover new tables on their own.
7. **Validate through Metabase, not only psql.** `POST /api/dataset` (or `/api/card/<id>/query`) on the Metabase DB. The replica and Metabase's DB can differ, and so can caching.
8. **Name drills uniquely.** `(drill) [KEY] <name>`. Upsert-by-name once served PNC data under an ANC drill because two indicators shared a name.

## Card SQL shape

```sql
with base as (                       -- ONE base: joins + voided + ALL filters
  select e.id, i.id as person_id, a."District", a."Block", e.encounter_date_time::date as d
  from <schema>.<encounter_table> e
  join <schema>.individual i on i.id = e.individual_id and i.is_voided = false
  join <schema>.address a   on a.id = i.address_id    and a.is_voided = false
  where e.is_voided = false and e.encounter_date_time is not null
  [[ and a."District" = {{district}} ]]
  [[ and a."Block"    = {{block}} ]]
  [[ and e.encounter_date_time >= {{start_date}} ]]
  [[ and e.encounter_date_time <  {{end_date}} + 1 ]]
)
select count(distinct person_id) as "Children visited" from base
```
- `[[ … ]]` = optional filter. It must contain a `{{var}}`, and OR/paren logic inside it fails ("must contain at least one {{}}"), so put that logic in the CTE.
- To validate locally, strip optional blocks with `re.sub(r"\[\[.*?\]\]", "", sql, flags=re.S)` (the `re.S` matters for multi-line blocks).
- Prefer **plain variables** (`text`/`date`) over field filters. Field filters depend on field ids, break on table aliases, and can't reach schemas Metabase hasn't registered.
- Percent cards: output `numerator, denominator, pct, target`, with `round(100.0*num/nullif(den,0),1)`.
- Line lists: `LIMIT 2000` (the display cap). For time series, `ORDER BY d DESC LIMIT 2000` and re-sort ascending, so the newest rows aren't cut.

## Visualisation gotchas
- Bar and pie POSTs need `graph.dimensions/metrics` or `pie.dimension/metric`, or you get a 400.
- `pie.slice_threshold: 0`. The default groups small slices into "Other", which collides with a real "Other" answer.
- `POST /api/card` rejects `description:""`, so send `null`.
- Links in a table column: `column_settings` `view_as:"link"`, `link_url:"{{value}}"`, or build the URL in SQL.
- Days with zero rows vanish from trends. Use `generate_series` (`sql/patterns/generate_series_trend.sql`).
- Add a "What these metrics mean" text card, and card descriptions that state denominators and caveats.

## Native vs MBQL
- Pivot or aggregate cards often use MBQL on top of a native base card (`source-table: "card__<BASE_ID>"`). Fixing the base fixes them all.
- Native cards don't auto-drill. If you need click-through on a GUI question, build it on a **Model**.
- When MBQL can't dedup (e.g. membership double-count), convert that card to native SQL with `DISTINCT ON`.

## Collections & permissions
Layout: `<Org> → Reports → {Dashboards, Report Cards}`. **Permissions don't inherit into subcollections.** Grant each one (`PUT /api/collection/graph`). Details and the stale `/api/user/<id>` trap are in `references/permissions.md`.

## References
- `references/api.md` — endpoints, payload shapes, revision recovery, CSV export beyond 2,000 rows.
- `references/filters.md` — the dropdown recipe, period quick-filter, multi-select filters.
- `references/drilldowns.md` — link-to-question and crossfilter JSON, the per-metric drill generator.
- `references/permissions.md` — groups, collection graph, verifying access.
