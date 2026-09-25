# Lab 1 — solution sketch

```sql
with base as (
  select i.id, a."Block"
  from <schema>.individual i
  join <schema>.address a on a.id = i.address_id and a.is_voided = false
  where i.is_voided = false
  [[ and a."Block" = {{block}} ]]
  [[ and i.registration_date >= {{start_date}} ]]
  [[ and i.registration_date <= {{end_date}} ]]
)
select coalesce("Block", '(No block)') as "Block", count(distinct id) as "Registered"
from base group by 1 order by 2 desc;
```

Values card `(filter values) Block`:
```sql
select distinct a."Block" from <schema>.address a
where a.is_voided = false and a."Block" is not null and a."Block" not ilike '%voided%' order by 1;
```

Then, in order:
- **Tag** `block`: `values-query-type: list`, `values-source-type: card`, `values-source-config: {card_id, value_field}`.
- **Card `parameters[]`**: the same in snake_case.
- **Dashboard parameter**: `values_query_type: list`, plus the same source.
- **`parameter_mappings`** target: `["variable",["template-tag","block"]]`.

Common mistakes: only setting the dashboard level (the card page is still free text); forgetting `a.is_voided`; `count(*)` instead of `count(distinct id)`.
