#!/usr/bin/env bash
# Install a pre-commit hook that runs the public-safety scan and skill lint on every commit.
set -euo pipefail
cd "$(dirname "$0")/.."
cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
bash scripts/check_public_safety.sh $(git diff --cached --name-only --diff-filter=ACM) || exit 1
python3 scripts/lint_skills.py || exit 1
HOOK
chmod +x .git/hooks/pre-commit
echo "✓ pre-commit hook installed"
