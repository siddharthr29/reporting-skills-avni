#!/usr/bin/env python3
"""QA checks for Avni reports (all read-only).

  qa.py except-all old.sql new.sql [--mb-db <DB_ID>]  prove a rewrite returns identical rows
                                                      (tunnel by default; --mb-db runs via Metabase)
  qa.py drill --metric <CARD_ID> --drill <CARD_ID>   scalar metric value vs drill row count (no filters)
  qa.py uuid-scan <CARD_ID> [...]                    any raw UUIDs in the output?  (want 0)
  qa.py time <CARD_ID> [...]                         cold + warm run time through Metabase
  qa.py audit-dash <DASH_ID> [--param block=X]       DEFINITION OF DONE: dropdowns, wiring, clickable, drill == number,
                                                     speed (≤5s goal, 30s limit), SQL review — one scorecard
"""
import argparse, os, re, subprocess, sys, time
from _common import die, load_env, strip_optional, template_vars
from _guard import require_catalog

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
    require_catalog(sql)
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


FAST, SLOW = 5, 30          # seconds: goal / hard limit


def card_query(api, cid, params=None):
    t0 = time.time()
    r = api.post(f"/card/{cid}/query", {"parameters": params} if params else None)
    if r.get("status") == "failed":
        die(f"card {cid}: {str(r.get('error'))[:300]}")
    return r, time.time() - t0


def tag_params(card_tags, filters):
    """Build Metabase query parameters for the given {slug: value} where the card has that tag."""
    out = []
    for slug, val in filters.items():
        t = card_tags.get(slug)
        if t:
            out.append({"type": "category" if t.get("type") != "date" else "date/single",
                        "target": ["variable", ["template-tag", slug]], "value": val})
    return out


def audit_dash(api, a):
    """One-command 'definition of done' check for a Metabase dashboard."""
    from mb import card_native
    from sql_review import review
    filters = dict(p.split("=", 1) for p in (a.param or []))
    d = api.get(f"/dashboard/{a.id}")
    params = d.get("parameters") or []
    res = {"filters": [], "wiring": [], "clicks": [], "drill": [], "speed": [], "sql": []}
    fail = lambda k, m: res[k].append(("✗", m))
    warn = lambda k, m: res[k].append(("!", m))
    okk = lambda k, m: res[k].append(("✓", m))

    for p in params:
        if p.get("type", "").startswith("date"):
            continue
        (okk if p.get("values_query_type") == "list" else fail)(
            "filters", f"dashboard filter {p['name']!r} is {'a dropdown' if p.get('values_query_type') == 'list' else 'a TEXT BOX — set values_query_type:list + a values source'}")
    cards = [dc for dc in d.get("dashcards") or [] if dc.get("card_id")]
    mapped_any = {m["parameter_id"] for dc in cards for m in dc.get("parameter_mappings") or []}
    print(f"Auditing dashboard #{a.id} {d['name']!r}: {len(params)} filters, {len(cards)} cards"
          + (f", with filters {filters}" if filters else "") + " …", file=sys.stderr)
    for dc in cards[: a.max_cards]:
        cid = dc["card_id"]
        card = api.get(f"/card/{cid}")
        name = f"#{cid} {card['name'][:60]!r}"
        sql, tags, _ = card_native(card)
        maps = {m["parameter_id"] for m in dc.get("parameter_mappings") or []}
        # card-level dropdowns for mapped text tags
        textbox = [slug for slug, t in tags.items()
                   if t.get("type") in ("text", "dimension") and t.get("values-source-type") and t.get("values-query-type") != "list"]
        if textbox:
            warn("filters", f"{name}: {', '.join(sorted(textbox))} open as TEXT BOXES on the card page "
                            "(tags need values-query-type:list — skills/metabase-reports/references/filters.md)")
        # filters present on the card but not wired to the dashboard
        slugs = {p.get("slug"): p["id"] for p in params}
        for slug in tags:
            if slug in slugs and slugs[slug] not in maps:
                warn("wiring", f"{name}: has filter '{slug}' but the dashboard filter isn't connected to it")
        # click-through
        cb = (dc.get("visualization_settings") or {}).get("click_behavior") or \
             (card.get("visualization_settings") or {}).get("click_behavior")
        col_cb = any((v or {}).get("click_behavior") for v in ((dc.get("visualization_settings") or {}).get("column_settings") or {}).values())
        is_metric = card.get("display") in ("scalar", "bar", "row", "pie", "line", "area", "combo", "funnel")
        if is_metric and not (cb or col_cb):
            warn("clicks", f"{name}: not clickable (no drill-down)")
        # exact drill: metric value == drill rows (scalars linking to a question)
        if not a.no_run and cb and cb.get("type") == "link" and cb.get("linkType") == "question" and card.get("display") == "scalar":
            drill = api.get(f"/card/{cb['targetId']}")
            _, dtags, _ = card_native(drill)
            m, _ = card_query(api, cid, tag_params(tags, filters))
            dr, _ = card_query(api, cb["targetId"], tag_params(dtags, filters))
            val = m["data"]["rows"][0][0] if m["data"]["rows"] else None
            n = dr.get("row_count", len(dr["data"]["rows"]))
            if n >= 2000:
                warn("drill", f"{name}: shows {val}, drill capped at 2000 rows — verify with SQL")
            elif str(val) == str(n):
                okk("drill", f"{name}: shows {val} → drill opens {n} rows")
            else:
                fail("drill", f"{name}: shows {val} but drill opens {n} rows (see playbooks/drilldown-issues.md)")
        # speed
        if not a.no_run:
            _, secs = card_query(api, cid, tag_params(tags, filters))
            if secs > SLOW:
                fail("speed", f"{name}: {secs:.1f}s (over {SLOW}s — will time out; see skills/report-performance)")
            elif secs > FAST:
                warn("speed", f"{name}: {secs:.1f}s (goal ≤{FAST}s)")
            else:
                okk("speed", f"{name}: {secs:.1f}s")
        # sql review
        if sql:
            iss = review(sql)
            e = [m for l, r, m in iss if l == "error"]
            w = [m for l, r, m in iss if l == "warn"]
            if e:
                fail("sql", f"{name}: {e[0]}" + (f" (+{len(e)-1} more)" if len(e) > 1 else ""))
            elif w:
                warn("sql", f"{name}: {len(w)} warning(s) — run tools/sql_review.py --card {cid}")
    for p in params:
        if p["id"] not in mapped_any:
            fail("wiring", f"dashboard filter {p['name']!r} is connected to NO card")

    titles = {"filters": "Filters are dropdowns", "wiring": "Filters connected", "clicks": "Numbers clickable",
              "drill": "Drill shows exactly the number", "speed": f"Cards load fast (≤{FAST}s)", "sql": "SQL review"}
    total_fail = 0
    for k, title in titles.items():
        items = res[k]
        f = sum(1 for s, _ in items if s == "✗"); w = sum(1 for s, _ in items if s == "!")
        total_fail += f
        head = "✅" if not f and not w else ("❌" if f else "⚠️")
        print(f"\n{head} {title}: {sum(1 for s,_ in items if s=='✓')} ok, {w} warning(s), {f} problem(s)")
        for s, m in items:
            if s != "✓" or a.verbose:
                print(f"   {s} {m}")
    sys.exit(1 if total_fail else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("except-all"); p.add_argument("old"); p.add_argument("new"); p.add_argument("--mb-db", type=int)
    p = sp.add_parser("drill"); p.add_argument("--metric", type=int, required=True); p.add_argument("--drill", type=int, required=True)
    p = sp.add_parser("uuid-scan"); p.add_argument("cards", type=int, nargs="+")
    p = sp.add_parser("time"); p.add_argument("cards", type=int, nargs="+")
    p = sp.add_parser("audit-dash"); p.add_argument("id", type=int)
    p.add_argument("--param", action="append", help="test with a filter set, e.g. --param block=Kuniya (repeatable)")
    p.add_argument("--no-run", action="store_true", help="config checks only (no queries)")
    p.add_argument("--max-cards", type=int, default=999); p.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    if a.cmd == "except-all":
        return except_all(a)
    api = mb()
    if a.cmd == "audit-dash":
        return audit_dash(api, a)
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
            flag = "✗ too slow" if cold > SLOW else ("! slow (goal ≤%ds)" % FAST if cold > FAST else "✓")
            print(f"card {cid}: cold {cold:.1f}s  warm {warm:.1f}s  {flag}")


if __name__ == "__main__":
    main()
