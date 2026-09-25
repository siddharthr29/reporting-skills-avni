# Requirement intake — ask once, build once

Fill this with the requester **before writing SQL**. Every blank here turns into a rework loop later.

**Org:** ______  **ETL schema:** ______  **Tool:** Metabase / Superset / Jasper
**New report or change to:** <link> ______  **Target collection / dashboard:** ______
**Ticket:** ______ (read the *whole* thread + every attachment)

## 1. The question
One sentence the report answers: ______________________________________

## 2. Grain
One row per: ☐ person ☐ enrolment ☐ visit/encounter ☐ session ☐ attendance mark ☐ other ____
Roster-based (everyone registered, even with no activity)? ☐ yes ☐ no

## 3. Metrics (one line each)
| Metric (client's words) | Numerator in data terms | Denominator / scope | Distinct what? | Target? |
|---|---|---|---|---|
| | | | | |

Tricky definitions to confirm explicitly:
☐ enrolled vs registered ☐ active vs all (voided/exited) ☐ latest visit vs any visit ☐ calendar vs fiscal year ☐ visit month vs "reflecting month" field

## 4. Filters
| Filter | Dropdown / free text / date | Values from | Default | Required? |
|---|---|---|---|---|
| | | | | |

## 5. Drill-downs
Which numbers must be clickable? What does the drilled list show (columns, order)?

## 6. Columns & order (line lists)
Paste the client's order sheet. It is the source of truth.

## 7. Out of scope / not captured in the data
(e.g. "Screening done" isn't a field. Agree the closest real field.)

## 8. Sign-off
Who verifies, against what (app screen, their Excel, last month's report)?
