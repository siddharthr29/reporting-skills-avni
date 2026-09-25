#!/usr/bin/env python3
"""Superset client for Avni reporting. Reads are free; writes are DRY-RUN unless --apply, and back up first.

  ss.py whoami
  ss.py dataset <id> [--sql]                         dataset summary, columns, database
  ss.py charts-for <dataset_id>                      charts using a dataset + their dashboards
  ss.py dashboard <id>                               charts, native filters, cross-filter setting
  ss.py sqllab --db <DB_ID> ("<sql>" | -f file) [--count]   execute through Superset (timed)
  ss.py set-dataset-sql <id> -f new.sql [--override-columns] [--apply]
"""
import argparse, json, sys, time, urllib.parse
from _common import Http, backup, die, load_env, show_diff
from _guard import require_catalog
from _pii import print_table

ENV = load_env()


def login():
    base = ENV.get("SUPERSET_URL", "https://reporting-superset.avniproject.org")
    user, pw = ENV.get("SUPERSET_USER"), ENV.get("SUPERSET_PASSWORD")
    if not user or user.startswith("<"):
        die("SUPERSET_USER / SUPERSET_PASSWORD not set in tools/.env")
    api = Http(base, cookies=True, timeout=300)
    tok = api.post("/api/v1/security/login", {"username": user, "password": pw, "provider": "db", "refresh": True})
    api.headers["Authorization"] = f"Bearer {tok['access_token']}"
    csrf = api.get("/api/v1/security/csrf_token/").get("result")
    api.headers.update({"X-CSRFToken": csrf, "Referer": base + "/"})
    return api


def q(obj):
    return urllib.parse.quote(json.dumps(obj) if not isinstance(obj, str) else obj)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("whoami")
    p = sp.add_parser("dataset"); p.add_argument("id", type=int); p.add_argument("--sql", action="store_true")
    p = sp.add_parser("charts-for"); p.add_argument("id", type=int)
    p = sp.add_parser("dashboard"); p.add_argument("id", type=int)
    p = sp.add_parser("sqllab"); p.add_argument("--db", type=int, required=True); p.add_argument("sql", nargs="?")
    p.add_argument("-f", "--file"); p.add_argument("--count", action="store_true")
    p = sp.add_parser("set-dataset-sql"); p.add_argument("id", type=int); p.add_argument("-f", "--file", required=True)
    p.add_argument("--override-columns", action="store_true"); p.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    api = login()

    if a.cmd == "whoami":
        # /api/v1/me/ needs a browser session (401 with a JWT), so prove access with a token-authorised call.
        n = api.get("/api/v1/dataset/?q=(page_size:1)").get("count")
        print(f"logged in as {ENV.get('SUPERSET_USER')} | datasets visible: {n}")

    elif a.cmd == "dataset":
        r = api.get(f"/api/v1/dataset/{a.id}")["result"]
        cols = [c["column_name"] for c in r.get("columns", [])]
        print(f"dataset #{a.id} {r['table_name']!r} | db={r['database']['id']} {r['database'].get('database_name')!r}"
              f" | schema={r.get('schema')} | virtual={bool(r.get('sql'))} | {len(cols)} columns")
        print("  columns:", ", ".join(cols))
        if a.sql:
            print("\n" + (r.get("sql") or ""))

    elif a.cmd == "charts-for":
        flt = f"(filters:!((col:datasource_id,opr:eq,value:{a.id})),page_size:100)"
        for c in api.get(f"/api/v1/chart/?q={urllib.parse.quote(flt)}").get("result", []):
            full = api.get(f"/api/v1/chart/{c['id']}")["result"]
            dashes = [f"#{d['id']} {d.get('dashboard_title')!r}" for d in full.get("dashboards", [])]
            print(f"chart #{c['id']} {c.get('slice_name')!r} viz={full.get('viz_type')} "
                  f"query_context={'yes' if full.get('query_context') else 'MISSING'} → {dashes or 'no dashboard'}")

    elif a.cmd == "dashboard":
        d = api.get(f"/api/v1/dashboard/{a.id}")["result"]
        meta = json.loads(d.get("json_metadata") or "{}")
        print(f"dashboard #{a.id} {d['dashboard_title']!r} | cross_filters={meta.get('cross_filters_enabled')}")
        for f in meta.get("native_filter_configuration", []):
            if f.get("type") == "DIVIDER":
                print(f"  — section: {f.get('title')!r}"); continue
            tg = [(t.get("datasetId"), (t.get("column") or {}).get("name")) for t in f.get("targets", [])]
            print(f"  filter {f.get('name')!r} {f.get('filterType')} targets={tg} charts={len(f.get('chartsInScope') or [])}")
        for c in api.get(f"/api/v1/dashboard/{a.id}/charts").get("result", []):
            print(f"  chart #{c['id']} {c.get('slice_name')!r}")

    elif a.cmd == "sqllab":
        sql = open(a.file).read() if a.file else a.sql
        require_catalog(sql)
        if a.count:
            sql = f"select count(*) as n from (\n{sql}\n) q"
        t0 = time.time()
        r = api.post("/api/v1/sqllab/execute/", {"database_id": a.db, "sql": sql, "schema": None,
                                                 "runAsync": False, "json": True, "tab": "reporting-skills"})
        rows = r.get("data") or []
        cols = [c.get("column_name") or c.get("name") for c in (r.get("columns") or [])] or (list(rows[0]) if rows else [])
        print_table(cols, [[row.get(c) for c in cols] for row in rows], 20)   # PII masked before printing
        print(f"-- returned in {time.time() - t0:.2f}s (status={r.get('status')})", file=sys.stderr)

    elif a.cmd == "set-dataset-sql":
        cur = api.get(f"/api/v1/dataset/{a.id}")["result"]
        new = open(a.file).read()
        require_catalog(new)
        if not show_diff(cur.get("sql") or "", new):
            return
        if not a.apply:
            print(f"\nDRY-RUN. Re-run with --apply. Output columns changing? add --override-columns.")
            return
        b = backup("dataset", a.id, cur)
        api.put(f"/api/v1/dataset/{a.id}", {"sql": new})
        if a.override_columns:
            # Re-read the column list from the new SQL (fixes stale 'X__1 does not exist' columns).
            api.put(f"/api/v1/dataset/{a.id}/refresh")
        after = api.get(f"/api/v1/dataset/{a.id}")["result"]
        before_cols = {c["column_name"] for c in cur.get("columns", [])}
        after_cols = {c["column_name"] for c in after.get("columns", [])}
        print(f"✓ dataset {a.id} updated (backup: {b}); sql_matches={(after.get('sql') or '').strip() == new.strip()}"
              f" columns {len(before_cols)}→{len(after_cols)} removed={sorted(before_cols - after_cols) or 'none'}")


if __name__ == "__main__":
    main()
