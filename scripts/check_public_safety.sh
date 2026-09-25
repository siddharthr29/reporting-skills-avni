#!/usr/bin/env bash
# Public-safety scan: fails if a file contains secrets, internal hosts, emails, raw BI object IDs,
# or forbidden files. Runs in CI, pre-commit, and inside tools/add_learning.py.
#   scripts/check_public_safety.sh              # scan the repo (tracked + untracked, not ignored)
#   scripts/check_public_safety.sh file1 file2  # scan specific files
# Suppress a deliberate false positive by ending that line with:  safety:allow
cd "$(dirname "$0")/.." || exit 2
exec python3 - "$@" <<'PY'
import os, re, subprocess, sys

RULES = [
  ("metabase api key",   r"\bmb_[A-Za-z0-9+/=]{20,}"),
  ("secret assignment",  r"(?i)\b(password|passwd|pgpassword|secret|api[_-]?key|token|pw)\b[\"']?\s*[:=]\s*[\"']?(?![<$\"'{(]|ENV\b|env\b|os\.|getpass|args?\.|self\.)[A-Za-z0-9@#%^&*!_+\-./]{6,}"),
  ("bearer/basic token", r"(?i)\b(bearer|basic)\s+[A-Za-z0-9+/=_\-.]{24,}"),
  ("private key",        r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
  ("pem file name",      r"\b[a-z0-9_\-]+\.pem\b"),
  ("internal host",      r"(?i)\b[a-z0-9.\-]*openchs\.org\b|\b(ssh|serverdb|stagingdb)\.[a-z0-9.\-]*avniproject\.org\b"),
  ("email address",      r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.(com|org|in|net|io|co)\b"),
  ("raw BI object id",   r"(?i)\b(database|db|card|dashboard|dash|dataset|collection|chart|slice)(_id|\s+id)?\s*[#:=]?\s*[\"']?\d{2,}\b"),
  ("BI object url",      r"(?i)(/question/|/dashboard/|slice_id=)\d+"),
]
BAD_FILES = re.compile(r"(^|/)(\.env|g_token\.json|g_client\.json|audit\.log)$|\.pem$")
BINARY = re.compile(r"\.(png|jpe?g|gif|ico|pdf|woff2?)$", re.I)
SELF = "scripts/check_public_safety.sh"

files = sys.argv[1:]
if not files:
    try:
        out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, text=True, check=True).stdout
        files = out.splitlines()
    except Exception:
        files = [os.path.relpath(os.path.join(d, f)) for d, _, fs in os.walk(".") for f in fs
                 if not d.startswith(("./.git", "./backups", "./schemas"))]

fails = 0
for f in files:
    if BINARY.search(f) or not os.path.isfile(f):
        continue
    if BAD_FILES.search(f):
        print(f"{f}: forbidden file in repo"); fails += 1; continue
    if f.endswith(SELF):
        continue
    try:
        lines = open(f, encoding="utf-8").read().splitlines()
    except UnicodeDecodeError:
        continue
    for n, line in enumerate(lines, 1):
        if "safety:allow" in line:
            continue
        for name, rx in RULES:
            m = re.search(rx, line)
            if m:
                print(f"{f}:{n}: {name}: …{line[max(0, m.start()-20):m.end()+20].strip()}…"); fails += 1

print("✓ public-safety scan clean" if not fails else f"✗ public-safety scan: {fails} issue(s) — use placeholders like <DB_ID>")
sys.exit(1 if fails else 0)
PY
