#!/usr/bin/env bash
# Shared helpers: load tools/.env and set read-only Postgres connection env. Source, don't run.
TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$TOOLS_DIR/.." && pwd)"
ENV_FILE="${AVNI_REPORTING_ENV:-$TOOLS_DIR/.env}"

log()  { printf '%s\n' "$*" >&2; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*" >&2; }
err()  { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; }

load_env() {
  [ -f "$ENV_FILE" ] || { err "missing $ENV_FILE — copy tools/.env.example to tools/.env"; return 1; }
  set -a; # shellcheck disable=SC1090
  . "$ENV_FILE"; set +a
  SSH_KEY="${SSH_KEY/#\~/$HOME}"
  export PGHOST=localhost PGPORT="${LOCAL_PORT:-5433}"
  # Every session through these tools is read-only at the server level.
  export PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=300000"
  PSQL="${PSQL:-psql}"
}

tunnel_is_up() { lsof -ti "tcp:${LOCAL_PORT:-5433}" >/dev/null 2>&1; }
