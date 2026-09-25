# "The report doesn't match the app" — decision tree

Most of these are **definition differences**, not data bugs. Always answer with exact numbers ("App 1,964 = 1,851 enrolled + 113 registered-not-enrolled").

```
Report ≠ app
├─ 1. Voided?        count with/without is_voided=false on every joined table
├─ 2. Definition?    enrolled vs registered · active cohort vs all · attended vs roster ·
│                    app dashboard scoped to the user's catchment/address · distinct people vs visits
├─ 3. Timing?        ETL lag (~90 min) · replica lag · Metabase result cache · device not synced yet
├─ 4. Dates?         NULL encounter_date_time (scheduled) · cancelled visits · timezone (Asia/Kolkata) ·
│                    fiscal year vs calendar year · reflecting month vs visit month
├─ 5. Duplicates?    membership in 2 groups · double-entered forms · repeat enrolments → count(distinct)/DISTINCT ON
├─ 6. Stale schema?  renamed/_old/voided_ column · Metabase not synced · stale concept view
└─ 7. Scope?         test/voided cohorts · participants linked only to voided groups · org has 2 DBs (live vs stale)
```

## Handy reconciliation queries
```sql
-- OLTP vs ETL (same org) — separates "report scope" from "data missing"
-- (OLTP side needs set role; see skills/avni-etl-data-model/references/oltp-fallback.md)
select 'etl', count(*) from <schema>.individual where is_voided = false;
```
```sql
-- where did the difference go? bucket every app-side person by why the report excludes them
select case when e.id is null then 'not enrolled'
            when e.is_voided then 'enrolment voided'
            when g.member_subject_id is null then 'no active group'
            else 'in report' end as bucket, count(*)
from <schema>.individual i
left join <schema>.individual_<program> e on e.individual_id = i.id
left join (select distinct member_subject_id from <schema>.<group>_<member> where is_voided=false) g
       on g.member_subject_id = i.id
where i.is_voided = false
group by 1 order by 2 desc;
```

## Real examples
| Org | Report vs app | Explanation |
|---|---|---|
| Durga India | 1,851 vs 1,964 | Report counted enrolled only. Added an Enrollment Status filter (default Enrolled, All = app) |
| Khel Mel | 173 vs 200 (Raigarh) | Attendance-only report. Rebuilt roster-based with an Attendance Status filter |
| Durga India | participant gap | Participants linked only to voided/test cohorts |
| Maitrayana | 21,761 vs 21,525 | Donor slices double-counted people in several batches |
| Shelter | "not syncing" | Pipeline healthy. An orphan table from a voided form mapping looked stale |
| APF Odisha | block mismatch | Data-entry: records captured under a different block. No report change needed |
