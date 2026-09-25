# Reading OLTP (public) safely — only when ETL doesn't have it yet

Use this for: a concept added to a form that ETL hasn't flattened yet, checklists or immunisations (no ETL equivalent), or reconciling "app vs report".

## Always scope with RLS
```sql
begin transaction read only;
set role "<org_db_user>";          -- RLS scopes public tables to this org
set search_path to public;         -- otherwise unqualified names hit the ETL schema
select count(*) from individual where is_voided = false;
commit;
```
Find the role: `select name, schema_name, db_user from public.organisation where name ilike '%<org>%';` (run with `reset role`). Always double-quote it.

## Reading an observation
```sql
select i.id, i.observations ->> '<concept_uuid>' as value
from public.individual i
where i.is_voided = false and i.observations ? '<concept_uuid>';
```
Coded answers in jsonb are **concept UUIDs**. Resolve them with a **materialised** lookup of just the UUIDs you need:
```sql
with c as materialized (
  select uuid, name from public.concept where uuid in ('<uuid1>','<uuid2>')
)
select ... join c on c.uuid = i.observations ->> '<concept_uuid>';
```

## Performance
`public.*_view` reporting views and `public.concept`, `entity_approval_status`, `checklist*` are **cross-org and huge**. Never correlate per row against them. Materialise a small lookup first, or rewrite on the ETL schema. One rewrite took a 74s count down to 1s.

## Switch back
Once `CATALOG.md` shows the new column in the ETL table, replace the jsonb read with the flat column and note it in the card description.
