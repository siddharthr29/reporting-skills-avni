#!/usr/bin/env python3
"""Read-only query through the tunnel, with the schema-first guard and PII masking.

  ./tools/q.sh "select a.\"Block\", count(*) from sangwari.individual i join sangwari.address a on ... group by 1"
  ./tools/q.sh -f card.sql [--limit 50]

- Refuses anything that isn't a read.
- Refuses org schemas that haven't been dumped locally (./tools/dump_org_schema.sh <schema>).
- Metabase [[ ... ]] optional filter blocks are stripped.
- Personal data in the output (names, phones, Aadhaar, DOB, address, GPS…) is masked before printing.
"""
import csv, io, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load_env, strip_optional, template_vars, die
from _guard import require_catalog
from _pii import print_table

READ_LEADS = ("select", "with", "explain", "show", "values", "table")


def main():
    args = sys.argv[1:]
    limit = 50
    if "--limit" in args:
        i = args.index("--limit"); limit = int(args[i + 1]); del args[i:i + 2]
    if not args:
        sys.exit(__doc__)
    sql = open(args[1]).read() if args[0] == "-f" else args[0]
    sql = strip_optional(sql).strip().rstrip(";")
    if template_vars(sql):
        die(f"required variables remain {template_vars(sql)} — substitute test values first")
    body = re.sub(r"--[^\n]*|/\*.*?\*/", " ", sql, flags=re.S)
    for st in [s for s in body.split(";") if s.strip()]:
        lead = re.match(r"\s*([A-Za-z_]+)", st)
        if not lead or lead.group(1).lower() not in READ_LEADS:
            die(f"refusing non-read statement: {(lead.group(1) if lead else st[:15])!r}")
    require_catalog(sql)

    env = load_env()
    penv = dict(os.environ, **{k: v for k, v in env.items() if k.startswith("PG")},
                PGHOST="localhost", PGPORT=env.get("LOCAL_PORT", "5433"),
                PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=300000")
    r = subprocess.run([env.get("PSQL", "psql"), "-X", "--csv", "-v", "ON_ERROR_STOP=1",
                        "-c", "begin transaction read only", "-c", sql, "-c", "commit"],
                       capture_output=True, text=True, env=penv)
    if r.returncode:
        die(r.stderr.strip()[:800] + "\n(tunnel up?  ./tools/tunnel.sh up)")
    text = r.stdout
    for noise in ("BEGIN\n", "COMMIT\n"):
        text = text.replace(noise, "")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        print("(no rows)"); return
    print_table(rows[0], rows[1:], limit)


if __name__ == "__main__":
    main()
