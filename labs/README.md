# Hands-on labs

> Want a full client-style exercise? Use the practice requirement sheet in [`practice/`](../practice/): 14 rows, Durga India UAT data. **Practice only: never change an original client report.**

Do these with your AI agent open in this repo. Use a **practice/UAT schema** your trainer gives you (`<practice_schema>`, e.g. an org's `*_uat` schema) and a **practice collection** in Metabase. Never practise on a client's live dashboard.

| Lab | Time | You'll learn | Solution |
|---|---|---|---|
| [Lab 1 — First filtered card](lab1-first-card.md) | 20 min | tunnel, schema dump, catalogue grep, base-CTE card, dropdown filter recipe | `solutions/lab1.md` |
| [Lab 2 — Fix a drill-down](lab2-fix-drill.md) | 20 min | per-metric drill, click behaviour, metric == drill proof | `solutions/lab2.md` |
| [Lab 3 — Fast *and* identical](lab3-fast-and-identical.md) | 20 min | multi-select trap, dead CTE, `EXCEPT ALL` proof | `solutions/lab3.md` |

Ground rules for every lab: the read-only tunnel only, dry-run before `--apply`, and end with `/learn` (or `tools/add_learning.py`) if you discovered anything new.
