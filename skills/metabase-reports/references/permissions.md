# Metabase permissions for org users

## Model
- Users belong to **groups**. Groups get **collection** permissions (`read` / `write` / none).
- Database-level access is often "unrestricted" for every group here. Access is really gated by **collections**. Don't mistake that for over-exposure.
- **Subcollections do not inherit.** Granting `Org → Reports` does NOT grant `Org → Reports → Dashboards`. Every subcollection needs its own grant, or users see only the top level ("I can't see the reports").

## With the tools (recommended)
```bash
python3 tools/mb.py perms <ORG_FOLDER_ID>                                  # every group × every folder; ✗ = gap
python3 tools/mb.py grant <ORG_FOLDER_ID> --group <GROUP_ID> --level read  # dry-run: shows changes
python3 tools/mb.py grant <ORG_FOLDER_ID> --group <GROUP_ID> --level read --apply   # backs up the graph first
python3 tools/mb.py perms <ORG_FOLDER_ID>                                  # confirm: no ✗ left
```

## Granting a group read on a collection tree (raw API)
```
GET  /api/collection/graph                 → {revision, groups:{<gid>:{<cid>:"read"|"write"|"none"}}}
     find the tree: every collection whose `location` starts with "/<root_id>/" (plus the root)
PUT  /api/collection/graph {revision, groups:{<gid>:{<cid>:"read", ...}}}
```
- In a dry-run, compare against the real values `read`/`write`, and treat a missing entry as `none`. Comparing against the string `"(none)"` once showed "all granted" when nothing was.
- Send the current `revision`, or the PUT is rejected.

## Users
- Use `GET /api/user?limit=2000` (bulk). `GET /api/user/<id>` intermittently returns empty `group_ids`.
- Membership: `POST /api/permissions/membership {group_id, user_id}`. Removal: `DELETE /api/permissions/membership/<membership_id>`.
- Deactivation is reversible (`PUT /api/user/<id>/reactivate`). Confirm with the client before any deactivation.

## Verify like the user
Log in as (or impersonate) a test member, open the collection tree, and confirm every subfolder and dashboard is visible.
