# ETL health — is the report data fresh and complete?

Read these global bookkeeping tables in `public` (no `set role` needed; never read org subject data this way).

## Is ETL enabled, and how fresh?
```sql
select schema_name,
       count(*)                                          as etl_tables,
       max(last_sync_time)                               as latest_sync,
       now() - max(last_sync_time)                       as lag,
       count(*) filter (where sync_status <> 'Success')  as non_success
from public.entity_sync_status
where schema_name = '<schema>'
group by schema_name;
-- no rows            → ETL not enabled for the org
-- lag >> 90 min      → ETL stalled; check the job log
-- non_success > 0    → a run failed; check the job log
```

## Which tables are behind?
```sql
select tm.name as etl_table, ess.last_sync_time, ess.sync_status
from public.entity_sync_status ess
join public.table_metadata tm on tm.id = ess.table_metadata_id
where ess.schema_name = '<schema>'
order by ess.last_sync_time asc
limit 20;
```
An old `last_sync_time` + `Success` + **0 rows** in the table = an **orphan table** from a voided form mapping. Find which table actually receives the new rows before calling it an ETL failure.

## A field disappeared after a form change?
```sql
select cm.name, cm.original_column_name
from public.column_metadata cm
join public.table_metadata tm on tm.id = cm.table_metadata_id
where tm.schema_name = '<schema>' and (cm.name like '%\_old' or cm.name like 'voided\_%');
```

## Job log (stack traces)
`GET <avni-origin>/etl/job/<orgUUID>` with a super-admin auth token. Replace `\n\t` with newlines to read it.

## Forcing a run / recreating (admin action, not from a reporting session)
- Run now: disable then re-enable ETL for the org (reschedules within seconds).
- Recreate a broken schema: disable ETL → `select delete_etl_metadata_for_schema('<schema>','<db_user>','<db_owner>');` → re-enable. The next run rebuilds it.

## The "not syncing to Metabase" diagnosis order
1. `entity_sync_status` fresh and `Success`?
2. Read-replica lag (compare `max(last_modified_date_time)` on OLTP vs ETL).
3. Is there new OLTP activity at all (did the field team sync their devices)?
4. ETL row counts for the table.
5. ETL tables == Metabase's known tables (`sync_schema` if not).
6. Metabase query cache. Re-run with the cache off.
7. Device sync telemetry (`public.sync_telemetry`) if users say "I submitted it".

## After a rule/form fix
Devices only run the fixed rule **after they sync**. Judge by `error_date_time` joined to `sync_telemetry`, not `created_date_time`.
