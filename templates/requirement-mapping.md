# Requirement mapping — <Org> · <sheet name>

Fill this **after** `tools/read_requirements.py` and `tools/dump_org_schema.sh`, **before** building.
One row per requirement row. Share the "Needs clarification" and "Not in data" rows with the client in **one** message.

| # | Requirement (client's words) | Type (number / % / chart / list) | Data source (table · column from CATALOG.md) | Logic in plain words | Filters | Click-through? | Status | Question for client |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | ✅ Buildable | |
| 2 | | | | | | | ❓ Needs clarification | |
| 3 | | | | | | | ⛔ Not in data | |

Status meanings:
- **✅ Buildable**: the columns exist and the logic is clear.
- **❓ Needs clarification**: ambiguous wording (e.g. "active", "registered vs enrolled", "last visit"), or a missing denominator, date basis or grouping.
- **⛔ Not in data**: no form captures it. Say so, and suggest the closest real field.

Build order: all ✅ rows, grouped by dashboard. Then the ❓ rows once answered.
