# Metabase filters — the recipes that work

## 1. Searchable dropdown (the "two-level" recipe)

A filter renders as a **free-text box** unless both levels are set. Proven on Metabase v0.60.

**Dashboard parameter** (in `PUT /api/dashboard/<id>` → `parameters[]`):
```json
{"id":"<dash_param_id>","name":"Block","slug":"block","type":"string/=",
 "values_query_type":"list",
 "values_source_type":"card",
 "values_source_config":{"card_id":<VALUES_CARD_ID>,"value_field":["field","Block",{"base-type":"type/Text"}]}}
```
Date parameters: leave `values_query_type` unset so they keep the calendar picker.

**Card template tag** (kebab-case, inside `native.template-tags`):
```json
"block":{"id":"<existing tag id>","name":"block","display-name":"Block","type":"text",
  "values-query-type":"list","values-source-type":"card",
  "values-source-config":{"card_id":<VALUES_CARD_ID>,"value_field":["field","Block",{"base-type":"type/Text"}]}}
```
**Card `parameters[]`** (snake_case, same content): `values_query_type`, `values_source_type`, `values_source_config`.
The question page reads the **tag**, and the values API reads **`parameters[]`**. Set both.

Static lists: `"values_source_type":"static-list","values_source_config":{"values":["Today","This Week"]}`.

**Values card** (`(filter values) Block`): `select distinct "Block" from <schema>.address where is_voided=false and "Block" is not null and "Block" not ilike '%voided%' order by 1`. Reuse it by name, never create duplicates.

The widget still shows a "T" icon, but it opens a searchable list. That's expected.

## 2. Wiring a filter to a card on a dashboard
`dashcards[].parameter_mappings`:
```json
{"parameter_id":"<dash_param_id>","card_id":<CARD_ID>,"target":["variable",["template-tag","block"]]}
```
**Audit:** every visible dashboard filter must be mapped on every card it should affect. A card without that tag **silently ignores** the filter, which is a classic "filter doesn't change this number" ticket. Intentionally unmapped filters (e.g. Grade on a staff card) go in the card description.

## 3. Quick-period filter (Today / This Week / Month / Quarter / Year)
```sql
[[ and d >= case {{period}}
      when 'Today'        then current_date
      when 'This Week'    then date_trunc('week',   current_date)::date
      when 'This Month'   then date_trunc('month',  current_date)::date
      when 'This Quarter' then date_trunc('quarter',current_date)::date
      when 'This Year'    then date_trunc('year',   current_date)::date end ]]
```
Tag type `text` + static-list values.

## 4. Multi-select column "contains" filter
```sql
[[ and {{facilitator}} in (select trim(x) from unnest(string_to_array(s."Facilitator", ',')) x) ]]
```
Only safe when no answer contains a comma. Otherwise filter through the `_coded` table.

## 5. Required filter with a default
Use a default when the app's number and the report's number differ by definition, e.g. `enrollment_status` default `Enrolled` (with `All` matching the app's count). Set `"required":true,"default":"Enrolled"` on both the tag and the parameter.

## 6. Filters that must not drop people
Put date and month filters **inside the activity CTE**, not on the final roster join. Otherwise people with no activity in the range vanish instead of showing 0.

## 7. Filters Metabase can't offer
- New column/table not in the field picker → `sync_schema`. New values missing from the dropdown → `rescan_values`.
- Field filter on a schema Metabase didn't register → use a plain variable or a Model.
- A filter the client wants but the data doesn't capture (e.g. "screening done") → say so. Don't fake it.
