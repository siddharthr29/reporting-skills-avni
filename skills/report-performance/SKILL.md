---
name: report-performance
description: Make slow Avni report queries fast without touching production (no indexes/DDL) — find dead CTEs, force AS MATERIALIZED, LATERAL top-1 per entity, materialised lookups on huge public tables, grain reduction, row caps. Use when a card/dataset/download is slow or times out (Superset 60s, Metabase ~120s).
---

# Report performance — the playbook

**You cannot add indexes or run DDL on production.** Every fix here is a **query rewrite**, proven identical with `EXCEPT ALL` (see `report-qa`).

## Step 1 — measure
```sql
explain (analyze, buffers) <query with filters stripped>;
```
Look for the node that takes the time: `Seq Scan` + `Sort` over millions of rows, `SubPlan` executed per row, or `loops=` × a big number. Time it **cold and warm** (4–7s cold vs <1s warm is common). Time it on the tool (Metabase/Superset), not only the replica. Prod Metabase can take minutes where the replica takes 135ms.

## Step 2 — the fixes that worked (in the order to try them)

| # | Smell in the plan | Fix | Real result |
|---|---|---|---|
| 1 | A CTE computes a window over a big table, but **none of its columns reach the final SELECT** | **Delete the dead CTE and its join** | APF Odisha Childline dataset: 1.6M-row `row_number()` sort removed, **2–5 min → 0.8s**, output identical |
| 2 | Postgres **inlined** a heavy CTE into a small outer query and re-ran it per row | `with x as materialized (...)` | Durga: 103s → 1.1s (and it had slowed the whole Metabase instance) |
| 3 | A correlated subquery per row against `public.concept` / `entity_approval_status` / `checklist*` (huge, cross-org) | Materialise just the UUIDs you need: `with c as materialized (select uuid,name from public.concept where uuid in (...))` | Gubbachi attendance: 41s → 0.7s; >120s timeout → 1.3s |
| 4 | "Latest row per entity" via `row_number()` over the **whole** table | `left join lateral (select … where x.individual_id = i.id order by d desc limit 1)`, which uses the existing `individual_id` index | 2–5 min → ~9s |
| 5 | An OLTP `public.*_view` (jsonb parsing across all orgs) | Rewrite on the org's ETL tables | Calcutta Kids: 74s → 1.0s |
| 6 | No ETL table exists (checklists) | `with cicv as materialized (select * from checklist_item_checklist_view)` + base-table joins | timeout → 5.7s |
| 7 | Line list of thousands of rows | `LIMIT 2000` (the display cap), and drop unused columns | faster render |
| 8 | Too fine a grain (per media file) | Change grain (per session) when the client agrees | 1,086 → 216 rows |
| 9 | The same expensive expression repeated (e.g. splitting an array 30×) | Compute it once in a base CTE | −6s |

Rules of thumb:
- Heavy multi-CTE + small outer query → `MATERIALIZED`.
- Never correlate per row against a cross-org `public` table.
- Filters belong **inside** the base CTE so every card scans less.
- A composite index *would* also work, but it needs Avni infra and is almost never necessary. Prove the rewrite first.

## Step 3 — prove it's the same data
```sql
with a as materialized (<old sql>), b as materialized (<new sql>)
select (select count(*) from a) old_rows, (select count(*) from b) new_rows,
       (select count(*) from (select * from a except all select * from b) x) old_minus_new,
       (select count(*) from (select * from b except all select * from a) y) new_minus_old;
-- ship only if old_rows = new_rows and both differences = 0
```
`tools/qa.py except-all old.sql new.sql` runs this for you.

## Timeouts, by tool
| Tool | Limit | Symptom |
|---|---|---|
| Superset | 60s webserver | chart spinner then error; **CSV download fails** |
| Metabase | ~120s query | "Your question took too long"; the whole instance slows for everyone |
| Jasper | server-side | report hangs or blanks |
