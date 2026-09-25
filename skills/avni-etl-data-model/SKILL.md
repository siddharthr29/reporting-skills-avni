---
name: avni-etl-data-model
description: How Avni's per-org flattened ETL schema really works and every data trap we hit (voided rows, coded/multi-select answers, UUID arrays, group membership double-counts, latest-per-entity, NULL dates, address hierarchy, stale schemas). Use before writing any report SQL.
---

# Avni ETL data model — what the tables mean and where they bite

## The two surfaces (same database)

| | OLTP | ETL / reporting |
|---|---|---|
| Schema | `public` | per org: `organisation.schema_name` (e.g. `sangwari`, `apfodisha`) |
| Shape | normalised, observations in **jsonb**, address as `ltree` | **flat**: one column per concept, address flattened |
| Scoped by | RLS, only after `set role "<org>"` | the schema itself |
| Freshness | live | incremental sync every **~90 min** |

- Reports read **ETL**. The app reads **OLTP**. Some difference inside the sync window is normal.
- **Schema shadowing:** tables like `individual` exist in both. Always **schema-qualify** (`sangwari.individual`, `public.concept`).
- The shared login **bypasses RLS**. `select count(*) from public.individual` returns every org's rows. Never read org data from `public` without `set role`.

## Table naming (per org)

| Kind | Pattern | Example |
|---|---|---|
| Subject | `<subject_type>` | `individual`, `household`, `student` |
| Enrolment | `<subject>_<program>` | `individual_child` |
| Program encounter | `<subject>_<program>_<encounter>` or `<subject>_<encounter>` | `individual_child_growth_monitoring` |
| General encounter | `<subject>_<encounter>` | `student_daily_attendance` |
| Exit / cancel | `…_exit`, `…_cancel` | `individual_child_exit` |
| Multi-select answers (EAV) | `<table>_coded` | one row per selected answer |
| Repeatable question group | `<table>_<group_name>` (truncated to 63 chars) | joins on `program_encounter_id = parent.id` |
| Group membership | `<group>_<member>` / `group_subject` | `group_subject_id → member_subject_id` |
| Address | `address` (one row per location, level columns) | `"District"`, `"Block"`, `"Village"` |
| Views | `enrolment_view`, `completed_visits_view`, `subject_view` … | rebuilt each run. **Can be empty. Verify before using.** |

Standard columns on data tables: `id, uuid, is_voided, address_id, created/last_modified_date_time, created_by_id, filled_by_id`. Encounters also have `encounter_date_time, earliest_visit_date_time, max_visit_date_time, cancel_date_time`.

## The traps (read all; each cost us a ticket)

1. **Voided rows.** Put `is_voided = false` on **every** joined table, and on dropdown value sources too. **Exception:** exits void the membership link (e.g. `class_student`), so metrics about people who *left* must not filter membership by `is_voided`. Take the latest link with `DISTINCT ON`. ETL can also suffix voided names (`AKN (voided~1374620)`), so value sources also need `NOT ILIKE '%voided%'`.
2. **Multi-select answers.** The flat column is **comma-joined text**, and some answer names contain commas (`Empathy, Non-Judgement (Gossiping)`). `ILIKE '%Baseline%'` matched `Baseline, Other`. For per-answer logic use the **`_coded` table** (`bool_and(answer IN (...))`). Pattern: `sql/patterns/coded_multiselect.sql`.
3. **Subject pickers and attendance** store a **JSON array of UUIDs** as text. `jsonb_array_elements_text(col::jsonb)` joined to `<subject>.uuid`, guarded by `col ~ '^\['`. Never output raw UUIDs. Pattern: `uuid_array_unnest.sql`.
4. **Membership double-counts.** A person in two groups is counted twice (251 vs 249; donor slices summed to 21,761 vs 21,525 people). Use `DISTINCT ON (member_subject_id) … ORDER BY id DESC` or `count(distinct)`. Pattern: `membership_distinct_on.sql`.
5. **Roster vs activity.** An INNER JOIN to attendance or enrolment shows only people *with* activity (173 vs 200 registered). Build **roster-based** with a LEFT JOIN plus a status filter defaulting to the common case. Pattern: `roster_left_join.sql`.
6. **Latest per entity** means the latest **non-null value per measure**, not the latest row. Otherwise a blank last visit reads as "not recovered" (a real bug: 0/0/1 was really 2/1/14). Pattern: `latest_nonnull_per_entity.sql`.
7. **NULL dates.** `encounter_date_time IS NULL` = scheduled or overdue. `cancel_date_time IS NOT NULL` = cancelled. Exclude both from "conducted". Some orgs have NULL `encounter_date_time` on most rows, so fall back to `earliest_visit_date_time`. Month cards drop NULL-dated rows while totals keep them, so document which.
8. **Duplicates in data.** Double-entered forms or enrolments: dedup with `DISTINCT ON (individual_id) … ORDER BY date DESC`.
9. **Stale schema / concept drift.** A form change renames, re-cases or retires columns (`"WEIGHT"`→`"Weight"`, removed field → `voided_<name>` or `_old`, typo fixes in table names but not columns). When a card suddenly errors, check the column in `CATALOG.md` or `information_schema` first. If Postgres has the column but Metabase doesn't, **sync Metabase's schema** (`POST /api/database/<DB_ID>/sync_schema`, plus `rescan_values` for dropdowns).
10. **ETL lags form changes.** A brand-new concept may exist in forms but not yet in ETL. If you must have it now, read OLTP jsonb (`observations->>'<concept_uuid>'`) and switch to ETL once it lands.
11. **Address columns vary per org** (`Phc`, `Subcentre`, `Cluster`, `Para`, `City`, `School`). Look them up in the catalogue. Same-named places exist (two "Raigarh District" nodes), so drills must pass village + district + state.
12. **63-character identifiers.** Long concept names are truncated (the original is in `public.column_metadata`). Metabase aliases can collide the same way, so use short aliases.
13. **Coded single-select** values are stored as **labels**, so no concept lookup is needed. Reason-UUID arrays (e.g. `reason_concept_uuids`) do need `public.concept`, and must use a **materialised lookup**, never a per-row subquery on that huge cross-org table.
14. **Packed values.** `SAM (-3.95)` = category + z-score in one text field; parse the prefix. Durations like `PT1H30M` need regex parsing. Text numbers need a `~ '^[0-9.]+$'` guard before casting.
15. **Empty views and forms.** `subject_view` / `enrolment_view` / `completed_visits_view` were empty for some orgs. Many fields are 0% filled because they are new. LEFT JOIN, label `(Not collected yet)`, and never fake a number.
16. **Type clashes.** In `UNION ALL` across forms, cast everything to `::text`. NUMERIC columns use `IS NOT NULL`, not `NULLIF(x,'')`. PostGIS point columns break table views (exclude them or cast `::text`).
17. **Postgres limits.** 1,664 columns max, so don't explode every multi-select into columns. `NOT (a OR b)` drops NULL rows, so use `coalesce(cond,false)`.
18. **Media** is in private S3. Link to the web-app encounter instead: `https://app.avniproject.org/#/app/subject/viewEncounter?uuid=<encounter_uuid>`.

## ETL health (when a report is empty or stale)

See `references/etl-health.md` for the SQL. In short: check `public.entity_sync_status` for the schema (fresh? `Success`?), then the job log `GET <avni-origin>/etl/job/<orgUUID>`. An orphan table with an old `last_sync_time` and 0 rows usually belongs to a **voided form mapping**. That is not an ETL failure.

## Need more?
- `references/etl-health.md` — freshness, stalled tables, `_old` columns, recreate procedure.
- `references/oltp-fallback.md` — reading OLTP jsonb safely (RLS, `set role`, search_path).
