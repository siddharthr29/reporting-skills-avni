# Filter issues — symptom → cause → fix

Recipes are in `skills/metabase-reports/references/filters.md` (Metabase) and `skills/superset-reports/SKILL.md` (Superset).

| # | Symptom | Root cause | Fix | Verify | Seen at |
|---|---|---|---|---|---|
| F1 | Dropdown is a **free-text box** on the dashboard | Dashboard parameter lacks `values_query_type:"list"` | Set it + `values_source_type/config` on the dashboard parameter | Open the filter: a searchable list appears | Gubbachi |
| F2 | Dropdown works on the dashboard but is **free text on the card page** | Only `card.parameters[]` set; the question page reads the **template tag** | Set kebab-case `values-query-type/values-source-*` on the tag **and** snake_case on `parameters[]` | Open the card itself | Gubbachi, Sangwari, Durga, DSS, ANT, Astitva |
| F3 | Dropdown lists deleted items (`AKN (voided~…)`) | Values card doesn't exclude voided | `where is_voided=false and col not ilike '%voided%'` in the values card | List shows only live values | Gubbachi |
| F4 | Changing a filter **doesn't change some cards** | Those cards lack the tag / `parameter_mappings` (silently ignored) | Add the tag + mapping to every card that should react. Document intentional exceptions | Set the filter; every mapped card changes | Gubbachi |
| F5 | Class/program filters never match **dropouts** | Exit voids the membership link; the filter joins `is_voided=false` links | For "left" metrics take the latest link regardless of voided (`DISTINCT ON`) | Dropout count unchanged by an unrelated filter | Gubbachi |
| F6 | A district/area **disappears** when filtering (e.g. Singrauli, half of Anuppur) | The filter options came from a **stale concept view** that was INNER-joined | Drop the stale view, filter on the real subject table, remap the field-filter dimension to the new field id | Per-district counts before = after | JSS Phulwari |
| F7 | Filters stopped working after an SQL edit | Template tags regenerated with new UUIDs, breaking parameter→tag wiring | Reuse the existing `template-tags` + `parameters[]` verbatim when patching | Dashboard shows "N connected" and filters apply | Durga |
| F8 | "must contain at least one {{}}" error | `[[ ]]` block wraps OR/paren logic | Move the logic into a pre-filtered CTE and keep `[[ and x = {{v}} ]]` simple | Card runs with and without the filter | Support metrics |
| F9 | New value **missing from the dropdown** | Metabase field values not rescanned (`is_full_sync=false`) | `POST /api/database/<DB_ID>/rescan_values` | Value appears | Shelter |
| F10 | New column/table **not selectable** at all | Metabase schema cache stale | `POST /api/database/<DB_ID>/sync_schema` | Column visible in the picker | Mantrana, Shramik Bharti |
| F11 | "Donor month"/"MIS month" filter gives odd results | Derived from dates, but the org records it as a **coded field** | Filter on the real concept (e.g. "Submission for approval" month) | Matches the client's own sheet | Durga |
| F12 | Filter on a multi-select column misses rows | Equality against comma-joined text | `{{v}} in (select trim(x) from unnest(string_to_array(col,',')) x)`, or the `_coded` table | Row with the value in 2nd position is found | Durga |
| F13 | Filter options wrong after a **grain change** | The filter expression was written for the old grain | Rewrite, e.g. `case when count(media)>0` per session | Spot-check 3 rows | Durga |
| F14 | Report count ≠ app count, "filter bug" reported | Definition gap (enrolled vs registered, attended vs roster) | Add a required status filter with a default (`Enrolled`), where `All` = the app | `All` equals the app number exactly | Durga, Khel Mel |
| F15 | Month filter **drops people** with no activity | Date filter applied after the roster join | Put date/month filters **inside** the activity CTE; roster LEFT JOIN outside | Roster size constant across months | Khel Mel |
| F16 | Month-filtered total < unfiltered total | NULL-dated sessions excluded by any date filter | Document it in the card description, or exclude NULL dates everywhere | Explained difference = NULL-date count | Khel Mel |
| F17 | Field filter can't target a table | Schema not registered in Metabase / alias mismatch | Plain `{{variable}}`, or build on a Model | Filter applies | Support metrics, Sangwari |
| F18 | Superset: new native filter shows no values / errors | Dataset's registered columns stale | `PUT /api/v1/dataset/<id>?override_columns=true` with columns | Filter lists values | JNPCT |
| F19 | Client asks for a filter the data can't support ("screening done") | No such field captured | Say so, and offer the closest real field | Client agrees | JNPCT |
| F20 | Some cards ignore the date filter **on purpose** (cohort recovery) | Cohort metrics are defined by enrolment, not visit date | Document on the card ("responds to location/worker only") | Description present | Sangwari |
| F21 | Filter "not applicable" for some cards (grade on a staff card) | Intentional | Leave unmapped + document | — | Gubbachi |
| F22 | Drill/filter hits the wrong place for same-named locations | Two nodes with the same name (two "Raigarh District") | Pass village + district + state together | Correct row count | Khel Mel |
