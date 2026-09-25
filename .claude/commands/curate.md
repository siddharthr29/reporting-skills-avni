---
description: Promote LEARNINGS.md entries into skills, playbooks, SQL patterns and evals; then clear the inbox
---

Follow `skills/report-learnings/SKILL.md` §2 (Curate).

For each entry between `<!-- LEARNINGS START -->` and `<!-- LEARNINGS END -->` in `LEARNINGS.md`:
1. Decide where it belongs (duplicate / playbook row / SQL pattern / skill rule / correction → fix + eval / org fact).
2. Make the edit. Keep SKILL.md files short and push detail to `references/`.
3. For **corrections**, fix the wrong text and add an `evals/cases/<slug>.json` case.
4. Remove the entry from the inbox and add a line under today's date in `CHANGELOG.md`.
5. Run `scripts/check_public_safety.sh` and `python3 scripts/lint_skills.py`. Both must pass.
6. Summarise the changes as a PR description (branch `learn/<topic>`). Don't push unless asked.
