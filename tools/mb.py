#!/usr/bin/env python3
"""Metabase client for Avni reporting. Reads are free; writes are DRY-RUN unless --apply, and back up first.

  mb.py whoami
  mb.py dbs [--match <text>]                       list databases (find the live one for a schema)
  mb.py search <text>                              cards / dashboards / collections by name
  mb.py card <id> [--sql]                          card summary (tags, params, db); --sql prints the SQL
  mb.py dash <id>                                  dashboard: params, cards, parameter mappings, click behaviours
  mb.py run --db <DB_ID> ("<sql>" | -f file.sql)   run SQL through Metabase (optional [[ ]] blocks stripped)
  mb.py set-sql <card_id> -f new.sql [--apply]     patch a card's SQL IN PLACE, keeping template tags + params
  mb.py create-card --name N --collection C --db D -f q.sql [--display scalar|table|bar] [--apply]
                                                   new card (SQL validated in Metabase first; dry-run default)
  mb.py tree <COLLECTION_ID>                       folder tree with dashboard/card counts; flags missing standard folders
  mb.py folders <COLLECTION_ID> [--apply]          create missing standard folders (Dashboards, Report Cards, …)
  mb.py perms <COLLECTION_ID>                      every group's access per folder; flags subfolder gaps
  mb.py grant <COLLECTION_ID> --group G [--level read|write] [--apply]   grant a group the whole folder tree
  mb.py sync <db_id> [--values] [--apply]          sync_schema (and rescan_values)
  mb.py backup (card|dashboard) <id>
"""
import argparse, json, sys, uuid
from _common import Http, backup, die, load_env, show_diff, strip_optional, template_vars
from _guard import require_catalog
from _pii import print_table

ENV = load_env()


def client():
    key = ENV.get("METABASE_API_KEY")
    if not key or key.startswith("<"):
        die("METABASE_API_KEY not set in tools/.env")
    return Http(ENV.get("METABASE_URL", "https://reporting.avniproject.org") + "/api", {"x-api-key": key})


def card_native(card):
    """Return (sql, template_tags, database_id) for both pMBQL (stages) and legacy shapes."""
    dq = card.get("dataset_query") or {}
    if "stages" in dq:
        st = (dq.get("stages") or [{}])[0]
        return st.get("native"), st.get("template-tags") or {}, dq.get("database")
    nat = dq.get("native") or {}
    return nat.get("query"), nat.get("template-tags") or {}, dq.get("database")


def cmd_card(api, a):
    c = api.get(f"/card/{a.id}")
    sql, tags, db = card_native(c)
    print(f"#{c['id']}  {c['name']}  | db={db} | display={c.get('display')} | collection={c.get('collection_id')}"
          f" | archived={c.get('archived')}")
    print("native SQL" if sql else "GUI/MBQL question (no native SQL)")
    for k, t in tags.items():
        print(f"  tag {{{{{k}}}}} type={t.get('type')} list={t.get('values-query-type')} "
              f"source={t.get('values-source-type')} required={t.get('required', False)}")
    for p in c.get("parameters") or []:
        print(f"  param {p.get('slug')} list={p.get('values_query_type')} source={p.get('values_source_type')}")
    if a.sql and sql:
        print("\n" + sql)


def cmd_dash(api, a):
    d = api.get(f"/dashboard/{a.id}")
    print(f"dashboard #{d['id']} {d['name']} | tabs={len(d.get('tabs') or [])}")
    for p in d.get("parameters") or []:
        print(f"  filter {p['name']!r} id={p['id']} type={p['type']} list={p.get('values_query_type')}")
    for dc in d.get("dashcards") or []:
        card = dc.get("card") or {}
        cb = (dc.get("visualization_settings") or {}).get("click_behavior")
        maps = [m["parameter_id"] for m in dc.get("parameter_mappings") or []]
        print(f"  card #{card.get('id')} {card.get('name','(text)')!r} filters_mapped={len(maps)} "
              f"click={cb.get('type') + ('→' + str(cb.get('targetId')) if cb.get('targetId') else '') if cb else '-'}")
    unmapped = {p["id"] for p in d.get("parameters") or []}
    for dc in d.get("dashcards") or []:
        unmapped -= {m["parameter_id"] for m in dc.get("parameter_mappings") or []}
    if unmapped:
        print(f"  ! filters mapped to NO card: {sorted(unmapped)}")


def cmd_run(api, a):
    sql = open(a.file).read() if a.file else a.sql
    if not sql:
        die("give SQL or -f file")
    sql = strip_optional(sql)
    if template_vars(sql):
        die(f"required variables remain: {template_vars(sql)} — substitute test values")
    require_catalog(sql)
    r = api.post("/dataset", {"database": a.db, "type": "native", "native": {"query": sql}})
    if r.get("status") == "failed" or r.get("error"):
        die(str(r.get("error"))[:600])
    cols = [c["name"] for c in r["data"]["cols"]]
    print_table(cols, r["data"]["rows"], a.limit)          # PII masked before printing
    print(f"-- ran in {r.get('running_time')} ms (API caps at 2000 rows)", file=sys.stderr)


def cmd_set_sql(api, a):
    c = api.get(f"/card/{a.id}")
    old, tags, db = card_native(c)
    if old is None:
        die("not a native SQL card")
    new = open(a.file).read()
    require_catalog(new)
    new_vars = template_vars(new)
    keep = {k: v for k, v in tags.items() if k in new_vars}          # reuse existing tags VERBATIM
    added = [v for v in new_vars if v not in tags]
    removed = [k for k in tags if k not in new_vars]
    for v in added:
        keep[v] = {"id": str(uuid.uuid4()), "name": v, "display-name": v.replace("_", " ").title(), "type": "text"}
    params = [p for p in (c.get("parameters") or []) if p.get("slug") in new_vars]
    if not show_diff(old, new):
        return
    if added:
        print(f"! NEW tags (type text — set type/value source, then map on dashboards): {added}")
    if removed:
        print(f"! tags REMOVED (their dashboard filters will disconnect): {removed}")
    if not a.apply:
        print("\nDRY-RUN. Re-run with --apply to write.")
        return
    path = backup("card", a.id, c)
    body = {"dataset_query": {"type": "native", "database": db, "native": {"query": new, "template-tags": keep}},
            "parameters": params}
    api.put(f"/card/{a.id}", body)
    chk_sql, chk_tags, _ = card_native(api.get(f"/card/{a.id}"))
    print(f"✓ card {a.id} updated in place (backup: {path}); sql_matches={chk_sql.strip() == new.strip()} "
          f"tags={sorted(chk_tags)}")


def cmd_create_card(api, a):
    sql = open(a.file).read()
    require_catalog(sql)
    tags = {}
    for v in template_vars(sql):
        is_date = "date" in v
        tags[v] = {"id": str(uuid.uuid4()), "name": v, "display-name": v.replace("_", " ").title(),
                   "type": "date" if is_date else "text"}
    body = {"name": a.name, "collection_id": a.collection, "display": a.display, "description": a.description,
            "visualization_settings": {},
            "dataset_query": {"type": "native", "database": a.db, "native": {"query": sql, "template-tags": tags}}}
    if a.display == "bar":
        print("! bar charts also need visualization_settings graph.dimensions/metrics — set after creation")
    print(f"Will create card {a.name!r} in collection {a.collection} on database {a.db} as {a.display}; "
          f"filters: {list(tags) or 'none'}")
    # Validate the SQL runs (filters stripped) before creating anything.
    probe = strip_optional(sql)
    if not template_vars(probe):
        r = api.post("/dataset", {"database": a.db, "type": "native", "native": {"query": probe}})
        if r.get("error"):
            die(f"SQL fails in Metabase: {str(r['error'])[:400]}")
        print(f"✓ SQL runs in Metabase ({r.get('row_count')} rows unfiltered)")
    if not a.apply:
        print("DRY-RUN. Re-run with --apply to create it."); return
    c = api.post("/card", body)
    print(f"✓ created card #{c['id']}  {ENV.get('METABASE_URL', '').rstrip('/')}/question/{c['id']}")


# ---------- folders (collections) & folder-wise permissions ----------
STANDARD = ["Dashboards", "Report Cards", "Report Cards/Drill-downs", "Report Cards/Filter values"]


def all_collections(api):
    cols = api.get("/collection")
    return [c for c in cols if isinstance(c.get("id"), int)]


def subtree(api, root_id):
    cols = all_collections(api)
    root = next((c for c in cols if c["id"] == root_id), None)
    if not root:
        die(f"collection {root_id} not found")
    prefix = f"{root.get('location', '/')}{root_id}/"
    kids = [c for c in cols if (c.get("location") or "").startswith(prefix) and not c.get("archived")]
    return root, kids


def path_of(c, byid):
    ids = [int(x) for x in (c.get("location") or "/").strip("/").split("/") if x]
    return " / ".join([byid[i]["name"] for i in ids if i in byid] + [c["name"]])


def cmd_tree(api, a):
    root, kids = subtree(api, a.id)
    byid = {c["id"]: c for c in [root] + kids}
    print(f"{root['name']}  (#{root['id']})")
    for c in sorted(kids, key=lambda c: path_of(c, byid)):
        depth = len([x for x in c["location"].strip("/").split("/") if x]) - len([x for x in root.get("location", "/").strip("/").split("/") if x])
        items = api.get(f"/collection/{c['id']}/items?models=card&models=dashboard").get("data", [])
        n_card = sum(1 for i in items if i.get("model") == "card")
        n_dash = sum(1 for i in items if i.get("model") == "dashboard")
        print(f"{'   ' * depth}└─ {c['name']}  (#{c['id']}) — {n_dash} dashboard(s), {n_card} card(s)")
    missing = [s for s in STANDARD if not any(path_of(c, byid).endswith(" / " + s.replace("/", " / ")) for c in kids)]
    if missing:
        print(f"\n! missing standard folders: {missing}  →  mb.py folders {a.id} --apply")


def cmd_folders(api, a):
    root, kids = subtree(api, a.id)
    byid = {c["id"]: c for c in [root] + kids}
    have = {path_of(c, byid): c["id"] for c in kids}
    base = path_of(root, byid)
    for s in STANDARD:
        full = base + " / " + s.replace("/", " / ")
        if full in have:
            print(f"✓ {s}")
            continue
        parent = a.id if "/" not in s else have.get(base + " / " + s.split("/")[0])
        if not a.apply:
            print(f"+ would create {s!r}")
            continue
        c = api.post("/collection", {"name": s.split("/")[-1], "parent_id": parent})
        have[full] = c["id"]
        print(f"✓ created {s!r} (#{c['id']})")
    if not a.apply:
        print("DRY-RUN. Re-run with --apply to create missing folders.")


def cmd_perms(api, a):
    root, kids = subtree(api, a.id)
    byid = {c["id"]: c for c in [root] + kids}
    graph = api.get("/collection/graph")
    groups = {g["id"]: g["name"] for g in api.get("/permissions/group")}
    folders = [root] + sorted(kids, key=lambda c: path_of(c, byid))
    gaps = 0
    for gid, perms in graph["groups"].items():
        levels = {c["id"]: perms.get(str(c["id"]), perms.get(c["id"], "none")) for c in folders}
        if all(v == "none" for v in levels.values()) or groups.get(int(gid)) == "Administrators":
            continue
        print(f"\nGroup {groups.get(int(gid), gid)!r} (#{gid})")
        for c in folders:
            lvl = levels[c["id"]]
            parent_ids = [int(x) for x in (c.get("location") or "/").strip("/").split("/") if x]
            parent_has = any(levels.get(p, "none") != "none" for p in parent_ids if p in levels)
            gap = lvl == "none" and parent_has
            gaps += gap
            print(f"   {'✗' if gap else ('✓' if lvl != 'none' else '·')} {path_of(c, byid)}: {lvl}"
                  + ("   ← NO ACCESS to this subfolder (permissions don't inherit)" if gap else ""))
    print(f"\n{'✓ no gaps' if not gaps else f'✗ {gaps} subfolder gap(s) — fix: mb.py grant {a.id} --group <id> --level read --apply'}")


def cmd_grant(api, a):
    root, kids = subtree(api, a.id)
    graph = api.get("/collection/graph")
    ids = [root["id"]] + [c["id"] for c in kids]
    cur = graph["groups"].get(str(a.group), {})
    changes = {str(i): a.level for i in ids if cur.get(str(i), cur.get(i, "none")) != a.level}
    print(f"Group #{a.group}: set '{a.level}' on {len(ids)} folder(s) under #{a.id}; {len(changes)} change(s) needed")
    if not changes:
        return
    if not a.apply:
        print("DRY-RUN. Re-run with --apply to grant.")
        return
    backup("collection_graph", a.group, graph)
    api.put("/collection/graph", {"revision": graph["revision"], "groups": {str(a.group): changes}})
    after = api.get("/collection/graph")["groups"].get(str(a.group), {})
    ok = all(after.get(k, after.get(int(k))) == a.level for k in changes)
    print(f"{'✓' if ok else '✗'} granted '{a.level}' on {len(changes)} folder(s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("whoami")
    p = sp.add_parser("dbs"); p.add_argument("--match", default="")
    p = sp.add_parser("search"); p.add_argument("text")
    p = sp.add_parser("card"); p.add_argument("id", type=int); p.add_argument("--sql", action="store_true")
    p = sp.add_parser("dash"); p.add_argument("id", type=int)
    p = sp.add_parser("run"); p.add_argument("--db", type=int, required=True); p.add_argument("sql", nargs="?")
    p.add_argument("-f", "--file"); p.add_argument("--limit", type=int, default=20)
    p = sp.add_parser("set-sql"); p.add_argument("id", type=int); p.add_argument("-f", "--file", required=True)
    p.add_argument("--apply", action="store_true")
    p = sp.add_parser("create-card"); p.add_argument("--name", required=True); p.add_argument("--collection", type=int, required=True)
    p.add_argument("--db", type=int, required=True); p.add_argument("-f", "--file", required=True)
    p.add_argument("--display", default="table", choices=["table", "scalar", "bar", "pie", "line"])
    p.add_argument("--description", default=None); p.add_argument("--apply", action="store_true")
    p = sp.add_parser("tree"); p.add_argument("id", type=int)
    p = sp.add_parser("folders"); p.add_argument("id", type=int); p.add_argument("--apply", action="store_true")
    p = sp.add_parser("perms"); p.add_argument("id", type=int)
    p = sp.add_parser("grant"); p.add_argument("id", type=int); p.add_argument("--group", type=int, required=True)
    p.add_argument("--level", choices=["read", "write"], default="read"); p.add_argument("--apply", action="store_true")
    p = sp.add_parser("sync"); p.add_argument("id", type=int); p.add_argument("--values", action="store_true")
    p.add_argument("--apply", action="store_true")
    p = sp.add_parser("backup"); p.add_argument("kind", choices=["card", "dashboard"]); p.add_argument("id", type=int)
    a = ap.parse_args()
    api = client()

    if a.cmd == "whoami":
        u = api.get("/user/current"); print(u.get("common_name"), "| superuser:", u.get("is_superuser"))
    elif a.cmd == "dbs":
        for d in api.get("/database").get("data", []):
            if a.match.lower() in d["name"].lower():
                print(f"{d['id']:>5}  {d['name']}  (engine={d.get('engine')}, full_sync={d.get('is_full_sync')})")
    elif a.cmd == "search":
        for r in api.get(f"/search?q={a.text}").get("data", [])[:40]:
            print(f"{r['model']:<10} #{r['id']:<6} {r['name']}  (collection: {(r.get('collection') or {}).get('name')})")
    elif a.cmd == "card":
        cmd_card(api, a)
    elif a.cmd == "dash":
        cmd_dash(api, a)
    elif a.cmd == "run":
        cmd_run(api, a)
    elif a.cmd == "set-sql":
        cmd_set_sql(api, a)
    elif a.cmd == "create-card":
        cmd_create_card(api, a)
    elif a.cmd in ("tree", "folders", "perms", "grant"):
        {"tree": cmd_tree, "folders": cmd_folders, "perms": cmd_perms, "grant": cmd_grant}[a.cmd](api, a)
    elif a.cmd == "sync":
        steps = ["sync_schema"] + (["rescan_values"] if a.values else [])
        if not a.apply:
            print(f"DRY-RUN: would POST {steps} on database {a.id}. Add --apply."); return
        for s in steps:
            api.post(f"/database/{a.id}/{s}"); print(f"✓ {s} triggered (runs async; wait a minute)")
    elif a.cmd == "backup":
        print(backup(a.kind, a.id, api.get(f"/{a.kind}/{a.id}")))


if __name__ == "__main__":
    main()
