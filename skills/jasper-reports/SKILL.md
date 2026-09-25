---
name: jasper-reports
description: Diagnose and safely edit legacy Avni Jasper reports (reporting-jasper.avniproject.org) — how Jasper reads the ETL schema, the export → edit JRXML → re-import round trip, $P{} / $P!{} parameters and location RLS, and why Jasper totals differ from the app. Diagnose + safe edit only; no from-scratch report authoring.
---

# Jasper for Avni (legacy, still live)

Jasper is **no longer recommended for new reports**. Steer new asks to Metabase or Superset. But some orgs (e.g. RWB, the water/silt programme) still run on it, so support covers **diagnose + safe edit**.

## How a Jasper report works
- A **report unit** in the JasperReports Server repository = the main **JRXML** (layout + `<queryString>` SQL) + input controls (parameters) + a data source (the shared read DB).
- The SQL runs against the **same per-org ETL schema** as Metabase and Superset. So you debug Jasper numbers **exactly like any report**: take the `<queryString>` SQL, substitute the parameters, run it read-only, and compare.
- Parameters: `$P{name}` = a bound value (safe). `$P!{name}` = raw text **spliced into the SQL** (used for dynamic WHERE fragments). Location RLS is done by appending `$P!{LoggedInUserAttribute_LocationFilter}` to the query.
- Drill-down between levels (State → District → Block → Village) passes the clicked value through **report parameters/variables in a hyperlink**. Pass a variable, not a hard-coded WHERE clause. Each level has its own fixed filters (a known limitation).

## Diagnosing "Jasper shows the wrong number"
1. Get the JRXML: download the file from the repository editor, or export (below).
2. Extract `<queryString>`, replace `$P{…}` with test values, and drop `$P!{LoggedInUserAttribute_LocationFilter}` (or substitute the user's location clause).
3. Run it read-only on the ETL schema (`tools/q.sh`). Compare with the app and the raw tables.
4. The usual causes: a **status filter** (e.g. only `latest_approval_status = 'Approved'` records count, so the report "doesn't re-filter" after a status change), **ETL lag**, voided rows, a fiscal-year boundary, or an aggregation that sums the recorded values instead of current ones. Often the report is *working as designed*, so explain it with numbers.

## Safe edit: the round trip
1. **Back up.** Export the folder: `./js-export.sh --uris /<Folder> --output-zip <name>.zip --secret-key=<key>` (run on the Jasper host in `buildomatic/`), then `scp` it down. Or download each JRXML from the web UI.
2. **Edit the text.** JRXML is plain XML. For an SQL change, edit only inside `<queryString><![CDATA[ … ]]>`, keep every `$P{}` / `$P!{}` intact, and keep the output column names the fields (`<field name=…>`) expect.
3. **Validate the SQL** read-only with test parameter values before touching the server.
4. **Layout changes** (a new visible column) need a `<field>`, a header `<textField>` and a detail `<textField>`. Doing this in **Jaspersoft Studio** with live preview is safer than hand-placing XML coordinates.
5. **Upload.** Web UI → Library → folder → report → **Edit** → *Main report* → upload the corrected JRXML → Submit. The server keeps prior versions. Or re-import the zip with the same key.
6. **Re-run every level and every fiscal-year copy.** Reports are often duplicated per year and level (e.g. 4 levels × 2 years = 8 files).

**Who uploads:** the agent prepares corrected JRXML files, a backup and a README. **A human uploads** through the Jasper UI. Agents don't push to the Jasper server.

## Worked example — RWB ticket 8420 (add a column)
Ask: add "Silt excavated under Lok-Sahabhag" to the district/block/GP/village aggregate reports for two fiscal years.
- SQL: a new aggregate CTE (`lokshbg_agg`) joined on the level key, plus the total formula updated to include it. Applied to all **8** JRXMLs (4 levels × 2 FY), and verified read-only to return non-zero values that were missing before.
- Layout: the new header and detail cell were added in Studio (copy the neighbouring column, relabel, rebind to the new field).
- Delivery: 8 corrected files + 8 originals + a README mapping each file to its repository URI. A human uploaded them in the web UI.

See `references/jrxml-anatomy.md` for the XML parts you'll touch.
