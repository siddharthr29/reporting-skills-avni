---
name: avni-reporting
description: Entry/router skill for any Avni report task (build, change, or debug) in Metabase, Superset or Jasper. Use first; it runs intake, picks the tool, and points to the next skill, SQL pattern and playbook.
---

# Avni reporting — router

## 1. Classify the request (one line)

| Mode | Signals | Next |
|---|---|---|
| **Build** a new report | "create a dashboard", requirement sheet, indicator list | Intake → data model → tool skill |
| **Change** an existing report | "add a column/filter", "rename", "move Location before Community" | Fetch live object → patch in place |
| **Debug** a wrong/slow report | "not matching app", "drill shows all", "not downloading", "filter not working" | `playbooks/` first, then data model |

## 2. Pick the tool

| Org is on… | Use | Skill |
|---|---|---|
| Metabase (most orgs, self-service) | `reporting.avniproject.org` | `metabase-reports` |
| Superset (e.g. APF Odisha, JNPCT, Ekam) | `reporting-superset.avniproject.org` | `superset-reports` |
| Jasper (legacy, e.g. RWB) | `reporting-jasper.avniproject.org/jasperserver` | `jasper-reports` (diagnose + safe edit) |

All three read **the same per-org flat ETL schema** in the one `openchs` Postgres. SQL that is correct in one tool is correct in all three. Only the wiring (parameters, filters, drills) differs.

## 3. Intake: ask once, up front

Use `templates/requirement-intake.md`. The minimum you need before writing SQL:
- **Grain**: one row per what? (child, enrolment, visit, session, attendance mark)
- **Definition** of each metric, meaning numerator and denominator in data terms. Confirm tricky ones: *enrolled vs registered*, *active cohort vs all*, *latest visit vs any visit*.
- **Filters**: which ones, dropdown or free text, defaults, required or optional.
- **Drill-downs**: which numbers must be clickable, and what the drilled list shows.
- **Where**: collection or dashboard, and whether it is a new object or a change to `<existing link>`.
- **Order of columns**: the client's sheet is the source of truth.

## 4. Build path

1. **First, always:** `./tools/dump_org_schema.sh <schema>`, then grep `schemas/<schema>/CATALOG.md` for the tables and columns. Don't browse the live DB for structure (the tools refuse un-dumped schemas).
2. Read the traps list in `avni-etl-data-model`.
3. Start from `sql/patterns/*.sql`. Shape every card as **base CTE (filters + voided) → metric → labelled output**.
4. Validate the SQL read-only (`tools/q.sh`), with filters stripped (`[[ ... ]]` removed) and then with filters set.
5. Build or patch through the tool skill.
6. Run `report-qa` before handover.

## 5. Debug path: check these first, in order

1. **Voided rows**: `is_voided = false` on every joined table (except "left the programme" metrics; see data model).
2. **Definition gap**: report vs app differ by design (enrolled vs registered, address-scoped app dashboard). Answer with exact numbers.
3. **ETL lag / stale schema**: `entity_sync_status`, renamed or `_old` or `voided_` columns, Metabase schema cache (`sync_schema`).
4. **Duplicates**: `count(distinct …)`, `DISTINCT ON` for membership and latest-per-entity.
5. **Timezone**: `at time zone 'Asia/Kolkata'` before `date_trunc`.
6. **Wiring**: parameter → tag mapping, click behaviour target, RLS rules, dataset columns.

Then open the matching playbook: `filter-issues.md`, `drilldown-issues.md`, `count-mismatch.md`.

## Standards every report meets

- **Three tiers**: title + "what these metrics mean" → count cards → drillable line lists.
- **One base query** per dashboard, and the same filters everywhere.
- **Numerator and denominator shown** next to every %, with divide-by-zero guarded (`NULLIF`).
- **Honest blanks**: missing fields read `(Not collected yet)`, and LEFT JOIN so they fill in later.
- **Loads under 30s** cold. Line lists capped at `LIMIT 2000` (the Metabase display cap).
- **No raw UUIDs** in output. Resolve them to names.

## Privacy: no PII to the AI
Reports may show beneficiary names to the *client*. **You** (the agent) only ever see masked output. Check line lists by row count. Query only through `tools/q.sh`, `mb.py run`, `ss.py sqllab`, which mask names, phones, IDs, DOB, addresses and GPS. Never open client files or screenshots containing people's details.
