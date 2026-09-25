# Facilitator notes: Durga India practice SRS

**Trainees: try first, peek later.** Numbers are from `durga_uat` on 25 Sep 2026 (they will drift as test data changes).

| Req | Expected status | The trap it teaches | Pattern / skill | Check |
|---|---|---|---|---|
| P01 Participants by location | ✅ | Voided rows. Location lives on the address (`address."City"`), not the participant | base CTE + dropdown recipe + per-metric drill | total ≈ 1,044. Sum of locations = total. Drill = number |
| P02 Registrations over time | ✅ | Months with 0 must still show | `sql/patterns/generate_series_trend.sql` | Apr–Sep 2026 present |
| P03 Age groups | ✅ | Age from DOB. "Unknown" bucket for blanks | sentinel CASE | groups add up to total |
| P04 Education profile | ✅ | ~87% blank in UAT. Show "Not collected yet", don't drop | `sql/patterns/sentinel_case.sql` | blanks bucket is the largest |
| P05 Cohort status | ❓ then ✅ | **10 cohorts have no status.** Ask: show them as "Not set"? | sentinel CASE | On-Going 62 · Completed 54 · Dropped 3 · blank 10 |
| P06 Sessions per month | ✅ | "Conducted" = has date AND not cancelled. Engagement Type is on the cohort | join session → cohort | 143 conducted in total |
| P07 Topic coverage | ✅ | **Multi-select.** Use `cohort_session_details_coded` (concept 'Topic'), never `ILIKE` | `sql/patterns/coded_multiselect.sql` | top: Power and Control 20 |
| P08 Facilitator workload | ✅ | Multi-select again (concept 'Facilitator'). A session counts for each facilitator | coded EAV | sum over facilitators ≥ sessions (expected) |
| P09 Average session length | ✅ (hard) | Duration text `PT1H30M` and variants (`PT02H00M`, blanks) | regex parse (see Durga case study) | no negative or absurd minutes |
| P10 Donor reach | ❓ then ✅ | Donor is on the cohort. **66 cohorts have no donor.** Count distinct people | `sql/patterns/membership_distinct_on.sql` | a person in 2 same-donor cohorts counts once |
| P11 Inactive cohorts | ✅ | NOT EXISTS / LEFT JOIN. On-Going only | roster-style | ≈ 60 on-going cohorts with no session in 30 days |
| P12 Approval status | ✅ | Cohorts can have **several submissions**. Use the latest per cohort. Include "Not submitted" | `DISTINCT ON` latest per entity | Approved 25 · Pending 23 · Rejected 6 · Not submitted 75 |
| P13 Active participants | ❓ | **Deliberately ambiguous**: status field? attended recently? in an on-going cohort? | intake: ask the client | trainee must NOT guess |
| P14 Job placement | ⛔ | **Not captured** in any form | honest "not in the data" + nearest field | trainee must NOT fake it |

## What to watch for in the room
- Skipping the ✅/❓/⛔ table and building straight away.
- Building outside the practice folder. Stop them immediately.
- Using `ILIKE` on Topic or Facilitator (P07, P08).
- Not clicking through to compare the drill-down count (P01, P11).
