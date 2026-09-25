---
name: superset-reports
description: Build, change and debug Avni reports in Superset (reporting-superset.avniproject.org) via the REST API — virtual datasets, charts with query_context, dashboards, native filters, cross-filter drill-downs, RLS and the 60s timeout. Use for any Superset dataset/chart/dashboard work.
---

# Superset for Avni

**Instance:** `https://reporting-superset.avniproject.org` (API only, no MCP). Client: `tools/ss.py`.
Every Superset DB connection points at the same shared read DB and can see every org schema. The org is chosen by the **schema in the SQL**.
Names mislead: a dataset called `<org>uat_…` may really read the prod schema. Read the SQL, not the name.

## Auth (must be exact)
1. `POST /api/v1/security/login {"username","password","provider":"db","refresh":true}` → `access_token`
2. `GET /api/v1/security/csrf_token/` **with a cookie jar** → `X-CSRFToken` header on every PUT/POST/DELETE (plus `Referer: <base>/`).

## The 9 rules

1. **Datasets are virtual SQL.** `POST /api/v1/dataset/ {database, schema, table_name, sql}`. Superset wraps them as `SELECT … FROM (<your sql>) AS virtual_table WHERE <filters/RLS>`, so **Postgres computes your whole inner query first**. A slow inner query is slow for every user, however small their slice.
2. **Changing dataset SQL doesn't refresh its columns.** Stale columns cause `column "X__1" does not exist`. When the output columns change, re-sync them after the SQL PUT: `PUT /api/v1/dataset/<id>/refresh` (or `PUT …?override_columns=true` with an explicit `columns[]`). `ss.py set-dataset-sql --override-columns` does the refresh. If you keep the SELECT list byte-identical, a plain `{"sql": …}` PUT is enough and the columns survive.
3. **No duplicate output names.** Two `"PHC name"` columns become `__1` errors. Alias one.
4. **Schema-qualify `public.*`.** The dataset's search path doesn't include `public` the way Metabase's does.
5. **Charts need `query_context`.** Without it, `/api/v1/chart/<id>/data` returns 400 "no query context". Set both `params` and `query_context` on create or update. Viz keys that work here: `table`, `big_number_total`, `pie`, `echarts_timeseries_bar` (`dist_bar` is **not registered**).
6. **Link charts to dashboards from the chart side.** `PUT /api/v1/chart/<id> {"dashboards":[<DASH_ID>]}`. The dashboard POST ignores `charts`, and `position_json` alone doesn't link them.
7. **Native filters** live in the dashboard's `json_metadata.native_filter_configuration`. Clone an existing filter object, give it a new id `NATIVE_FILTER-<random hex>`, and set `targets:[{datasetId, column:{name}}]` + `chartsInScope`. **Keep existing filters** in the array. The dataset must expose the column (rule 2).
8. **Drill-down = cross-filters.** Set `cross_filters_enabled` on the dashboard, and in `chart_configuration` scope each summary chart to emit only to its own line list. Native drill-to-detail (`/datasource/table/<id>/samples`) returns 404 on this instance.
9. **60-second webserver timeout.** A dataset that takes longer makes the chart and **CSV download** fail ("report not downloading"). Fix the SQL (`skills/report-performance`). Adding permissions won't help.

## Access & RLS
- A role needs **`datasource_access` on the dataset** (and dashboard access) to see anything. Missing access and a timeout look the same to the user ("it doesn't load"), so check both.
- **RLS rules on one dataset AND-combine** across the rules that apply to a role. Three overlapping block rules on one role is legal but fragile. Keep one clean rule per role.
- Admins bypass RLS. Test as a restricted user, or reproduce the RLS `WHERE` yourself.

## Migrating Metabase → Superset
Native Metabase cards become virtual datasets (the SQL ports as-is, both are Postgres). MBQL aggregates become charts: parse `stages[0]` (source-card, breakout, aggregation, filters). **Verify every count equals Metabase**, and preserve hidden dedups (e.g. `visit_no = 1`). If a pie shows a blank NULL slice, confirm with the client whether they want `IS NOT NULL`.

## Verify
- SQL Lab execute through the same DB: `POST /api/v1/sqllab/execute/ {database_id, sql:"select count(*) from (<dataset sql>) q", runAsync:false}`. Check the count and wall time.
- `POST /api/v1/chart/data` with the chart's saved `query_context` → 200 + rowcount.
- Back up dataset and dashboard JSON before every PUT (`ss.py` does this).

See `references/api.md` for payload skeletons.
