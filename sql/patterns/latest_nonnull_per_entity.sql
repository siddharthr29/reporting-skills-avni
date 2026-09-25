-- PATTERN: latest NON-NULL value per measure, per entity
-- Use when: "current status", "latest weight", "recovered?" per child/mother.
-- Trap it avoids: taking the latest ROW — if the last visit left the field blank, the entity
-- looks "unknown/not recovered" (real bug: 0/0/1 was really 2/1/14).
-- Placeholders: <schema>, <encounter_table>, "<Measure A>", "<Measure B>"

with visits as (
  select e.individual_id,
         coalesce(e.encounter_date_time, e.earliest_visit_date_time) as d,
         e."<Measure A>" as a,
         e."<Measure B>" as b
  from <schema>.<encounter_table> e
  where e.is_voided = false
    and e.cancel_date_time is null
    and coalesce(e.encounter_date_time, e.earliest_visit_date_time) is not null
)
select individual_id,
       (array_agg(a order by d desc) filter (where a is not null))[1] as latest_a,
       (array_agg(b order by d desc) filter (where b is not null))[1] as latest_b,
       max(d) as last_visit
from visits
group by individual_id;
