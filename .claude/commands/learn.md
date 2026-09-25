---
description: Capture what this session learned about Avni reporting into LEARNINGS.md (safety-scanned)
argument-hint: [optional: what to record]
---

Follow `skills/report-learnings/SKILL.md` §1 (Capture).

1. Review this session: which symptoms, causes, fixes, tool behaviours or skill **corrections** were new compared to `skills/`, `playbooks/` and `LEARNINGS.md`? Grep them before adding, and don't duplicate.
2. For each genuinely new item (usually 0–3), run `python3 tools/add_learning.py …` with type/tool/org/title/symptom/cause/fix/source. Use placeholders for any ID, and no names/emails/data.
3. If the script refuses (safety scan), rewrite the entry without the flagged text and retry.
4. Report what you added in one line each. If nothing was new, say so.

$ARGUMENTS
