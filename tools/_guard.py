"""Schema-first guard: any SQL touching an org schema requires that schema's local catalogue.

Why: agents must grep schemas/<schema>/CATALOG.md instead of exploring the live DB — fewer tokens,
fewer API/DB calls. The dump is one command: ./tools/dump_org_schema.sh <schema>
"""
import os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXEMPT = {"public", "information_schema", "pg_catalog", "pg_temp"}
STALE_DAYS = 14


def schemas_in(sql):
    s = re.sub(r"--[^\n]*|/\*.*?\*/", " ", sql, flags=re.S)
    found = re.findall(r'\b(?:from|join)\s+"?([A-Za-z_][A-Za-z0-9_]*)"?\s*\.', s, flags=re.I)
    return sorted({f.lower() for f in found} - EXEMPT)


def require_catalog(sql):
    missing, stale = [], []
    for sch in schemas_in(sql):
        cat = os.path.join(ROOT, "schemas", sch, "CATALOG.md")
        if not os.path.exists(cat):
            missing.append(sch)
        elif time.time() - os.path.getmtime(cat) > STALE_DAYS * 86400:
            stale.append(sch)
    if missing:
        cmds = "\n".join(f"    ./tools/dump_org_schema.sh {m}" for m in missing)
        sys.exit("STOP — dump the schema locally first (saves tokens and DB/API calls):\n" + cmds +
                 "\nThen read schemas/<schema>/CATALOG.md to find tables and columns.")
    for s in stale:
        print(f"! schemas/{s}/CATALOG.md is over {STALE_DAYS} days old — re-dump if a column seems missing.",
              file=sys.stderr)
