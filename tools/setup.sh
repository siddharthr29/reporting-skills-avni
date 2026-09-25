#!/usr/bin/env bash
# First-time setup: every person enters THEIR OWN Metabase API key and Superset login.
# Writes tools/.env (private to you, never committed) and checks each login works.
#   ./tools/setup.sh
set -uo pipefail
TOOLS="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${AVNI_REPORTING_ENV:-$TOOLS/.env}"
ME="$(id -un)"

say()  { printf '%s\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$*"; }
old()  { [ -f "$ENV_FILE" ] && grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- || true; }
ask()  { # ask VAR "Question" [secret] [default]
  local var="$1" q="$2" secret="${3:-}" def="${4:-}" v
  if [ -n "$secret" ]; then read -r -s -p "  $q: " v; echo; else
    read -r -p "  $q${def:+ [$def]}: " v; fi
  v="${v:-$def}"; printf -v "$var" '%s' "$v"
}

say ""
say "Avni reporting — setup for: $ME"
say "Use YOUR OWN logins. Never use or share someone else's. Nothing you type is shown or committed."
say ""

if [ -f "$ENV_FILE" ] && [ "$(old SETUP_BY)" != "$ME" ]; then
  say "  A settings file exists but was not created by you ($(old SETUP_BY || echo unknown)). It will be replaced."
fi

say "1) Your Metabase API key"
say "   Ask your admin to create an API key named after you (Metabase → Admin → Authentication → API keys)."
while :; do
  ask MB_KEY "Paste your Metabase API key (starts with mb_)" secret
  case "$MB_KEY" in mb_*) break ;; *) bad "That doesn't look like a Metabase API key (should start with mb_). Try again." ;; esac
done

say ""
say "2) Your Superset login (the one you use at reporting-superset.avniproject.org)"
while :; do ask SS_USER "Superset username"; [ -n "$SS_USER" ] && break; bad "Username can't be empty."; done
while :; do ask SS_PASS "Superset password" secret; [ -n "$SS_PASS" ] && break; bad "Password can't be empty."; done

say ""
say "3) Database access (your lead gives you these; press Enter to keep the value shown)"
ask SSH_KEY  "Path to your SSH key file" "" "$(old SSH_KEY)"
ask SSH_USER "SSH user" "" "$(old SSH_USER)"
ask SSH_JUMP "SSH jump host" "" "$(old SSH_JUMP_HOST)"
ask DB_HOST  "Read database host" "" "$(old READ_DB_HOST)"
ask PG_USER  "Database user" "" "$(old PGUSER)"
PG_PASS_OLD="$(old PGPASSWORD)"
ask PG_PASS  "Database password (Enter = keep existing)" secret
PG_PASS="${PG_PASS:-$PG_PASS_OLD}"
PSQL_BIN="$(old PSQL)"; PSQL_BIN="${PSQL_BIN:-$(command -v psql || echo psql)}"

umask 077
cat > "$ENV_FILE" <<EOF
# Personal settings of $ME — created $(date +%Y-%m-%d) by tools/setup.sh.
# These are YOUR credentials. Do not share this file or copy it to anyone. Never commit it.
SETUP_BY=$ME
METABASE_URL=https://reporting.avniproject.org
METABASE_API_KEY=$MB_KEY
SUPERSET_URL=https://reporting-superset.avniproject.org
SUPERSET_USER=$SS_USER
SUPERSET_PASSWORD=$SS_PASS
SSH_KEY=$SSH_KEY
SSH_USER=$SSH_USER
SSH_JUMP_HOST=$SSH_JUMP
READ_DB_HOST=$DB_HOST
LOCAL_PORT=5433
PGUSER=$PG_USER
PGPASSWORD=$PG_PASS
PGDATABASE=openchs
PSQL=$PSQL_BIN
EOF
chmod 600 "$ENV_FILE"
ok "saved your settings (only you can read the file)"

say ""
say "Checking your logins…"
if python3 "$TOOLS/mb.py" whoami >/tmp/.avni_mb_$$ 2>&1; then ok "Metabase: $(tail -1 /tmp/.avni_mb_$$)"; else bad "Metabase login failed: $(tail -1 /tmp/.avni_mb_$$) — re-run ./tools/setup.sh"; fi
if python3 "$TOOLS/ss.py"  whoami >/tmp/.avni_ss_$$ 2>&1; then ok "Superset: $(tail -1 /tmp/.avni_ss_$$)"; else bad "Superset login failed: $(tail -1 /tmp/.avni_ss_$$ | cut -c1-120) — re-run ./tools/setup.sh"; fi
rm -f /tmp/.avni_mb_$$ /tmp/.avni_ss_$$
say ""
say "Next: ./tools/tunnel.sh up   (tests database access), then open Claude in this folder."
