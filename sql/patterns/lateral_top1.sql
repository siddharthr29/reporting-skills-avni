-- PATTERN: latest visit per entity via LATERAL top-1 (uses the existing individual_id index)
-- Use instead of row_number() over a whole multi-million-row table (2–5 min → ~9s).
-- FIRST check whether the latest-visit columns are even selected — if not, delete the CTE (0.8s).

select i.id, i.first_name, lv.encounter_date_time, lv."<Weight>"
from <schema>.individual i
join <schema>.individual_<program> enl on enl.individual_id = i.id and enl.is_voided = false
left join lateral (
  select g.encounter_date_time, g."<Weight>"
  from <schema>.<program_encounter_table> g
  where g.individual_id = i.id
    and g.is_voided = false
    and g.encounter_date_time is not null
  order by g.encounter_date_time desc nulls last, g.id desc     -- id = deterministic tiebreak
  limit 1
) lv on true
where i.is_voided = false;
