#!/usr/bin/env bash
# Read-only SSH tunnel to the Avni read replica.
#   ./tools/tunnel.sh up       open (idempotent) + prove writes are rejected
#   ./tools/tunnel.sh status   is it up? is the session read-only?
#   ./tools/tunnel.sh down     close it
set -euo pipefail
. "$(dirname "$0")/_env.sh"
load_env

prove_read_only() {
  local ro probe
  ro=$("$PSQL" -X -At -c "show default_transaction_read_only" 2>&1) || { err "cannot connect: $ro"; return 1; }
  [ "$ro" = "on" ] || { err "session is NOT read-only (default_transaction_read_only=$ro) — stop"; return 1; }
  # A write MUST fail. CREATE (even TEMP) is rejected in a read-only transaction.
  if probe=$("$PSQL" -X -At -c "create temp table _ro_probe(x int)" 2>&1); then
    err "a write SUCCEEDED — this connection is not safe. Close it: ./tools/tunnel.sh down"; return 1
  fi
  ok "read-only proven (write rejected: $(echo "$probe" | head -1 | cut -c1-80))"
}

case "${1:-status}" in
  up)
    if tunnel_is_up; then ok "tunnel already up on localhost:${LOCAL_PORT}"; else
      [ -f "$SSH_KEY" ] || { err "SSH key not found: $SSH_KEY"; exit 1; }
      ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
          -o ConnectTimeout=15 -o ServerAliveInterval=30 \
          -L "${LOCAL_PORT}:${READ_DB_HOST}:5432" -N -f "${SSH_USER}@${SSH_JUMP_HOST}"
      sleep 1; tunnel_is_up && ok "tunnel up on localhost:${LOCAL_PORT}" || { err "tunnel failed"; exit 1; }
    fi
    prove_read_only ;;
  status)
    if tunnel_is_up; then ok "tunnel up on localhost:${LOCAL_PORT}"; prove_read_only; else err "tunnel down"; exit 1; fi ;;
  down)
    lsof -ti "tcp:${LOCAL_PORT}" | xargs kill 2>/dev/null || true; ok "tunnel closed" ;;
  *) log "usage: $0 up|status|down"; exit 2 ;;
esac
