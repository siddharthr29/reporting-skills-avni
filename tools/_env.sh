#!/usr/bin/env bash
# Shared helpers: load tools/.env and set read-only Postgres connection env. Source, don't run.
TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO_ROOT; REPO_ROOT="$(cd "$TOOLS_DIR/.." && pwd)"   # used by scripts that source this file
ENV_FILE="${AVNI_REPORTING_ENV:-$TOOLS_DIR/.env}"

log()  { printf '%s\n' "$*" >&2; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*" >&2; }
err()  { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; }

load_env() {
  [ -f "$ENV_FILE" ] || { err "no settings yet — run ./tools/setup.sh (enter YOUR OWN logins)"; exit 1; }
  local by; by=$(grep -E '^SETUP_BY=' "$ENV_FILE" | cut -d= -f2- || true)
  if [ "$by" != "$(id -un)" ]; then
    err "these settings were not created by you (created by: ${by:-unknown}; you are: $(id -un))."
    err "Everyone must use their own credentials. Run: ./tools/setup.sh"; exit 1
  fi
  set -a; # shellcheck disable=SC1090
  . "$ENV_FILE"; set +a
  SSH_KEY="${SSH_KEY/#\~/$HOME}"
  export PGHOST=localhost PGPORT="${LOCAL_PORT:-5433}"
  # Every session through these tools is read-only at the server level.
  export PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=300000"
  PSQL="${PSQL:-psql}"
}

tunnel_is_up() { lsof -ti "tcp:${LOCAL_PORT:-5433}" >/dev/null 2>&1; }
