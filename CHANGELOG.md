# Changelog

Curated learnings are recorded here when they move from `LEARNINGS.md` into the skills.

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
