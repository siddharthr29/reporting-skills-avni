# Lab 1 — Your first filtered card (20 min)

**Goal:** a Metabase card "Registered people by Block" on `<practice_schema>` with a **searchable Block dropdown** and optional date filters, placed on a practice dashboard.

## Steps
1. `./tools/tunnel.sh up`. Confirm it prints "read-only proven".
2. `./tools/dump_org_schema.sh <practice_schema>`
3. Ask your agent:
   > Using AGENTS.md and the avni-reporting skill, grep `schemas/<practice_schema>/CATALOG.md` and tell me which table holds registered people and which address column is the Block. Don't query the DB.
4. Ask your agent to write the card SQL from the base-CTE shape in `skills/metabase-reports/SKILL.md`, with `[[ and a."Block" = {{block}} ]]` and date filters on `registration_date`.
5. Validate it read-only: `./tools/q.sh -f card.sql` (the optional filters are stripped automatically).
6. Create the card in your practice collection (UI or API), then apply the **dropdown recipe** from `skills/metabase-reports/references/filters.md` (values card + tag + parameters + dashboard parameter).
7. Put it on a practice dashboard and map the Block filter.

## Done when
- [ ] The filter opens a **searchable list** on the dashboard *and* on the card page.
- [ ] No voided values in the list.
- [ ] Sum over all Blocks = the unfiltered total (identity check).
- [ ] `python3 tools/qa.py time <your card>` shows under 30s cold.
