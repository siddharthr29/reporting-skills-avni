-- PATTERN: resolve concept UUIDs (reasons, coded jsonb answers) without killing performance
-- Trap it avoids: correlated per-row subquery on public.concept (huge, cross-org): 41s → 0.7s,
-- and a >120s timeout → 1.3s.

with rc as materialized (
  select uuid, name
  from public.concept
  where uuid in ('<uuid-1>', '<uuid-2>', '<uuid-3>')      -- only the ones the form can emit
),
marks as (
  select a.id, a.student_id, r.uuid as reason_uuid
  from <schema>.attendance_record a
  cross join lateral unnest(a.reason_concept_uuids) as r(uuid)   -- or jsonb_array_elements_text
  where a.is_voided = false
)
select m.student_id, string_agg(rc.name, ', ' order by rc.name) as reasons
from marks m
join rc on rc.uuid = m.reason_uuid
group by 1;

-- General rule: a heavy multi-CTE with a small outer query → add AS MATERIALIZED
-- (Postgres otherwise may inline and re-run it per row: 103s → 1.1s).
