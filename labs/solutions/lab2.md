# Lab 2 — solution sketch

Metric:
```sql
with roster as (select i.id, a."Block" from <schema>.individual i
                join <schema>.address a on a.id = i.address_id and a.is_voided = false
                where i.is_voided = false [[ and a."Block" = {{block}} ]]),
last_visit as (select individual_id, max(encounter_date_time) d from <schema>.<encounter_table>
               where is_voided = false and encounter_date_time is not null group by 1)
select count(*) from roster r left join last_visit v on v.individual_id = r.id
where v.d is null or v.d < current_date - 30;
```
Drill `(drill) [NOVISIT30] People with no visit in 30 days`: the **same CTEs and the same WHERE**, selecting `r.id, name, "Block", v.d as last_visit … limit 2000`.

Click behaviour on the metric dashcard:
```json
{"type":"link","linkType":"question","targetId":<DRILL_ID>,
 "parameterMapping":{"<block_param_id>":{"id":"<block_param_id>",
   "source":{"type":"parameter","id":"<block_param_id>","name":"Block"},
   "target":{"type":"variable","id":"block"}}}}
```
Root cause of the original bug: the click target was a shared list with no metric condition, so it could never equal the metric.
