---
name: report-sql-review
description: SQL code review for every Avni report card or dataset before it ships — run tools/sql_review.py (static checks + optional EXPLAIN plan), fix errors, justify or fix warnings. Use whenever SQL is written or changed, and when a card is slow or its numbers look wrong.
---

# SQL code review: no card ships without it

```bash
python3 tools/sql_review.py card.sql --explain          # a file you wrote
python3 tools/sql_review.py --card <CARD_ID> --explain  # a live Metabase card
python3 tools/qa.py audit-dash <DASH_ID>               # reviews every card on a dashboard
```
`--explain` asks Postgres for the plan (read-only, no rows read) and flags big scans and sorts.

## What it checks and why

| Rule | Level | Why it matters (real case) |
|---|---|---|
| `dead-join` | error | CTE LEFT JOINed but none of its columns used: APF Odisha download **2–5 min → 0.8s** after removing it |
| `dead-cte` | error | CTE never used, pure wasted time |
| `correlated-public` | error | Per-row subquery on `public.concept`/approval/checklist tables: Gubbachi **41s → 0.7s** with a materialised lookup |
| `filter-block` / `filter-block-or` | error | `[[ ]]` without `{{var}}`, or with OR inside: Metabase rejects the card |
| `big-sort` (plan) | error | Sorting >1M rows. Usually a window/DISTINCT over a whole table |
| `voided` | warn | Counted table without `is_voided=false`: deleted records inflate numbers. (LEFT JOIN lookups are just a note) |
| `window-cte` | warn | Ranking a whole table: use `LATERAL … LIMIT 1` for "latest per person" |
| `ilike-multiselect` | warn | `ILIKE '%Baseline%'` matched "Baseline, Other" (Durga, 39 sessions wrong). Use `_coded` |
| `not-in` | warn | `NOT IN (select…)` returns nothing if the subquery has a NULL. Use `NOT EXISTS` |
| `select-star`, `limit` | warn | Line lists: named columns + `LIMIT 2000` (Metabase's display cap) |
| `divide-by-zero` | warn | `/ count(…)` without `NULLIF(…,0)` |
| `hardcoded-date` | warn | Use `{{start_date}}`/`{{end_date}}` filters |
| `seq-scan`, `subplan` (plan) | warn | Full scans of >500k rows, per-row subqueries |
| `timezone`, `count-distinct`, `materialize`, `cte-order` | note | Correctness and speed hints to consider |

## How to act on the result
- **Errors: fix before shipping.** No exceptions.
- **Warnings: fix, or say why not** in the card description (e.g. "voided not filtered: this card counts people who left").
- **Notes: judgement calls.** Mention them in the handover if relevant.
- After any rewrite of a live card, prove the output is unchanged with `tools/qa.py except-all old.sql new.sql` (0 / 0), unless the change is meant to change numbers. Then say so to the client.
