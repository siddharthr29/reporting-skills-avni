<p align="center">
  <img src="assets/avni-logo.png" alt="Avni" width="260">
</p>

<h1 align="center">reporting-skills-avni</h1>

<p align="center">
  Everything we learned building Avni reports in <b>Metabase</b>, <b>Superset</b> and <b>Jasper</b>,<br>
  packaged so an AI coding agent (Claude Code, Cursor, Codex, Grok, Copilot) and an intern can build reports fast, correctly and cheaply.
</p>

<p align="center">
  <a href="START-HERE.md"><b>New here? Start here</b></a> ·
  <a href="https://siddharthr29.github.io/reporting-skills-avni/">▶ Session deck</a> ·
  <a href="AGENTS.md">Agent entry point</a> ·
  <a href="playbooks/">Fix playbooks</a> ·
  <a href="labs/">Hands-on labs</a>
</p>

---

## Why this exists

Reports for Avni orgs kept going wrong in the same few ways. Drill-downs opened the whole list, dropdown filters showed up as free-text boxes, a form change silently broke a card, and a line list timed out after 60s. Agents also burned tokens re-discovering an org's schema every session. This repo turns ~30 real report builds and support tickets into:

- **Skills** that an agent loads on demand (`skills/*/SKILL.md`).
- **Playbooks** mapping every filter and drill-down bug we hit: symptom → cause → fix → how to verify.
- **A SQL pattern library** for the Avni flat ETL schema (`sql/patterns/`).
- **Tools**: a read-only tunnel, a **one-command schema dump** that turns an org into a small `CATALOG.md` the agent can grep, and Metabase/Superset API clients that back up before they write.
- **Templates, labs and evals** for onboarding and for checking that an agent understood the material.

## 10-minute quickstart

```bash
git clone https://github.com/siddharthr29/reporting-skills-avni.git
cd reporting-skills-avni
./tools/setup.sh                      # enter YOUR OWN Metabase API key + Superset login (hidden), DB access from your lead
./tools/tunnel.sh up                  # read-only tunnel to the replica; proves a write FAILS
./tools/dump_org_schema.sh <schema>   # e.g. sangwari → schemas/sangwari/CATALOG.md (gitignored)
```

Then open the repo in your agent and ask, for example:

> *"Using the avni-reporting skill, build a Metabase card for `<org>`: count of children enrolled by block, with Block and Date filters and a drill-down to the line list."*

The agent reads `AGENTS.md`, then `skills/avni-reporting/SKILL.md`, then the catalogue, then a SQL pattern. It builds through the API and runs the QA checks before calling the job done.

## Map of the repo

| Path | What's inside | Read it when |
|---|---|---|
| [`AGENTS.md`](AGENTS.md) | Golden rules + the workflow. Every agent starts here. | Always |
| [`skills/avni-reporting`](skills/avni-reporting/SKILL.md) | Router: intake → pick tool → which skill next | Any reporting task |
| [`skills/avni-etl-data-model`](skills/avni-etl-data-model/SKILL.md) | Flat ETL schema, coded/multi-select, voided, membership, address, latest-per-entity | Writing any SQL |
| [`skills/metabase-reports`](skills/metabase-reports/SKILL.md) | API, cards, dropdown filters, drill-downs, permissions | Metabase work |
| [`skills/superset-reports`](skills/superset-reports/SKILL.md) | Datasets, charts, query_context, native filters, RLS, timeouts | Superset work |
| [`skills/jasper-reports`](skills/jasper-reports/SKILL.md) | Diagnose + safe edit (export → edit JRXML → re-import) | Jasper tickets |
| [`skills/report-performance`](skills/report-performance/SKILL.md) | Dead CTEs, MATERIALIZED, LATERAL, row caps | Anything slow / timing out |
| [`skills/report-sql-review`](skills/report-sql-review/SKILL.md) | SQL code review: dead joins, per-row lookups, voided, multi-select traps, plan check | Any SQL written or changed |
| [`skills/report-qa`](skills/report-qa/SKILL.md) | EXCEPT ALL, metric == drill, identities, UUID-leak scan | Before you say "done" |
| [`playbooks/`](playbooks/) | Filter issues, drill-down issues, count mismatches, ticket handling, case studies | Debugging a ticket |
| [`sql/patterns/`](sql/patterns/) | Copy-paste SQL for recurring Avni shapes | Writing SQL |
| [`tools/`](tools/) | tunnel, schema dump + catalogue, Metabase/Superset clients, QA | Setup + every build |
| [`templates/`](templates/) | Requirement intake, report spec, handover note, client reply | Start / end of a job |
| [`labs/`](labs/) | 3 hands-on labs with solutions | Training |
| [`evals/`](evals/) | Prompts + must-include answers to test an agent | After changing skills |
| [`docs/`](docs/) | The 8-slide session deck (GitHub Pages) | The session |

## Safety in one paragraph

**Everyone uses their own logins.** `./tools/setup.sh` asks for your personal Metabase API key and Superset username/password and checks they work. The tools refuse to run with a settings file someone else created. Production is **read-only, always**. The tunnel sets `default_transaction_read_only=on` and proves a write fails. Report changes are made **in place**; never recreate a card or dashboard, because users bookmark links. Every write through `tools/mb.py` or `tools/ss.py` is a dry-run until you pass `--apply`, and it saves a JSON backup first. Nothing secret or personal goes in this repo: `tools/.env`, `schemas/` and `backups/` are gitignored, and CI runs a secret and anonymisation scan.

## What's anonymised

Org names are real because you'll meet these orgs in tickets. Database, card, dashboard and dataset IDs are written as `<DB_ID>`, `<CARD_ID>` and so on, and internal hosts as `<SSH_JUMP_HOST>` / `<READ_DB_HOST>`. No personal names, emails, participant data or credentials appear anywhere.
