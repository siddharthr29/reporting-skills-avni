-- PATTERN: Metabase "Quick period" dropdown + explicit date range, both optional
-- Tag {{period}}: type text, static-list values [Today, This Week, This Month, This Quarter, This Year]
-- Tags {{start_date}}, {{end_date}}: type date

select count(*)
from <schema>.<encounter_table> e
where e.is_voided = false and e.encounter_date_time is not null
[[ and e.encounter_date_time >= {{start_date}} ]]
[[ and e.encounter_date_time <  {{end_date}} + 1 ]]
[[ and (e.encounter_date_time at time zone 'Asia/Kolkata')::date >= case {{period}}
      when 'Today'        then current_date
      when 'This Week'    then date_trunc('week',    current_date)::date
      when 'This Month'   then date_trunc('month',   current_date)::date
      when 'This Quarter' then date_trunc('quarter', current_date)::date
      when 'This Year'    then date_trunc('year',    current_date)::date end ]];
