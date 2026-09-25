-- PATTERN: roster-based report (everyone registered shows up, even with no activity)
-- Trap it avoids: INNER JOIN to activity → only active people (173 shown vs 200 registered).
-- Put date filters INSIDE the activity CTE, never on the outer join.

with roster as (
  select i.id, concat_ws(' ', i.first_name, i.last_name) as name, a."District", a."Block"
  from <schema>.individual i
  join <schema>.address a on a.id = i.address_id and a.is_voided = false
  where i.is_voided = false
  [[ and a."Block" = {{block}} ]]
),
activity as (
  select e.individual_id, count(*) as sessions
  from <schema>.<encounter_table> e
  where e.is_voided = false and e.encounter_date_time is not null
  [[ and e.encounter_date_time >= {{start_date}} ]]
  [[ and e.encounter_date_time <  {{end_date}} + 1 ]]
  group by 1
)
select r.*, coalesce(a.sessions, 0) as sessions,
       case when a.sessions is null then 'Not attended' else 'Attended' end as "Attendance Status"
from roster r
left join activity a on a.individual_id = r.id
where 1 = 1
[[ and case when a.sessions is null then 'Not attended' else 'Attended' end = {{attendance_status}} ]]
order by r."Block", r.name
limit 2000;
