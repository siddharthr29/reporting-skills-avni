#!/usr/bin/env bash
# Read-only query through the tunnel. Refuses anything that isn't a read.
#   ./tools/q.sh "select count(*) from sangwari.individual where is_voided = false"
#   ./tools/q.sh -f card.sql            # Metabase [[ ]] optional blocks are stripped automatically
set -euo pipefail
. "$(dirname "$0")/_env.sh"
load_env
tunnel_is_up || { err "tunnel down — run ./tools/tunnel.sh up"; exit 1; }

if [ "${1:-}" = "-f" ]; then SQL=$(cat "$2"); else SQL="${1:?usage: q.sh \"<select>\" | -f file.sql}"; fi

# Strip Metabase optional filters [[ ... ]] (multi-line) so the SQL runs as the unfiltered card would.
SQL=$(python3 -c 'import re,sys; print(re.sub(r"\[\[.*?\]\]","",sys.stdin.read(),flags=re.S))' <<<"$SQL")
if grep -qE '\{\{[a-zA-Z_]+\}\}' <<<"$SQL"; then
  err "required {{variables}} remain — substitute test values first"; exit 1; fi

LEAD=$(python3 - "$SQL" <<'PY'
import re,sys
s=re.sub(r"--[^\n]*|/\*.*?\*/"," ",sys.argv[1],flags=re.S)
bad=[m.group(0).lower() for st in s.split(";") if st.strip()
     for m in [re.match(r"\s*([a-zA-Z_]+)",st)] if m and m.group(1).lower() not in
     ("select","with","explain","show","values","table","set","reset")]
print(",".join(bad))
PY
)
[ -z "$LEAD" ] || { err "refusing non-read statement(s): $LEAD"; exit 1; }

exec "$PSQL" -X -v ON_ERROR_STOP=1 -P pager=off -c "begin transaction read only;" -c "$SQL" -c "commit;"
