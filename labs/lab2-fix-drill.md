# Lab 2 — Fix a drill-down (20 min)

**Scenario (a real ticket shape):** "On the dashboard, *Children with no visit in 30 days* shows **14**, but clicking it opens the full child list (**300+** rows)."

## Steps
1. On your Lab 1 dashboard, add a scalar card "People with no visit in 30 days" (roster LEFT JOIN visits, no visit since `current_date - 30`).
2. Add a generic line-list card "All people" and set the scalar's click behaviour to open it. You've now reproduced the bug.
3. Ask your agent:
   > The metric shows N but the drill shows everyone. Use playbooks/drilldown-issues.md and skills/metabase-reports/references/drilldowns.md to fix it properly.
4. Expect it to: create a **dedicated drill card** (same base CTE + the metric's condition), point the click behaviour at it with target `{"type":"variable","id":"block"}`, and pass the Block filter through.
5. Verify: `python3 tools/qa.py drill --metric <metric id> --drill <drill id>`, then repeat in the browser with Block = one value.

## Done when
- [ ] metric == drill rows, unfiltered **and** with a Block selected.
- [ ] The drill card is named `(drill) [NOVISIT30] …`.
- [ ] You can explain why a shared line list is the root cause.
