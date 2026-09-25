# Metabase API — the calls we actually use

Auth: `x-api-key: <key>` (an admin API key). Add retry/backoff on 429/502/503/504, a 90s timeout, and run one process at a time. Stray background runs race each other.

| Task | Call | Notes |
|---|---|---|
| Find DBs for a schema | `GET /api/database` → inspect `details` / run `select current_schema` | Several DBs can map to one schema. Pick the live one |
| Run SQL (validate) | `POST /api/dataset` `{"database":<DB_ID>,"type":"native","native":{"query":"..."}}` | Returns ≤2,000 rows |
| Full export | `POST /api/dataset/csv` (form-encoded `query=<json>`) | Beyond the 2,000-row cap, for reconciliation |
| Read card | `GET /api/card/<id>` | pMBQL: `dataset_query.stages[0].native`, `stages[0]["template-tags"]` |
| List cards | `GET /api/card?f=database&model_id=<DB_ID>` | Slim `dataset_query`. GET each for the real SQL |
| Update card | `PUT /api/card/<id>` `{dataset_query:{type:"native",database:<DB_ID>,native:{query,"template-tags"}}, parameters:[…]}` | Reuse existing tags and parameters |
| Create card | `POST /api/card` `{name, collection_id, display, visualization_settings, dataset_query, description:null}` | |
| Card history | `GET /api/revision?entity=card&id=<id>` | `diff.before.dataset_query…` restores an overwritten query |
| Dashboard | `GET/PUT /api/dashboard/<id>` | PUT with `dashcards`, **`tabs`** and `parameters`. New dashcards get negative ids |
| Archive | `PUT /api/card/<id>` `{archived:true}` | Also removes its dashcards |
| Sync schema | `POST /api/database/<DB_ID>/sync_schema` | New tables/columns |
| Rescan values | `POST /api/database/<DB_ID>/rescan_values` | New dropdown values |
| Public link | `POST /api/card/<id>/public_link` | No-login share |
| Users | `GET /api/user?limit=2000` | Use bulk. `/api/user/<id>` can return stale `group_ids` |

## Build scripts: rules
- **Idempotent and scoped.** Upsert by exact name *within one collection*. An "archive then rebuild" step must be scoped to that collection, or it wipes sibling cards.
- **Never mint new IDs for an existing report.** Re-running a builder that creates new dashboards breaks bookmarks, and users keep landing on old archived copies.
- **Keep the builder and the live SQL in sync.** A rebuild from stale local SQL silently reverts fixes. Pull live SQL (`mb.py card <id> --sql`) before editing, never an old file.
- **Back up** the object JSON before every PUT (`mb.py` writes `backups/<type>_<id>_<ts>.json`).

## Reading a card safely (python)
```python
def card_sql(card):
    dq = card["dataset_query"]
    if "stages" in dq:                       # new pMBQL shape
        st = dq["stages"][0]
        return st.get("native"), st.get("template-tags", {})
    return dq["native"]["query"], dq["native"].get("template-tags", {})   # legacy
```
