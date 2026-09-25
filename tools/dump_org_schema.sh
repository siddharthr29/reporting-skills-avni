#!/usr/bin/env bash
# Dump ONE org's ETL schema locally so agents grep a file instead of querying the DB.
#   ./tools/dump_org_schema.sh <schema>            e.g. sangwari
#   ./tools/dump_org_schema.sh <schema> --exact    exact row counts (slower; default = planner estimates)
# Output (gitignored):  schemas/<schema>/ddl.sql      full DDL (tables, views, columns, types)
#                       schemas/<schema>/CATALOG.md   compact, token-cheap summary for agents
set -euo pipefail
. "$(dirname "$0")/_env.sh"
load_env
SCHEMA="${1:?usage: dump_org_schema.sh <schema> [--exact]}"; shift || true
[[ "$SCHEMA" =~ ^[a-z0-9_]+$ ]] || { err "schema must be lowercase letters/digits/_"; exit 1; }
tunnel_is_up || { err "tunnel down — run ./tools/tunnel.sh up"; exit 1; }

OUT="$REPO_ROOT/schemas/$SCHEMA"; mkdir -p "$OUT"
PGDUMP="${PGDUMP:-$(dirname "$(command -v "$PSQL")")/pg_dump}"; [ -x "$PGDUMP" ] || PGDUMP=pg_dump

log "→ DDL (schema-only, no data) ..."
if "$PGDUMP" --schema-only --no-owner --no-privileges --no-comments -n "$SCHEMA" > "$OUT/ddl.sql" 2>"$OUT/.pg_dump.err"; then
  ok "ddl.sql ($(grep -c '^CREATE TABLE' "$OUT/ddl.sql") tables, $(grep -c '^CREATE VIEW' "$OUT/ddl.sql") views)"
else
  err "pg_dump failed (version mismatch?): $(head -2 "$OUT/.pg_dump.err") — continuing with the catalogue only"
fi

log "→ CATALOG.md ..."
python3 "$(dirname "$0")/schema_catalog.py" "$SCHEMA" "$@" > "$OUT/CATALOG.md"
ok "$(wc -l < "$OUT/CATALOG.md") lines → schemas/$SCHEMA/CATALOG.md"
log "Tip: agents should grep this file, e.g.  grep -n -i 'weight' schemas/$SCHEMA/CATALOG.md"
