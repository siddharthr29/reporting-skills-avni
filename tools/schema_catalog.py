#!/usr/bin/env python3
"""Compact, token-cheap catalogue of ONE Avni ETL schema, for agents to grep.

    python3 tools/schema_catalog.py <schema> [--exact]  > schemas/<schema>/CATALOG.md

Uses planner stats (pg_class.reltuples, pg_stats) so it does NOT scan tables — fast and light on the
replica. --exact adds real row counts (one count(*) per table; slower).
Low-cardinality text columns list their common values (coded answers) — except columns whose name
suggests personal data. The output is gitignored; never commit it.
Requires the tunnel (tools/tunnel.sh up) and tools/.env.
"""
import os, re, subprocess, sys, datetime

TOOLS = os.path.dirname(os.path.abspath(__file__))
STD = {"id", "uuid", "is_voided", "organisation_id", "created_by_id", "last_modified_by_id",
       "created_date_time", "last_modified_date_time", "created_by", "last_modified_by",
       "legacy_id", "sync_concept_1_value", "sync_concept_2_value"}
PII = re.compile(r"name|phone|mobile|contact|aadha|email|address|house|father|mother|husband|guardian|"
                 r"dob|birth_?date|uuid|_id$|^id$|remark|comment|note|landmark|pin", re.I)


def env():
    e = dict(os.environ)
    path = os.path.join(TOOLS, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                e.setdefault(k.strip(), v.strip())
    e.update(PGHOST="localhost", PGPORT=e.get("LOCAL_PORT", "5433"),
             PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=120000")
    return e


ENV = env()
PSQL = ENV.get("PSQL", "psql")


def q(sql):
    r = subprocess.run([PSQL, "-X", "-At", "-F", "\t", "-c", sql], capture_output=True, text=True, env=ENV)
    if r.returncode:
        sys.exit(f"query failed: {r.stderr.strip()[:300]}")
    return [l.split("\t") for l in r.stdout.splitlines() if l]


def main():
    if len(sys.argv) < 2 or not re.fullmatch(r"[a-z0-9_]+", sys.argv[1]):
        sys.exit(__doc__)
    s, exact = sys.argv[1], "--exact" in sys.argv

    rels = q(f"""select c.relname, c.relkind, c.reltuples::bigint
                 from pg_class c join pg_namespace n on n.oid = c.relnamespace
                 where n.nspname = '{s}' and c.relkind in ('r','v','m','p') order by 1""")
    if not rels:
        sys.exit(f"no tables in schema '{s}' (wrong name? ETL not enabled?)")
    cols = {}
    for t, c, dt in q(f"""select table_name, column_name, data_type from information_schema.columns
                          where table_schema = '{s}' order by table_name, ordinal_position"""):
        cols.setdefault(t, []).append((c, dt))
    stats = {(t, c): (float(nf or 0), float(nd or 0), mcv) for t, c, nf, nd, mcv in q(
        f"""select tablename, attname, null_frac, n_distinct, coalesce(most_common_vals::text,'')
            from pg_stats where schemaname = '{s}'""")}

    out = [f"# Catalogue: `{s}` — generated {datetime.date.today()}",
           "",
           f"Standard columns omitted per table: {', '.join(sorted(STD))}.",
           "Legend: `[a|b|…]` common values · `(empty)` never filled · `~N% null` · `UUID-array` JSON list of "
           "subject UUIDs · `(63-char, truncated)` name cut by Postgres · row counts are "
           + ("exact." if exact else "planner estimates (~)."),
           ""]
    for name, kind, est in rels:
        kind_s = {"v": "view", "m": "matview"}.get(kind, "")
        if exact and kind in ("r", "p", "m"):
            n = q(f'select count(*) from "{s}"."{name}"')[0][0]
            size = f"{int(n):,} rows"
        elif kind_s:
            size = kind_s
        elif int(est) < 0:
            size = "size unknown — never analysed; use --exact"   # reltuples = -1, NOT the same as empty
        else:
            size = f"~{int(est):,} rows"
        head = f"## {name}  ({size})"
        if name.endswith("_coded"):
            head += "  — coded EAV: one row per selected answer (id, concept_name, answer)"
        parts = []
        for c, dt in cols.get(name, []):
            if c in STD:
                continue
            nf, nd, mcv = stats.get((name, c), (0.0, 0.0, ""))
            tag = f"{'`'+c+'`' if c.islower() and ' ' not in c else chr(34)+c+chr(34)} {dt}"
            if len(c) >= 63:
                tag += " (63-char, truncated)"
            if nf >= 0.999:
                tag += " (empty)"
            elif nf >= 0.2:
                tag += f" ~{round(nf*100)}% null"
            if mcv.startswith('{"[') or mcv.startswith("{[\""):
                tag += " UUID-array"
            elif (dt in ("text", "character varying") and 0 < nd <= 30 and mcv
                  and not PII.search(c)):
                vals = [v.strip('"') for v in re.findall(r'"(?:[^"\\]|\\.)*"|[^,{}]+', mcv.strip("{}"))]
                tag += " [" + "|".join(vals[:12]) + ("|…" if len(vals) > 12 else "") + "]"
            parts.append(tag)
        out.append(head)
        out.append(" · ".join(parts) if parts else "(standard columns only)")
        out.append("")
    print("\n".join(out))


if __name__ == "__main__":
    main()
