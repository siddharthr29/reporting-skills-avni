#!/usr/bin/env python3
"""QA checks for Avni reports (all read-only).

  qa.py except-all old.sql new.sql [--mb-db <DB_ID>]  prove a rewrite returns identical rows
                                                      (tunnel by default; --mb-db runs via Metabase)
  qa.py drill --metric <CARD_ID> --drill <CARD_ID>   scalar metric value vs drill row count (no filters)
  qa.py uuid-scan <CARD_ID> [...]                    any raw UUIDs in the output?  (want 0)
  qa.py time <CARD_ID> [...]                         cold + warm run time through Metabase
"""
import argparse, os, re, subprocess, sys, time
from _common import die, load_env, strip_optional, template_vars

ENV = load_env()
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def mb():
    from mb import client
    return client()


def psql_rows(sql):
    env = dict(os.environ, **{k: v for k, v in ENV.items() if k.startswith("PG")},
               PGHOST="localhost", PGPORT=ENV.get("LOCAL_PORT", "5433"),
               PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=600000")
    r = subprocess.run([ENV.get("PSQL", "psql"), "-X", "-At", "-F", "\t", "-c", sql],
                       capture_output=True, text=True, env=env)
    if r.returncode:
        die(r.stderr.strip()[:600] + "\n(is the tunnel up?  ./tools/tunnel.sh up)")
    return [l.split("\t") for l in r.stdout.splitlines() if l]


def prep(path):
    sql = strip_optional(open(path).read()).strip().rstrip(";")
    if template_vars(sql):
        die(f"{path}: required variables remain {template_vars(sql)}")
    return sql


def except_all(a):
    old, new = prep(a.old), prep(a.new)
    sql = f"""with a as materialized ({old}), b as materialized ({new})
select (select count(*) from a), (select count(*) from b),
       (select count(*) from (select * from a except all select * from b) x),
       (select count(*) from (select * from b except all select * from a) y)"""
    t0 = time.time()
    if a.mb_db:
        r = mb().post("/dataset", {"database": a.mb_db, "type": "native", "native": {"query": sql}})
        row = r["data"]["rows"][0]
    else:
        row = psql_rows(sql)[0]
    o, n, om, no = (int(x) for x in row)
    ok = o == n and om == 0 and no == 0
    print(f"old_rows={o} new_rows={n} old_minus_new={om} new_minus_old={no}  ({time.time()-t0:.1f}s)")
    print("✓ IDENTICAL — safe to ship" if ok else "✗ DIFFERENT — do not ship; inspect with EXCEPT ALL")
    sys.exit(0 if ok else 1)


def card_query(api, cid):
    t0 = time.time()
    r = api.post(f"/card/{cid}/query")
    if r.get("status") == "failed":
        die(f"card {cid}: {str(r.get('error'))[:300]}")
    return r, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("except-all"); p.add_argument("old"); p.add_argument("new"); p.add_argument("--mb-db", type=int)
    p = sp.add_parser("drill"); p.add_argument("--metric", type=int, required=True); p.add_argument("--drill", type=int, required=True)
    p = sp.add_parser("uuid-scan"); p.add_argument("cards", type=int, nargs="+")
    p = sp.add_parser("time"); p.add_argument("cards", type=int, nargs="+")
    a = ap.parse_args()

    if a.cmd == "except-all":
        return except_all(a)
    api = mb()
    if a.cmd == "drill":
        m, _ = card_query(api, a.metric)
        d, _ = card_query(api, a.drill)
        val = m["data"]["rows"][0][0] if m["data"]["rows"] else None
        cnt = d.get("row_count", len(d["data"]["rows"]))
        capped = cnt >= 2000
        print(f"metric={val}  drill_rows={cnt}{' (capped at 2000 — verify with SQL count)' if capped else ''}")
        print("✓ match" if str(val) == str(cnt) else ("? capped" if capped else "✗ MISMATCH — see playbooks/drilldown-issues.md"))
    elif a.cmd == "uuid-scan":
        for cid in a.cards:
            r, _ = card_query(api, cid)
            hits = [(i, c) for i, row in enumerate(r["data"]["rows"]) for c in row if c and UUID.search(str(c))]
            print(f"card {cid}: {len(hits)} UUID cell(s){' e.g. row %d' % hits[0][0] if hits else ''}")
    elif a.cmd == "time":
        for cid in a.cards:
            _, cold = card_query(api, cid)
            _, warm = card_query(api, cid)
            flag = "✗ too slow" if cold > 30 else "✓"
            print(f"card {cid}: cold {cold:.1f}s  warm {warm:.1f}s  {flag}")


if __name__ == "__main__":
    main()
