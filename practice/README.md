# Practice: Durga India requirement sheet (SRS)

> ## ⚠ Disclaimer: practice only
> This sheet, and everything you build from it, is **only for learning**.
> - Build **only** in your own practice folder in Metabase (e.g. `Practice — <your name>`).
> - **Never** create, edit, move, rename or delete anything in an **original client report**, dashboard or folder. That includes Durga India and every other organisation.
> - Use the **UAT (test) data**, schema `durga_uat`. Use `durga_india` only if your lead says so, and still only in your practice folder.
> - If you're unsure whether something is a client report, **stop and ask your lead**.

## What's here
| File | What it is |
|---|---|
| `durga-india-practice-srs.xlsx` | The requirement sheet, in the same format clients send: READ ME, Requirements (14 rows), Dashboards, Filters |
| `durga-india-practice-srs.csv` | The Requirements tab as CSV |
| `FACILITATOR-NOTES.md` | Expected answers and traps for the trainer. **Try first, peek later.** |

These practice reports are **different** from the Durga India reports already delivered to the client (Cohort, Participant, Observation, Comms, Complete, Session Assessment, Cohort and Participant Attendance). You won't be copying existing work.

## How to use it (hands-on)
1. Set up once: `./tools/setup.sh`, then `./tools/tunnel.sh up` (see `START-HERE.md`).
2. Open Claude in the repo folder and paste:
   ```
   Read AGENTS.md. This is PRACTICE. Here is the requirement sheet for Durga India practice (schema durga_uat): practice/durga-india-practice-srs.xlsx. Read every tab and show me each requirement marked buildable, needs clarification, or not in the data.
   ```
3. Build **P01** first, following the 5 steps in `START-HERE.md`. Then pick any 2 more.
4. Treat **P13** and **P14** like real client rows: decide what to ask the client.
5. Done when the **Definition of done** is all ✅ for each report you built.

## Metabase note
The "Durga India" Metabase database only reads the client's live schema. An admin needs to add a **Durga India UAT** database so Metabase practice can use test data. Until then, explore and check numbers on `durga_uat` through the tunnel, and build in your practice folder only as your lead directs.
