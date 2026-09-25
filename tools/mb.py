#!/usr/bin/env python3
"""Metabase client for Avni reporting. Reads are free; writes are DRY-RUN unless --apply, and back up first.

  mb.py whoami
  mb.py dbs [--match <text>]                       list databases (find the live one for a schema)
  mb.py search <text>                              cards / dashboards / collections by name
  mb.py card <id> [--sql]                          card summary (tags, params, db); --sql prints the SQL
  mb.py dash <id>                                  dashboard: params, cards, parameter mappings, click behaviours
  mb.py run --db <DB_ID> ("<sql>" | -f file.sql)   run SQL through Metabase (optional [[ ]] blocks stripped)
  mb.py set-sql <card_id> -f new.sql [--apply]     patch a card's SQL IN PLACE, keeping template tags + params
  mb.py sync <db_id> [--values] [--apply]          sync_schema (and rescan_values)
  mb.py backup (card|dashboard) <id>
"""
import argparse, json, sys, uuid
from _common import Http, backup, die, load_env, show_diff, strip_optional, template_vars

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
    r = api.post("/dataset", {"database": a.db, "type": "native", "native": {"query": sql}})
    if r.get("status") == "failed" or r.get("error"):
        die(str(r.get("error"))[:600])
    cols = [c["name"] for c in r["data"]["cols"]]
    rows = r["data"]["rows"]
    print("\t".join(cols))
    for row in rows[: a.limit]:
        print("\t".join("" if v is None else str(v) for v in row))
    print(f"-- {r.get('row_count', len(rows))} rows (showing ≤{a.limit}; API caps at 2000) in {r.get('running_time')} ms",
          file=sys.stderr)


def cmd_set_sql(api, a):
    c = api.get(f"/card/{a.id}")
    old, tags, db = card_native(c)
    if old is None:
        die("not a native SQL card")
    new = open(a.file).read()
    new_vars = template_vars(new)
    keep = {k: v for k, v in tags.items() if k in new_vars}          # reuse existing tags VERBATIM
    added = [v for v in new_vars if v not in tags]
    removed = [k for k in tags if k not in new_vars]
    for v in added:
        keep[v] = {"id": str(uuid.uuid4()), "name": v, "display-name": v.replace("_", " ").title(), "type": "text"}
    params = [p for p in (c.get("parameters") or []) if p.get("slug") in new_vars]
    show_diff(old, new)
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
