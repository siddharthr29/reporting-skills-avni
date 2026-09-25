# Lab 3 — solution sketch

**Performance (identical output):** delete CTE `latest` and its `left join`. They contribute no selected column, and the left join on `rn = 1` never changes the row count. `qa.py except-all` → `old_rows = new_rows`, `0 / 0`. `explain analyze` loses the Sort over the whole encounter table.

**Correctness (different output, on purpose):**
```sql
... where exists (select 1 from <schema>.individual_coded c
                  where c.id = i.id and c.concept_name = '<Concept>' and c.answer = '<Answer>')
    and a.is_voided = false
```
Explain the change with numbers: "N people were counted because another answer contained the text '<Answer>' (e.g. '<Answer>, Other'); M voided addresses were included."

Learning to log (example): `--type pitfall --tool sql --title "ILIKE on multi-select matches substrings"` if your org's catalogue showed a new variant of it.
