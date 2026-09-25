# Lessons from real client feedback

**Everything in this pack comes from real client feedback and real requirements.** No rule here is theoretical. Each one exists because a client told us something was wrong, slow, confusing or missing, or because **we** made a mistake while fixing it. This page lists them honestly, so nobody has to repeat them.

Client words are paraphrased and people are referred to by role. Ticket numbers are Freshdesk references.

---

## 1. "The report doesn't show what we expect" (numbers & definitions)

| What the client told us | Org · ticket | What was really wrong | What we changed (rule / tool) |
|---|---|---|---|
| "We registered ~2,000 children in Raigarh but the report shows 173 rows" | Khel Mel · 8448 | The report was built from **attendance**, so children who never attended were invisible | Agree the **grain** (roster vs activity) at intake. `roster_left_join.sql` pattern + an "Attendance Status" filter |
| "The app shows 1,964 participants, the report 1,851" | Durga India | The report counted **enrolled** people and the app counts **registered** people. Both were right | "Enrollment Status" filter defaulting to Enrolled, with "All" matching the app. `playbooks/count-mismatch.md` |
| "Sessions with 'Baseline, Other' are being excluded from attendance %" (client gave an exact cohort example) | Durga India | `ILIKE '%Baseline%'` on a multi-select matched mixed answers. 39 sessions were wrong | Multi-selects only via the `_coded` table. `sql_review` flags `ilike-multiselect` |
| "The donor chart adds up to more people than we have" | Maitrayana | People in several batches were counted once per batch | `DISTINCT ON` membership pattern |
| "Block numbers don't match our records" | APF Odisha · 8506 | Records had been entered under a different block in the app. **Not a report bug** | Investigate before changing anything. Answer with exact numbers |
| "Recovery numbers look wrong" | Sangwari | Metric took the latest **row**, and a blank last visit read as "not recovered" (0/0/1 was really 2/1/14) | "Latest non-null value" pattern. Found **because** drills exposed it |
| "Counts don't match the old reports" after moving tools | Ekam (Metabase → Superset) | The old reports had a hidden `visit_no = 1` dedup | Migrations must reproduce hidden dedups. Verify every count |
| "The Z-score / value isn't updated in the report" | Sangwari · 8465 | ETL lag + Metabase cache: reports trail the app by ~1.5 h | Explain the lag. `etl-health.md` checks |

## 2. "Clicking the number shows the wrong list" (drill-downs)

| What the client told us | Org | What was really wrong | What we changed |
|---|---|---|---|
| "Clicking 'Absent' shows Present students" | Gubbachi | Drill pointed at a generic list | **One drill card per metric**, with exactly the metric's condition |
| "The card says 2 but clicking shows everyone" | Sangwari | Same, across many cards | Drill generator: `drill = base + metric condition`. 105 drills built |
| "The ANC drill shows PNC data" | Sangwari | **Our mistake:** two indicators shared a name, and our build script overwrote the wrong card | Name drills `(drill) [KEY] …` |
| "Clicking does nothing" | Door Step School | **Our mistake:** our script read Metabase's older card format and wired 0 filters | Read cards via `stages[0]`, handled in `mb.py` |
| "A blank month appears and can't be clicked" | ANT | Scheduled (undated) visits formed a NULL month | Exclude `encounter_date_time IS NULL` from "done" counts |
| "The drill ignores the block I selected" | several | Dashboard filters weren't passed into the drill | Pass every filter through. `qa.py audit-dash --param` tests drills **with** filters |

→ Rule: **if a card shows 10, the click opens exactly 10, also when filtered** (Definition of done #3).

## 3. "The filter doesn't work" (filters)

| What the client told us | Org · ticket | What was really wrong | What we changed |
|---|---|---|---|
| "The filter is a box I have to type into" | Gubbachi, Sangwari, Durga, others | Dropdown settings were only on the dashboard, not on the card | The two-level dropdown recipe. Audit checks both levels |
| "When I pick a district, Singrauli and half of Anuppur disappear" | JSS · 8447 | Filter options came from a **stale** view joined as INNER | Filter on the real subject table. Check per-area counts |
| "Changing the filter doesn't change this number" | Gubbachi | That card wasn't connected to the filter | Audit reports unconnected filters |
| "Dropouts vanish when I filter by class" | Gubbachi | Leaving the programme voids the class link | Metrics about people who left ignore the voided link |
| "We need a 'Screening done' filter" | JNPCT · 8511 | No form records it | Say "not in the data" and offer the closest field. ⛔ status in the requirement mapping |

## 4. "It's slow / it won't download" (performance)

| What the client told us | Org · ticket | What was really wrong | What we changed |
|---|---|---|---|
| "The child list won't download, still failing across all blocks" | APF Odisha · 8402 | A hidden query sorted 1.6M rows on every load but its result was never used. 2–5 min > 60s limit | Deleted it: **0.8s**, output proven identical. `sql_review` flags `dead-join` |
| "Metabase is very slow for everyone" | Durga India | A heavy sub-query re-ran per row (103s) | `AS MATERIALIZED`: 1.1s |
| "Attendance lists time out" | Gubbachi | Per-row lookups on a huge shared table | Materialised lookup: 41s → 0.7s |
| "Reports take over a minute" | Calcutta Kids | Old cross-organisation views | Rewritten on the org's own tables: 74s → 1s |

→ Rule: **every card ≤5s** (Definition of done #2).

## 5. "Something is missing / we can't see it" (schema, access, folders)

| What the client told us | Org · ticket | What was really wrong | What we changed |
|---|---|---|---|
| "The new Zaid crops question isn't in the report" | Shramik Bharti · 8450 | Metabase hadn't refreshed its list of tables | `mb.py sync`. Dump the schema first |
| "Half the new form fields aren't available" | Mantrana | Same, and the prod schema has a UAT-looking name | Check the live database and schema per org |
| "Six reports suddenly broke" | Sangwari | A form change renamed `WEIGHT` → `Weight` | Re-dump the catalogue on "column does not exist" |
| "Data isn't syncing to Metabase" | Shelter · 8513, 8439 | Pipeline was healthy. An old table from a removed form looked stale, and a second, stale Metabase database existed | ETL diagnosis order. Pick the live database |
| "Our team can see the folder but not the reports" | JSS · 8399 | Metabase permissions **don't pass down** to subfolders | `mb.py perms` / `mb.py grant` (Definition of done #7) |
| "Some users see old, broken dashboards" | Gubbachi | **Our mistake:** rebuilding created new dashboards, but users kept old bookmarks | **Patch in place, never recreate** |
| "Please put Location before Community type in every report" | Durga India | Column order matters to users | The client's order sheet is the source of truth |
| "Build us the same report we had in Salesforce" | Goonj · 8444 | Value spellings differed between systems | Row-level reconciliation: match / only-theirs / only-ours |
| "Add a column to the Jasper reports" | RWB · 8420 | Reports were copied per level × fiscal year (8 files) | Patch **all** copies. A human uploads JRXML |

---

## Our own mistakes, and the rule each one created

| Mistake we made | What it caused | Rule now |
|---|---|---|
| Read only the first 10 messages of a long ticket (the API pages at 10) | Wrong diagnosis. Missed the client's filled sheet and an escalation (JSS · 8399) | **Read the whole ticket + every attachment** |
| Fixed permissions, then proposed an infra escalation, before proving the cause | The problem stayed open. The escalation would have been unnecessary (APF · 8402) | **Prove the cause first** (EXPLAIN, EXCEPT ALL), then act |
| A permissions dry-run compared text wrongly and showed "all granted" | False confidence (JSS · 8399) | Verify **as the user**. `mb.py perms` compares real values |
| A blanket find-and-replace of a misspelled name | Broke columns that were still misspelled (Maitrayana · 8456) | Check every column's real spelling in the catalogue |
| Rebuilt dashboards instead of editing them | Users stuck on old bookmarked copies (Gubbachi) | Patch in place. Never recreate |
| Rebuilt from old local SQL | Silently undid earlier fixes (Gubbachi) | Always pull the **live** SQL before editing |
| Matched multi-select answers with text search | Wrong attendance % (Durga) | `_coded` table only |
| Drill cards shared one generic list | "Clicked 2, saw everyone" tickets (Gubbachi, Sangwari) | One drill per metric, verified equal |

---

**Add to this page.** When a client reports something new, or we get something wrong, record it with `python3 tools/add_learning.py …`. During `/curate`, the lesson is promoted here with the rule it created.
