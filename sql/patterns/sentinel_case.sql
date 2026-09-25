-- PATTERN: NULL-safe categories shared by metric AND drill (so counts match and bars are clickable)
-- Use the SAME expression in the metric card and in its drill card.

select case
         when e."<Field>" is null or trim(e."<Field>") = '' then '(Not collected yet)'
         else e."<Field>"
       end as category,
       count(distinct e.individual_id) as people
from <schema>.<encounter_table> e
where e.is_voided = false
group by 1
order by 2 desc;

-- Numeric bands (e.g. haemoglobin):
--   case when hb is null then '(Not collected yet)'
--        when hb < 7 then 'Severe (<7)' when hb < 10 then 'Moderate (7–9.9)'
--        when hb < 11 then 'Mild (10–10.9)' else 'Normal (≥11)' end
-- Text that should be numeric: case when x ~ '^[0-9.]+$' then x::numeric end
