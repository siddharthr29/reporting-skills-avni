-- PATTERN: resolve a JSON array of subject UUIDs (attendance lists, student pickers) to names
-- Stored as text like '["uuid1","uuid2"]'. Never show raw UUIDs in output.

select s.id as session_id,
       st.id as student_id,
       concat_ws(' ', st.first_name, st.last_name) as student
from <schema>.<session_encounter> s
cross join lateral jsonb_array_elements_text(s."<Students present>"::jsonb) as u(uuid)
join <schema>.<student_subject> st on st.uuid = u.uuid and st.is_voided = false
where s.is_voided = false
  and s."<Students present>" ~ '^\s*\['          -- guard: only rows holding a JSON array
;
-- Cheap existence check (one student): s."<Students present>" ilike '%' || st.uuid || '%'
