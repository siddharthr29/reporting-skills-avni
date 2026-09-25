# AGENTS.md — Avni reporting skill pack

You are helping build or fix **reports for Avni organisations** in Metabase, Superset or Jasper.
This file is the entry point for every agent (Claude Code, Cursor, Codex, Grok, Copilot).
Read it fully, then load **only** the skill you need.

## Golden rules (non-negotiable)

1. **Production is read-only.** Query only through `tools/tunnel.sh` (sets `default_transaction_read_only=on`) or `tools/q.sh`. Never run INSERT/UPDATE/DELETE/DDL on any Avni database. Indexes and ETL changes belong to Avni infra.
2. **Patch in place, never recreate.** Cards, dashboards, datasets and charts have bookmarked URLs. Change SQL and settings on the existing object. When editing a Metabase card, reuse its existing `template-tags` and `parameters` verbatim.
3. **Back up before any write.** `tools/mb.py` and `tools/ss.py` save JSON to `backups/` and are dry-run until `--apply`.
4. **Output must be proven, not assumed.** Before saying "done", run the checks in `skills/report-qa`: metric count == drill row count, identities add up, and `EXCEPT ALL` = 0 both ways for performance rewrites.
5. **Read the whole ticket.** The Freshdesk API returns 10 conversations per page. Paginate, and open every attachment. The latest client message is usually the real ask.
6. **No secrets or personal data** in files, commits, logs or replies. Refer to people by role.
7. **Change only what was asked.** If you spot other problems, list them, don't fix them silently.

## Workflow

```
intake ──► catalogue ──► pattern ──► build (API) ──► QA ──► handover
```

1. **Intake.** Fill `templates/requirement-intake.md` in one round of questions: grain, metric definitions, filters, drills, tool, target collection or dashboard.
2. **Catalogue.** `./tools/dump_org_schema.sh <schema>`, then **grep `schemas/<schema>/CATALOG.md`** instead of querying `information_schema` repeatedly. Re-dump when you hit "column does not exist".
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
