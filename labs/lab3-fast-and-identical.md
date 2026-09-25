# Lab 3 — Fast *and* identical (20 min)

You get this query (adapt the names to your practice schema's catalogue):

```sql
with latest as (                                      -- (A)
  select v.individual_id, v.encounter_date_time,
         row_number() over (partition by v.individual_id order by v.encounter_date_time desc) rn
  from <schema>.<encounter_table> v where v.is_voided = false
)
select a."Block", count(distinct i.id) as people
from <schema>.individual i
join <schema>.address a on a.id = i.address_id
left join latest l on l.individual_id = i.id and l.rn = 1
where i."<Multi-select column>" ilike '%<Answer>%'    -- (B)
group by 1;
```

## Tasks
1. **Find both bugs** with your agent (hint: `skills/report-performance` and trap #2 in `skills/avni-etl-data-model`).
   - (A) is a dead CTE: none of its columns reach the SELECT, yet it sorts the whole encounter table.
   - (B) matches `<Answer>, Other` and any answer whose name *contains* `<Answer>`. It also forgot `a.is_voided`.
2. Save the original as `old.sql`. Write `new.sql` without the dead CTE, **keeping (B) unchanged for now**.
3. Prove it: `python3 tools/qa.py except-all old.sql new.sql` → IDENTICAL. Compare the timings with `explain analyze`.
4. Now fix (B) with the `_coded` table (`sql/patterns/coded_multiselect.sql`) and explain *why* the counts change. This is a **correctness** change, so it gets a separate note to the client.

## Done when
- [ ] The performance rewrite is proven identical (0/0).
- [ ] The multi-select fix is explained with numbers (how many rows moved and why).
- [ ] You logged one learning with `tools/add_learning.py` (a real one from this lab, or "none new").
