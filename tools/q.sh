#!/usr/bin/env bash
# Read-only query through the tunnel: schema-first guard + PII masking. See tools/q.py.
#   ./tools/q.sh "select count(*) from sangwari.individual where is_voided = false"
#   ./tools/q.sh -f card.sql [--limit 50]
exec python3 "$(dirname "$0")/q.py" "$@"
