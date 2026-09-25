#!/usr/bin/env python3
"""SQL code review for Avni report queries — catches the mistakes that made reports wrong or slow.

  python3 tools/sql_review.py card.sql [more.sql …] [--explain]
  python3 tools/sql_review.py --card <CARD_ID> [--explain]        (reads the live Metabase card)

Static checks always run. --explain also asks Postgres for the plan (read-only, through the tunnel;
no rows are read) and flags big sequential scans and sorts.
Exit code: 0 = no errors (warnings allowed), 1 = errors.
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import strip_optional, template_vars

BIG_PUBLIC = r"public\.(concept|entity_approval_status|checklist\w*|form_element\w*|individual|encounter|program_encounter)"


def strip_comments(sql):
    return re.sub(r"--[^\n]*|/\*.*?\*/", " ", sql, flags=re.S)


def blank_quoted(s):
    """Replace the inside of "quoted identifiers" and 'string literals' so words in them aren't parsed as SQL."""
    s = re.sub(r'"[^"]*"', lambda m: '"' + "q" * (len(m.group(0)) - 2) + '"', s)
    return re.sub(r"'[^']*'", lambda m: "'" + "s" * (len(m.group(0)) - 2) + "'", s)


def cte_blocks(sql):
    """Return {cte_name: body} for top-level WITH ... AS (...) blocks."""
    out, s = {}, sql
    for m in re.finditer(r'(?:\bwith\b|,)\s*(?:recursive\s+)?"?([A-Za-z_][A-Za-z0-9_]*)"?\s+as\s+(?:not\s+)?(?:materialized\s+)?\(',
                         s, re.I):
        depth, i = 1, m.end()
        while i < len(s) and depth:
            depth += {"(": 1, ")": -1}.get(s[i], 0)
            i += 1
        out[m.group(1)] = s[m.end():i - 1]
    return out


def review(sql, name="query"):
    issues = []   # (level, rule, message)
    add = lambda lvl, rule, msg: issues.append((lvl, rule, msg))
    raw = strip_comments(sql)
    low = raw.lower()

    # Metabase optional blocks
    for blk in re.findall(r"\[\[(.*?)\]\]", raw, flags=re.S):
        if not re.search(r"\{\{\s*\w+\s*\}\}", blk):
            add("error", "filter-block", "[[ … ]] block without a {{variable}} — Metabase will reject it")
        if re.search(r"\bor\b", blk, re.I):
            add("error", "filter-block-or", "[[ … ]] block contains OR — move that logic into a CTE, keep [[ and x = {{v}} ]] simple")
    body = strip_optional(raw)
    blow = body.lower()
    bq = blank_quoted(blow)          # for table/keyword scans only

    # 1. voided rows: tables that decide WHAT is counted must filter is_voided; LEFT JOIN lookups only label rows
    for kw, sch, tbl, alias in re.findall(
            r'\b(left\s+(?:outer\s+)?join|join|from)\s+"?([a-z_][a-z0-9_]*)"?\."?([a-z_][a-z0-9_]*)"?\s+(?:as\s+)?"?([a-z_][a-z0-9_]*)?', bq):
        if sch in ("public", "pg_catalog", "information_schema") or tbl.endswith(("_view", "_coded")):
            continue
        al = alias if alias and alias not in ("on", "where", "left", "join", "inner", "group", "order", "limit", "cross") else tbl
        if re.search(rf'\b({re.escape(al)}|{re.escape(tbl)})\.is_voided\b', blow):
            continue
        if kw.startswith("left"):
            add("info", "voided-lookup", f"{sch}.{tbl} ({al}) is a LEFT JOIN lookup without is_voided — only affects labels, not counts")
        else:
            add("warn", "voided", f"{sch}.{tbl} ({al}) has no is_voided filter — deleted records will be counted "
                                  "(skip only for 'people who left' metrics)")

    # 2. unqualified tables
    for tbl in re.findall(r'\b(?:from|join)\s+"?([a-z_][a-z0-9_]*)"?\s+(?!\.)', bq):
        if tbl in ("lateral", "unnest", "generate_series", "jsonb_array_elements_text", "jsonb_array_elements",
                   "string_to_array", "select", "values") or tbl in cte_blocks(body):
            continue
        add("warn", "schema-qualify", f"table '{tbl}' is not schema-qualified (write <schema>.{tbl})")

    # 3. dead / heavy CTEs
    ctes = cte_blocks(body)
    for cname, cbody in ctes.items():
        rest = body.replace(cbody, " ")
        refs = len(re.findall(rf'\b{re.escape(cname)}\b', rest, re.I)) - 1
        if refs <= 0:
            add("error", "dead-cte", f"CTE '{cname}' is never used — delete it (it still costs time)")
        # joined, but none of its columns used outside the ON clause → dead join (APF Odisha: 2–5 min → 0.8 s)
        for alias in re.findall(rf'\bjoin\s+"?{re.escape(cname)}"?\s+(?:as\s+)?"?([a-z_][a-z0-9_]*)"?\s+on\b', rest, re.I):
            no_on = re.sub(rf'\bjoin\s+"?{re.escape(cname)}"?\s+(?:as\s+)?"?{re.escape(alias)}"?\s+on\b.*?(?=\b(left|right|inner|full|cross|join|where|group|order|limit)\b|$)',
                           " ", rest, flags=re.I | re.S)
            if not re.search(rf'\b{re.escape(alias)}\s*\.', no_on, re.I) and \
               re.search(rf'\bleft\s+join\s+"?{re.escape(cname)}\b', rest, re.I):
                add("error", "dead-join", f"CTE '{cname}' is LEFT JOINed as '{alias}' but none of its columns are used — "
                                          "delete the CTE and the join (same output, faster)")
        if re.search(r"\b(row_number|rank|dense_rank)\s*\(\s*\)\s*over", cbody, re.I):
            add("warn", "window-cte", f"CTE '{cname}' ranks a whole table — make sure its columns are really selected; "
                                      "for 'latest per person' prefer LATERAL … LIMIT 1 (sql/patterns/lateral_top1.sql)")
    if len(ctes) >= 3 and "materialized" not in blow:
        add("info", "materialize", "3+ CTEs and none MATERIALIZED — if the outer query is small, add AS MATERIALIZED to the heavy one")

    # 4. per-row lookups on huge cross-org tables
    if re.search(r"\(\s*select[^()]{0,400}?\bfrom\s+" + BIG_PUBLIC, blow):
        add("error", "correlated-public", "per-row subquery on a huge public table — use a MATERIALIZED lookup CTE "
                                          "(sql/patterns/materialized_lookup.sql)")

    # 5. multi-select text matching
    if re.search(r"\bilike\s+'%[^']+%'", blow):
        add("warn", "ilike-multiselect", "ILIKE '%…%' — on a multi-select this also matches 'X, Other' and names containing X; "
                                         "use the _coded table (sql/patterns/coded_multiselect.sql)")

    # 6. NOT IN (subquery)
    if re.search(r"\bnot\s+in\s*\(\s*select", blow):
        add("warn", "not-in", "NOT IN (SELECT …) returns nothing if the subquery has a NULL — use NOT EXISTS")

    # 7. SELECT *
    if re.search(r"\bselect\s+\*\s+from\b", blow) and not re.search(r"select\s+\*\s+from\s+\(", blow):
        add("warn", "select-star", "SELECT * — list the columns you need (faster, and output stays stable)")

    # 8. line list without LIMIT
    final = re.split(r"\)\s*select\b", blow)[-1] if ctes else blow
    is_agg = re.search(r"\b(count|sum|avg|min|max)\s*\(|\bgroup\s+by\b", final)
    if not is_agg and "limit" not in final:
        add("warn", "limit", "line list without LIMIT — add LIMIT 2000 (Metabase shows at most 2000 rows anyway)")

    # 9. unsafe division
    for m in re.finditer(r"/\s*(?!nullif)(count|sum)\s*\(", blow):
        add("warn", "divide-by-zero", "division by count/sum without NULLIF(…, 0)")
        break

    # 10. dates without timezone
    if re.search(r"(date_trunc\s*\(\s*'\w+'\s*,\s*[\w.\"]*date_time\s*\)|[\w.\"]*date_time\s*::\s*date)", blow) \
            and "time zone" not in blow:
        add("info", "timezone", "date bucketing on a timestamp without AT TIME ZONE 'Asia/Kolkata' — late-evening entries can land on the wrong day")

    # 11. hard-coded dates
    if re.search(r"'20\d\d-\d\d-\d\d'", blow):
        add("warn", "hardcoded-date", "hard-coded date — use a {{start_date}}/{{end_date}} filter instead")

    # 12. counting rows across joins
    if re.search(r"\bcount\s*\(\s*\*\s*\)", blow) and len(re.findall(r"\bjoin\b", blow)) >= 2:
        add("info", "count-distinct", "count(*) across several joins — use count(distinct <person/encounter id>) if joins can duplicate rows")

    # 13. ORDER BY inside a CTE without LIMIT (wasted sort)
    for cname, cbody in ctes.items():
        if re.search(r"\border\s+by\b", cbody, re.I) and not re.search(r"\blimit\b|\bover\s*\(", cbody, re.I):
            add("info", "cte-order", f"ORDER BY inside CTE '{cname}' is wasted work — sort only in the final SELECT")
    return issues


def explain(sql):
    from _guard import require_catalog
    from _common import load_env
    q = strip_optional(sql).strip().rstrip(";")
    if template_vars(q):
        return [("info", "explain", f"skipped plan check: required variables {template_vars(q)} remain")]
    require_catalog(q)
    env = load_env()
    penv = dict(os.environ, **{k: v for k, v in env.items() if k.startswith("PG")}, PGHOST="localhost",
                PGPORT=env.get("LOCAL_PORT", "5433"),
                PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=60000")
    r = subprocess.run([env.get("PSQL", "psql"), "-X", "-At", "-c", f"explain (format json) {q}"],
                       capture_output=True, text=True, env=penv)
    if r.returncode:
        return [("error", "explain", "query does not run: " + r.stderr.strip()[:300])]
    plan = json.loads(r.stdout)[0]["Plan"]
    out = [("info", "plan", f"estimated cost {plan['Total Cost']:,.0f}, rows {plan['Plan Rows']:,}")]

    def walk(n):
        t, rows = n.get("Node Type"), n.get("Plan Rows", 0)
        if t == "Seq Scan" and rows > 500_000:
            out.append(("warn", "seq-scan", f"full scan of {n.get('Relation Name')} (~{rows:,} rows) — filter earlier or use an indexed key"))
        if t == "Sort" and rows > 1_000_000:
            out.append(("error", "big-sort", f"sorting ~{rows:,} rows — usually a window/DISTINCT over a whole table; see skills/report-performance"))
        if t == "SubPlan" or n.get("Parent Relationship") == "SubPlan":
            out.append(("warn", "subplan", "a subquery runs once per row — rewrite as a JOIN or MATERIALIZED CTE"))
        for c in n.get("Plans", []):
            walk(c)
    walk(plan)
    return out


def print_issues(name, issues):
    icon = {"error": "✗", "warn": "!", "info": "·"}
    errs = sum(1 for i in issues if i[0] == "error")
    warns = sum(1 for i in issues if i[0] == "warn")
    print(f"{'✓' if not errs and not warns else ('✗' if errs else '!')} {name}: {errs} error(s), {warns} warning(s)")
    for lvl, rule, msg in issues:
        print(f"   {icon[lvl]} [{rule}] {msg}")
    return errs


def main():
    args = sys.argv[1:]
    do_explain = "--explain" in args
    args = [a for a in args if a != "--explain"]
    if not args:
        sys.exit(__doc__)
    targets = []
    if args[0] == "--card":
        from mb import client, card_native
        api = client()
        for cid in args[1:]:
            c = api.get(f"/card/{cid}")
            sql, _, _ = card_native(c)
            if sql:
                targets.append((f"card {cid} {c['name']!r}", sql))
    else:
        targets = [(p, open(p).read()) for p in args]
    total = 0
    for name, sql in targets:
        issues = review(sql, name) + (explain(sql) if do_explain else [])
        total += print_issues(name, issues)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
