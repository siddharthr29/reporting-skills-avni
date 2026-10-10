# Learnings inbox

New learnings land here first (via `tools/add_learning.py` or by hand), then get **curated** into
`skills/`, `playbooks/`, `sql/patterns/` and `evals/` — see `skills/report-learnings/SKILL.md`.

Format (one block per learning, newest at the bottom):

```
### YYYY-MM-DD · <type> · <tool> · <org or -> — <title>
- **Symptom:** …
- **Cause:** …
- **Fix:** … (how it was verified)
- **Source:** ticket / session
```

<!-- LEARNINGS START -->
### 2026-09-25 · fix · process · Door Step School — dump_org_schema crashed on coded values containing tabs/newlines
- **Symptom:** schema_catalog.py: ValueError not enough values to unpack (expected 5, got 1); CATALOG.md empty
- **Cause:** pg_stats most_common_vals had a value with a newline/tab, breaking psql -At -F tab row splitting
- **Fix:** regexp_replace tabs/newlines to spaces in the stats query (tools/schema_catalog.py)
- **Source:** DSS dashboards build 2026-09-25

### 2026-09-25 · pattern · metabase · Door Step School — Exact drill from every cell of a crosstab table incl. the Total row
- **Symptom:** Crosstab (rows x Male/Female/Total columns) needs a drill per cell; column clicks cannot pass a constant
- **Cause:** Metabase click parameterMapping only passes dashboard params or the clicked row's columns
- **Fix:** One drill card per column (condition hardcoded) + row key passed from a row column; Total row labelled 'Total' and drill uses [[ and ({{row_x}} = 'Total' or col = {{row_x}}) ]] (OR inside an optional block works on v0.60); hidden-ish column (e.g. Standards '1,2') passes a set via string_to_array. Verified 70 -> 70 rows in browser
- **Source:** DSS dashboards build 2026-09-25

### 2026-09-25 · tool-behaviour · metabase · - — mb.py search crashes on text with spaces
- **Symptom:** mb.py search "Door Step" -> http.client InvalidURL
- **Cause:** search text is not URL-encoded
- **Fix:** search one word for now; tools/mb.py should urllib.parse.quote the query
- **Source:** DSS dashboards build 2026-09-25

### 2026-09-25 · org-fact · etl · Door Step School — DSS: attendance types are subjects; FLN assessments have no Pre/Post marker
- **Symptom:** Hours by Language/Maths requested; Pre/Post levels requested
- **Cause:** attendance_type rows = Language / Maths / Other Programs with no duration; FLN Performance Assessment is monthly with no Assessment Type (Reading/Library have Baseline/Midline/Endline)
- **Fix:** Sessions attended per type (hours pending session length); FLN Pre = first assessment, Post = latest per enrolment, pending client confirmation
- **Source:** DSS dashboards build 2026-09-25

### 2026-09-28 · pitfall · metabase · Door Step School — Text filters are multi-select by default and crash '= {{x}}' SQL
- **Symptom:** Picking two wards on a dashboard made every card fail: syntax error at or near ','
- **Cause:** Dashboard string parameters default to multi-select; Metabase substitutes 'a', 'b' into a plain = {{var}}
- **Fix:** Set isMultiSelect:false on every string/= dashboard parameter (one dashboard PUT, no SQL change), or write the condition as IN
- **Source:** DSS review 2026-09-28

### 2026-09-28 · pitfall · metabase · - — Never move Avni canned cards or rename the org collection
- **Symptom:** Tidying the org folder (canned cards into a subfolder, root renamed to '<Org> Reports') looks harmless
- **Cause:** avni-server CollectionRepository.getCollection finds the org collection by exact organisation name and checks canned items at its top level; teardown deletes that collection
- **Fix:** Leave the canned dashboard/cards at the root and keep the collection name; build report folders beside them
- **Source:** avni-server CollectionRepository, 2026-09-28

### 2026-09-28 · pitfall · sql · - — First-vs-latest Pre/Post puts single-assessment children in both columns
- **Symptom:** Post level table looked identical to Pre; totals always matched
- **Cause:** Pre = first and Post = latest assessment per child; a child assessed once is its own Post (773 of 1,004 at DSS)
- **Fix:** Count Post only when a later assessment exists (count(*) over (partition by enrolment) >= 2) and add a 'Not yet re-assessed' row; compare % charts on the matched cohort
- **Source:** DSS review 2026-09-28

### 2026-09-28 · tool-behaviour · sql · - — sql_review.py flags voided filters inside subqueries and VALUES CTEs as missing
- **Symptom:** Every DSS card showed voided / schema-qualify warnings although each table was filtered
- **Cause:** The checker does not look inside derived tables or union branches, and treats VALUES CTEs (p, known, g) as tables
- **Fix:** Treat those warnings as false positives after checking; the checker needs to read subquery predicates
- **Source:** DSS review 2026-09-28

### 2026-09-28 · tool-behaviour · metabase · PHRII — Click-through passes only the first value of a multi-select filter unless the target card's parameter is isMultiSelect
- **Symptom:** Two villages selected: dashboard table showed Mild = 26, the clicked list opened with one village and 13 rows
- **Cause:** Link-to-question copies a dashboard filter into the drill card's variable; when the drill card's own parameter lacks isMultiSelect:true Metabase keeps only the first value. API simulation (passing lists to /api/card/query) cannot show it
- **Fix:** Set isMultiSelect:true on every category parameter of drill cards (card parameters[]); re-tested in the browser: URL carries both values, 26 rows. Always click one multi-value case in the browser
- **Source:** PHRII P1 reports build 2026-09-28 (SCRUM-132)

### 2026-09-28 · correction · etl · PHRII — _coded tables split option labels that contain commas
- **Symptom:** HPV genotype 'Other Group A (31, 33, 52, 58)' appeared in <table>_coded as four answers: 'Other Group A (31', '33', '52', '58)'
- **Cause:** The ETL builds _coded rows by splitting the comma-joined answer text, so it does not avoid the comma trap sql/patterns/coded_multiselect.sql says it avoids
- **Fix:** When an option label contains a comma, match whole option labels on the main-table text column: ', ' || col || ', ' LIKE '%, <label>, %' (labels from concept_answer); pattern header corrected
- **Source:** PHRII P1 reports build 2026-09-28 (SCRUM-132), phrii_uat

### 2026-09-28 · pattern · metabase · - — Native text variables take several values: write IN ({{var}})
- **Symptom:** Needed n and % of the filtered total (not expressible in the query builder) with multi-select location filters
- **Cause:** Metabase 0.60 renders a multi-value text variable as IN (?, ?); a single value also works with IN
- **Fix:** SQL cards reading a model via {{#id-slug}} with [[AND m."Village" IN ({{village}})]] keep multi-select dropdowns and exact percentages
- **Source:** PHRII P1 reports build 2026-09-28 (SCRUM-132)

### 2026-09-28 · tool-behaviour · metabase · - — Link column: view_as link + link_text, no link_url
- **Symptom:** Unsure whether link_url '{{value}}' substitutes the cell value
- **Cause:** With no link_url Metabase uses the cell value as the href; link_text sets the visible text
- **Fix:** column_settings {view_as:'link', link_text:'Open'} on the deep-link column; browser check: every 'Open' anchor had the https://app.avniproject.org/#/app/subject?uuid= href
- **Source:** PHRII P1 reports build 2026-09-28 (SCRUM-132)

### 2026-09-28 · tool-behaviour · process · - — No tunnel: build schemas/<schema>/CATALOG.md from Metabase metadata
- **Symptom:** dump_org_schema.sh needs the tunnel; mb.py run refuses without a catalogue
- **Cause:** The guard only checks that the catalogue file exists; Metabase /api/database/<id>/metadata has every table and column, field values give coded answers
- **Fix:** Generated the catalogue from metadata + MBQL counts + cached field values (script kept in the PHRII session scratchpad, worth adding to tools/)
- **Source:** PHRII P1 reports build 2026-09-28 (SCRUM-132)

### 2026-09-28 · org-fact · etl · PHRII — PHRII prod: HPV results live on the Colposcopy form; blood sugar 0 is stored as Normal
- **Symptom:** Lab Results has 1 form (voided patient) while 533 swabs are collected; 149 Vitals have Blood sugar = 0 with interpretation Normal
- **Cause:** Results were typed into the Colposcopy form's copied HPV section; the form rule treats 0 as <140
- **Fix:** HPV tests read Lab Results + Colposcopy (dedup same-date copies); glucose computed from the value with 0 = not recorded
- **Source:** PHRII P1 reports build 2026-09-28 (SCRUM-132)

### 2026-10-02 · tool-behaviour · metabase · - — Card query API returns at most 2,000 rows - sum big cards in SQL when checking
- **Symptom:** A per-child-month card summed through /api/card/<id>/query came out short (8,349 vs 14,777)
- **Cause:** The card and dataset APIs cap results at 2,000 rows; a list card with more rows is silently truncated
- **Fix:** Check totals of big list cards by wrapping the card SQL in select sum(...)/count(*) and running that
- **Source:** DSS change request 2026-10-02

### 2026-10-02 · pitfall · sql · Door Step School — Same-date same-subject assessment re-entries inflate assessment counts
- **Symptom:** FLN 'assessments conducted' looked 17% higher than the assessments actually held
- **Cause:** Teachers re-submit the same assessment (same child, date, subject), up to 6 times, often with different levels
- **Fix:** Count an assessment as distinct (child, date, subject); show the extra entries separately and list them on a duplicates dashboard
- **Source:** DSS change request 2026-10-02

### 2026-10-05 · pitfall · sql · PHRII — A CTE used only inside [[ ]] optional clauses is 'never used' when the filter is empty
- **Symptom:** sql_review flagged CTE 'periods' as never used on every Period-aware card
- **Cause:** The Period filter's window lookup sat in a CTE referenced only inside [[AND ...]]; with no period chosen the CTE is unreferenced (Postgres skips it, the reviewer errors)
- **Fix:** Inline the lookup in the optional clause: [[AND EXISTS (SELECT 1 FROM (<periods select>) p WHERE p.period = {{period}} AND m.d BETWEEN p.d0 AND p.d1)]]; keep the CTE only where the main query selects from it
- **Source:** PHRII round 2 reports 2026-10-05

### 2026-10-05 · tool-behaviour · metabase · - — Browser testing with filters changes the user's remembered dashboard filter values
- **Symptom:** After click-testing with Period=2026 and two villages, the dashboards reopened with those values instead of the defaults
- **Cause:** Metabase keeps each user's last-used dashboard parameter values server-side
- **Fix:** End every browser test by opening each dashboard with every filter explicitly empty (and default-valued filters at their default) so the user sees the defaults
- **Source:** PHRII round 2 reports 2026-10-05

### 2026-10-05 · pattern · sql · PHRII — Prove rules the data cannot exercise yet with VALUES fixtures through Metabase
- **Symptom:** Prod had 17 HPV results, all Cobas: Seegene follow-up, BDO/Alinity groups, invalids and swab linking could not be checked on real data
- **Cause:** Report logic for workflows the client has not started entering yet
- **Fix:** Swap the model's source tables for VALUES CTEs (same column names) on real participant ids, run through /api/dataset, assert each case; select only ids and test columns (reports/tests/test_hpv_samples.py, 19 cases)
- **Source:** PHRII round 2 reports 2026-10-05

<!-- LEARNINGS END -->
