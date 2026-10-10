-- PATTERN: per-answer logic on a MULTI-SELECT using the <table>_coded EAV table
-- Use when: "sessions whose topics are ONLY baseline/endline", "has answer X", counting each answer.
-- Trap it avoids: ILIKE on comma-joined text ('Baseline, Other' matched '%Baseline%').
-- CAUTION — labels that contain commas: at PHRII (2026-09-28) the _coded table SPLIT
-- 'Other Group A (31, 33, 52, 58)' into four answers. Check first:
--   select distinct answer from <schema>.<table>_coded where answer not in (select name from public.concept);
-- Any rows → match whole labels on the main text column instead:
--   ', ' || t."<Concept>" || ', ' LIKE '%, <label from concept_answer>, %'
-- The _coded table has one row per selected answer: (id, concept_name, answer).

-- A) entities whose answers are ALL within a set  → e.g. exclude pure-baseline sessions
with only_admin as (
  select c.id
  from <schema>.<table>_coded c
  where c.concept_name = '<Concept>'
  group by c.id
  having bool_and(c.answer in ('Baseline','Endline','Graduation Day'))
)
select count(*) from <schema>.<table> s
where s.is_voided = false and s.id not in (select id from only_admin);

-- B) count of entities per answer (each answer counted once per entity)
select c.answer, count(distinct c.id)
from <schema>.<table>_coded c
join <schema>.<table> s on s.id = c.id and s.is_voided = false
where c.concept_name = '<Concept>'
group by 1 order by 2 desc;
