-- PATTERN: one row per member, from group membership (class, cohort, batch, phulwari)
-- Use when: attributing a person to a group attribute (donor, program, class).
-- Trap it avoids: a person in 2 groups counted twice (251 vs 249; 21,761 vs 21,525).
-- For "people who LEFT" metrics drop the is_voided filter on the link (exit voids the link).

with membership as (
  select distinct on (gs.member_subject_id)
         gs.member_subject_id as person_id,
         gs.group_subject_id  as group_id
  from <schema>.<group>_<member> gs            -- or public.group_subject scoped to the org
  where gs.is_voided = false                   -- REMOVE for dropout/exit metrics
  order by gs.member_subject_id, gs.id desc    -- latest link wins
)
select g."<Group attribute>" as attribute, count(*) as people
from membership m
join <schema>.<group> g on g.id = m.group_id and g.is_voided = false
group by 1
order by 2 desc;
