-- PATTERN: monthly trend that shows zero months (instead of skipping them)

with months as (
  select generate_series(date_trunc('month', coalesce({{start_date}}, current_date - interval '11 months')),
                         date_trunc('month', coalesce({{end_date}},   current_date)),
                         interval '1 month')::date as m
),
counts as (
  select date_trunc('month', e.encounter_date_time at time zone 'Asia/Kolkata')::date as m,
         count(*) as n
  from <schema>.<encounter_table> e
  where e.is_voided = false and e.encounter_date_time is not null
  group by 1
)
select to_char(months.m, 'Mon YYYY') as "Month", coalesce(counts.n, 0) as "Visits"
from months left join counts using (m)
order by months.m;
-- Note: {{start_date}}/{{end_date}} as REQUIRED date tags here (no [[ ]]), or hard-code a window.
