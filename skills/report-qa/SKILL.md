---
name: report-qa
description: Verification checklist and methods to prove an Avni report is correct before handover or before replying to a ticket — metric equals drill count, identities, EXCEPT ALL diffs, UUID-leak scan, tool-vs-tunnel checks, app reconciliation, timing, backups. Use before saying "done".
---

# Report QA — prove it, then claim it

A reply to a client may only claim what one of these checks proved.
Every check here works on **counts and masked output**. You never need to read a person's name to verify a report.

## Fastest path
```bash
python3 tools/qa.py audit-dash <DASH_ID>                        # dropdowns, wiring, clickable, drill==number, speed, SQL
python3 tools/qa.py audit-dash <DASH_ID> --param village=<v>    # same, with a filter applied
python3 tools/mb.py tree <ORG_FOLDER_ID>; python3 tools/mb.py perms <ORG_FOLDER_ID>
```
Then report the **Definition of done** table from `AGENTS.md` as ✅/❌.

## The checklist (run all that apply)

| # | Check | How | Pass |
|---|---|---|---|
| 1 | **Runs through the tool** | `mb.py run <card>` / Superset SQL Lab execute | no error, rows > 0 (or explained 0) |
| 2 | **Metric == drill** | For every clickable number and every bar segment, count the drill card's rows under the same filters | equal (or a documented reason: >2,000 cap, people vs visits) |
| 3 | **Identities** | M + F + Other = Total, Open + Pending + Resolved = Created, sum of slices = total distinct | exact |
| 4 | **Filters really filter** | Set each dashboard filter and watch every card change (or be documented as unmapped) | all mapped cards react |
| 5 | **Dropdowns are lists** | Open each filter on the dashboard **and** on the card page | searchable list, no voided values |
| 6 | **No UUID leakage** | `tools/qa.py uuid-scan <card>`: regex `[0-9a-f]{8}-[0-9a-f]{4}-` over all output cells | 0 hits |
| 7 | **Same data after a rewrite** | `tools/qa.py except-all old.sql new.sql` | row counts equal, both diffs 0 |
| 8 | **Tool == tunnel == truth** | Same count via the Metabase/Superset API and via the read-only tunnel | equal (replica lag aside) |
| 9 | **Report vs app** | Reconcile against the app's number. Explain any gap with a definition (enrolled vs registered, voided, ETL lag) | explained to the row |
| 10 | **Speed** | Cold and warm timing through the tool | <30s target; hard limits 60s (Superset) and ~120s (Metabase) |
| 11 | **Backups exist** | `backups/` has the pre-change JSON of every object you PUT | yes |
| 12 | **Links unchanged** | Same card/dashboard IDs as before (patched in place) | yes |

## Useful SQL
```sql
-- identity: gender split adds up
select count(*) filter (where g='Male') + count(*) filter (where g='Female')
     + count(*) filter (where g not in ('Male','Female') or g is null) = count(*) as ok
from (select coalesce(gender,'(none)') g from base) t;
```
```sql
-- both present after an attendance fix (not silently all-Absent)
select status, count(*) from attendance_drill group by 1;
```

## Row-level reconciliation against a client export
Load their CSV, join on the natural key, and split rows into **match / only in client file / only in Avni**. Report the three counts plus examples, not a single "doesn't match".

## Before the reply
- State the number and **how it was verified** ("metric 41, drill 41 rows; tested with Block = X").
- Mention anything you saw but didn't change.
- Use `templates/client-reply.md`.
