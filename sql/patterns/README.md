# SQL patterns for the Avni flat ETL schema

Replace `<schema>`, `<table>` and `"<Column>"` using `schemas/<org>/CATALOG.md`. Every pattern names the trap it avoids.

| File | Use for |
|---|---|
| `latest_nonnull_per_entity.sql` | current status / latest measure per person |
| `membership_distinct_on.sql` | people per group attribute without double counting |
| `coded_multiselect.sql` | multi-select logic via `_coded` (only / any / per answer) |
| `uuid_array_unnest.sql` | attendance or student-picker arrays → names |
| `roster_left_join.sql` | everyone registered, with or without activity |
| `period_quick_filter.sql` | Today / This Week / … + date range filters |
| `materialized_lookup.sql` | concept UUIDs → names, fast |
| `lateral_top1.sql` | latest visit per entity without a full-table sort |
| `sentinel_case.sql` | NULL-safe categories shared by metric and drill |
| `generate_series_trend.sql` | trends that keep zero months |

Card shape: **base CTE (joins + `is_voided=false` + all filters) → metric → labelled output**.
