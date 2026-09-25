---
name: report-learnings
description: The self-improvement loop for this skill pack. After every Avni reporting task (build, change, debug), capture what was learned into LEARNINGS.md with tools/add_learning.py; periodically curate repeated learnings into the skills, playbooks and SQL patterns. Use at the end of every task, and when asked to "curate" or "update the skills".
---

# Keep learning: capture → curate → promote

This repo is meant to get smarter every time anyone (human or agent) builds or fixes a report.
**Every task ends with a learning check.** If something was new, surprising, or cost more than ~15 minutes, record it.

## 1. Capture (every task, 1 minute)

Ask yourself:
- Did a symptom lead somewhere not already in `playbooks/`?
- Did a column, table, API shape or tool behave differently than a skill says?
- Did a skill give **wrong** advice? (Record it as a *correction*. These are the most valuable.)
- Is there an org-specific fact the next person needs (live DB vs stale DB, prod schema name, odd address columns)?

If yes, append the learning:
```bash
python3 tools/add_learning.py \
  --type pitfall|fix|pattern|correction|org-fact|tool-behaviour \
  --tool metabase|superset|jasper|sql|etl|process \
  --org "<org name or ->" \
  --title "Drill showed all rows because tag target was type:parameter" \
  --symptom "Clicking a bar opened the full line list" \
  --cause "click_behavior target used type:parameter instead of variable" \
  --fix "target {type:variable, id:<tag slug>}; verified metric==drill for 12 segments" \
  --source "ticket <number> / session <date>"
```
The script appends to `LEARNINGS.md`, stamps the date, and **refuses to write** if the safety scanner finds a secret, email, internal host or numeric DB/card id. Use placeholders (`<DB_ID>`).

No shell? Edit `LEARNINGS.md` directly using the same block format, then run `scripts/check_public_safety.sh`.

## 2. Curate (weekly, or when the inbox has 5+ entries)

For each entry in `LEARNINGS.md`, choose one:
| Situation | Action |
|---|---|
| Duplicates something in a skill or playbook | Delete the entry and add its extra detail to the existing line |
| A new symptom → fix | Add a row to `playbooks/filter-issues.md` / `drilldown-issues.md` / `count-mismatch.md` |
| A reusable SQL shape | Add a `sql/patterns/*.sql` file with a header comment |
| A rule that prevents a class of bugs | Add it to the relevant `skills/*/SKILL.md` (keep each SKILL.md short; move detail to `references/`) |
| **Correction** | Fix the wrong text in the skill **first**, then add an eval case in `evals/cases/` so it can't regress |
| An org-specific fact | Add it to `playbooks/case-studies.md` (org section) |

Then remove the promoted entries from `LEARNINGS.md` and note them in `CHANGELOG.md` under today's date.
In Claude Code, `/curate` walks through this.

## 3. Share
Open a PR (branch `learn/<short-topic>`). CI runs the safety scan, frontmatter lint and evals checks. One learning per commit is fine.

## Rules
- A learning is **one observed fact + evidence** ("verified on 12 segments"), not an opinion.
- Never paste client data, names, emails, credentials, raw IDs or query results.
- Prefer fixing an existing sentence over adding a new one. The pack must stay small enough to read.
