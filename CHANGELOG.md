# Changelog

Curated learnings are recorded here when they move from `LEARNINGS.md` into the skills.

## 2026-09-25 — workshop deck redesign
- Deck rebuilt as a hands-on workshop handout (serif headings, ruled layout, no emoji/gradients): every step is a numbered "Do this" list with exact clicks, a "Type exactly" box with copy button, what Claude replies, and tick-boxes.
- New slide 2 "Why this pack, and not just ask the AI" (side-by-side + real proof). Deck is now 9 slides with a timed agenda.

## 2026-09-25 — built from real client feedback
- New `playbooks/client-feedback-lessons.md`: 32 real client issues from 17 orgs (what the client said → what was really wrong → the rule it created), plus 8 mistakes we made ourselves and the rule each created.
- README, AGENTS.md, START-HERE and deck slide 1 state that everything comes from real client feedback and requirements; `/curate` promotes new client feedback onto that page.

## 2026-09-25 — Definition of done, SQL review, dashboard audit, folders & permissions
- AGENTS.md **Definition of done** (8 standards): SQL reviewed, ≤5s per card, exact drill-down (also filtered), every number clickable, dropdown filters (dashboard + card page), standard folders, folder-wise permissions, proven numbers. Agents state it in the plan and report ✅/❌ at the end.
- New skill `report-sql-review` + `tools/sql_review.py` (static rules incl. dead-join/dead-CTE/per-row public lookups/voided/multi-select ILIKE/NOT IN/LIMIT; `--explain` plan check). Catches the APF Odisha dead join.
- `qa.py audit-dash <id> [--param k=v]`: one scorecard for dropdowns, wiring, clickable, drill==number (filtered too), speed, SQL.
- `mb.py tree | folders | perms | grant`: standard folder layout + folder-wise permission gaps/fix (permissions don't inherit).
- Speed goal tightened to ≤5s per card; deck slides 7–8, START-HERE, skills updated; 3 eval cases.

## 2026-09-25 — everyone uses their own logins
- `tools/setup.sh`: guided first-run setup. Each person enters their OWN Metabase API key and Superset login (hidden input); both are checked live; writes a private `tools/.env` (chmod 600) stamped `SETUP_BY=<their username>`.
- Every tool (Python and shell) refuses settings created by someone else, e.g. a copied `.env`.
- AGENTS.md: never ask for or accept credentials in chat. README, START-HERE, `.env.example` and deck slide 3 updated.

## 2026-09-25 — requirement sheets (Google Sheet / xlsx / csv)
- `tools/read_requirements.py`: reads every tab of a Google Sheet link (shared "anyone with link"), .xlsx or .csv → `requirements/<org>/<name>.md` (gitignored); stdlib only; title rows, blank columns and merged group cells handled; personal data masked (bare "Name" only when the tab is a people list).
- `templates/requirement-mapping.md`: every row → ✅ buildable / ❓ needs clarification / ⛔ not in data.
- AGENTS.md intake, avni-reporting skill, START-HERE step 1 and deck slide 4 now start from the sheet.

## 2026-09-25 — schema-first + no PII to the AI
- **Schema-first guard:** every SQL tool (`q.sh`, `mb.py run/create-card/set-sql`, `ss.py sqllab/set-dataset-sql`, `qa.py except-all`) refuses org schemas without a local `schemas/<schema>/CATALOG.md`.
- **PII masking:** query output is masked before the AI sees it (names, phones, Aadhaar/ABHA/bank IDs, DOB, addresses, GPS, staff names; phone/Aadhaar/email-shaped values in any column). Catalogue never lists values of PII columns.
- `.claude/settings.json` denies reading `.env`/keys and running raw `psql`/`pg_dump`.
- AGENTS.md golden rules 1–2, START-HERE "two rules", deck updated; 2 new eval cases.

## 2026-09-25 — v1
- Initial pack: 8 skills, 5 playbooks, SQL pattern library, tools (tunnel, schema dump + catalogue, Metabase/Superset clients, QA), templates, labs, evals, 8-slide session deck.
- Seeded from report builds and tickets across Durga India, Gubbachi, Sangwari, APF Odisha, JSS, Khel Mel, Goonj, Maitrayana, Ekam, JNPCT, Shelter, Shramik Bharti, ANT, Astitva, PHRII, Door Step School, Calcutta Kids, Mantrana, RWB.
