# AGENTS.md — Avni reporting skill pack

You are helping build or fix **reports for Avni organisations** in Metabase, Superset or Jasper.
This file is the entry point for every agent (Claude Code, Cursor, Codex, Grok, Copilot).
Read it fully, then load **only** the skill you need.

## Golden rules (non-negotiable)

1. **Dump the org's schema first. Every time you start work on an org.** Run `./tools/dump_org_schema.sh <schema>`, then read and grep `schemas/<schema>/CATALOG.md` for tables, columns and coded values. Do **not** explore `information_schema` or browse the database/Metabase to discover structure. That wastes tokens and API/DB calls. The tools enforce this: any query on an org schema without a local catalogue is refused.
2. **No personal data (PII) goes to the AI.** Names, phone numbers, Aadhaar/ABHA/bank/ration numbers, dates of birth, addresses, GPS, emails and staff names must never enter your context.
   - Work with **counts and aggregates**. Verify line lists by **row counts**, not by reading rows.
   - Only run SQL through `tools/q.sh`, `tools/mb.py run`, `tools/ss.py sqllab`. They **mask PII automatically**. Never run raw `psql` or open exported data files.
   - Never ask the user to paste client spreadsheets, beneficiary lists or screenshots showing people's details. If one arrives in a ticket, don't open it. Ask for a de-identified version, or process it with a local script that outputs counts only.
   - Never put PII in files, commits, learnings, replies or eval cases.
3. **Production is read-only.** Query only through `tools/tunnel.sh` (sets `default_transaction_read_only=on`) or `tools/q.sh`. Never run INSERT/UPDATE/DELETE/DDL on any Avni database. Indexes and ETL changes belong to Avni infra.
4. **Patch in place, never recreate.** Cards, dashboards, datasets and charts have bookmarked URLs. Change SQL and settings on the existing object. When editing a Metabase card, reuse its existing `template-tags` and `parameters` verbatim.
5. **Back up before any write.** `tools/mb.py` and `tools/ss.py` save JSON to `backups/` and are dry-run until `--apply`.
6. **Output must be proven, not assumed.** Before saying "done", run the checks in `skills/report-qa`: metric count == drill row count, identities add up, and `EXCEPT ALL` = 0 both ways for performance rewrites.
7. **Read the whole ticket.** The Freshdesk API returns 10 conversations per page. Paginate, and open every attachment. The latest client message is usually the real ask.
8. **No secrets or personal data** in files, commits, logs or replies. Refer to people by role.
9. **Change only what was asked.** If you spot other problems, list them, don't fix them silently.

## Working with beginners (interns, non-technical staff)

Many users follow `START-HERE.md` and talk in plain words. Map their phrases to actions:

| They say | You do |
|---|---|
| "open the read-only connection" / "set me up" | `./tools/tunnel.sh up` and confirm "read-only proven" |
| "download the data map for <org>" | `./tools/dump_org_schema.sh <schema>` (look up the schema from the org name: `select name, schema_name from public.organisation where name ilike '%<org>%'`) |
| "read this requirement sheet <file / Google Sheet link>" | `python3 tools/read_requirements.py <source> --org <schema>` → read the .md → fill `templates/requirement-mapping.md` and show it as a short table: ✅ / ❓ / ⛔ per row |
| "fill in the requirement form" | walk through `templates/requirement-intake.md` and ask **only** the open questions, max 3–4 at a time |
| "show me the numbers, don't create anything" | run read-only queries (`tools/q.sh`), give a short table + total, no Metabase writes |
| "show me the plan first" | list the cards, filters and click-throughs you'll create/change, then **wait for a yes** |
| "run the checks" | `skills/report-qa`: load time, dropdown filters, metric == click-through list count, totals add up, no raw IDs |
| "the list shows everyone" / "the filter is a typing box" | look up `playbooks/drilldown-issues.md` / `playbooks/filter-issues.md` |
| "write the reply" | `templates/client-reply.md`, plain language, only verified claims |
| "/learn" | `skills/report-learnings` capture step |

If a beginner asks to "show the list with names/phone numbers": explain that the AI never sees personal details, and show counts plus the masked list instead. They can open the real list themselves in Metabase.

With beginners: explain in **simple words** (no SQL unless asked), say "table" as "register/list", show small result tables, always **plan before building**, build in the **practice folder** unless told otherwise, and give them the exact line to paste when a write needs their approval.

## Workflow

```
intake ──► catalogue ──► pattern ──► build (API) ──► QA ──► handover
```

1. **Intake.** Requirements usually arrive as a **sheet** (Google Sheet, `.xlsx` or `.csv`) with one row per indicator and its logic. Run `python3 tools/read_requirements.py <file or link> --org <schema>`, read the generated `requirements/<org>/<name>.md`, then fill `templates/requirement-mapping.md`: every row marked ✅ buildable / ❓ needs clarification / ⛔ not in data, using the catalogue. Send all ❓/⛔ questions to the client in **one** message. With no sheet (a ticket or chat message), use `templates/requirement-intake.md`: grain, metric definitions, filters, drills, tool, target collection or dashboard.
2. **Catalogue (mandatory, before any SQL).** `./tools/dump_org_schema.sh <schema>`, then **grep `schemas/<schema>/CATALOG.md`**. It's compact and already hides personal values. Re-dump when you hit "column does not exist" or the catalogue is older than 14 days.
3. **Pattern.** Adapt a file from `sql/patterns/`. Check `skills/avni-etl-data-model` for traps (voided, coded multi-selects, UUID arrays, membership double-counts, NULL dates).
4. **Build.** Metabase → `skills/metabase-reports`. Superset → `skills/superset-reports`. Jasper → `skills/jasper-reports` (diagnose and safe edit only).
5. **QA.** `skills/report-qa` + `tools/qa.py`. Time it cold and warm. It must load well under 60s (Superset) or 120s (Metabase), and should be under 30s.
6. **Handover.** `templates/handover-note.md` + `templates/client-reply.md`. Claim only what you verified.
7. **Learn (mandatory).** Before ending, check whether anything was new, surprising, or contradicted a skill. If so, record it with `python3 tools/add_learning.py …` (see `skills/report-learnings`). Corrections to wrong advice matter most. In Claude Code: `/learn`.

## This pack keeps learning

`LEARNINGS.md` is the inbox. **Every agent appends to it** at the end of a task, and the safety scan rejects secrets, IDs and personal data. Periodically someone runs `/curate` (or follows `skills/report-learnings` §2) to promote entries into skills, playbooks, patterns and eval cases, then clears the inbox. If you are told the pack gave wrong advice, **fix the skill text in the same task** and add an eval case, so the next agent doesn't repeat the mistake.

## Keep token cost low

- Grep the local `CATALOG.md`, and don't explore the schema live.
- Count first (`select count(*)`), then `LIMIT 20`. Never print whole result sets.
- Load one skill at a time. Open `references/` files only when that sub-topic comes up.
- Match a symptom to `playbooks/` before investigating from scratch. Most bugs are already solved there.
- Use a cheaper model or a sub-agent for broad exploration, and keep the main context for decisions.

## When a write is blocked

Some agent harnesses (e.g. Claude Code auto-mode) block writes to shared services. Don't route around the block. Put the change in an idempotent script and hand the human the command (`! python3 tools/mb.py ... --apply` in Claude Code). The human runs it and the output comes back to you.

## Where things are

| Need | Go to |
|---|---|
| Which tool / skill? | `skills/avni-reporting/SKILL.md` |
| Table & column meaning | `skills/avni-etl-data-model/SKILL.md` + `schemas/<org>/CATALOG.md` |
| Filter doesn't work / dropdown is free text | `playbooks/filter-issues.md` |
| Drill shows wrong rows | `playbooks/drilldown-issues.md` |
| "Report doesn't match the app" | `playbooks/count-mismatch.md` |
| Slow / timeout | `skills/report-performance/SKILL.md` |
| Real past cases | `playbooks/case-studies.md` |
