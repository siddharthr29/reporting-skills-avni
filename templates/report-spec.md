# Report spec — <Org> · <Report name>

| | |
|---|---|
| Tool / instance | Metabase · `reporting.avniproject.org` |
| Database / schema | `<DB_ID>` · `<schema>` |
| Location | `<Org> → Reports → Dashboards → <name>` |
| Grain | one row per … |

## Base query (shared by every card)
```sql
-- joins, is_voided=false on every table, all [[ optional filters ]]
```

## Cards
| # | Card | Type | Logic (numerator / denominator) | Drill card | Filters mapped |
|---|---|---|---|---|---|

## Filters
| Filter | Tag | Type | Values source | Default |
|---|---|---|---|---|

## Known caveats (shown in card descriptions)
- e.g. NULL-dated sessions excluded from month cards (N rows)

## QA evidence
| Check | Result |
|---|---|
| metric == drill (all) | |
| identities | |
| cold / warm load | |
| matches app / client sheet | |
