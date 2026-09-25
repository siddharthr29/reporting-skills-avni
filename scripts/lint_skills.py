#!/usr/bin/env python3
"""Lint the skill pack: frontmatter present and valid, name == folder, sizes sane, evals parse,
referenced repo paths exist."""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errs = []

for path in sorted(glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md"))):
    folder = os.path.basename(os.path.dirname(path))
    text = open(path).read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        errs.append(f"{folder}: missing YAML frontmatter"); continue
    fm = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
    name, desc = fm.get("name", "").strip(), fm.get("description", "").strip()
    if name != folder:
        errs.append(f"{folder}: frontmatter name '{name}' != folder")
    if not (40 <= len(desc) <= 1024):
        errs.append(f"{folder}: description length {len(desc)} (want 40–1024)")
    n = text.count("\n")
    if n > 200:
        errs.append(f"{folder}: SKILL.md is {n} lines — move detail into references/")

for path in sorted(glob.glob(os.path.join(ROOT, "evals", "cases", "*.json"))):
    try:
        c = json.load(open(path))
        for k in ("prompt", "must_include"):
            assert k in c, f"missing '{k}'"
    except Exception as e:
        errs.append(f"{os.path.relpath(path, ROOT)}: {e}")

# referenced repo paths in markdown must exist
for md in glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True):
    if "/schemas/" in md or "/backups/" in md:
        continue
    for ref in re.findall(r"`((?:skills|playbooks|sql|tools|templates|labs|evals|scripts|docs)/[A-Za-z0-9_./\-]+)`", open(md).read()):
        ref = ref.rstrip(".")
        if "<" in ref or "*" in ref or ref.endswith(".env"):
            continue
        if not os.path.exists(os.path.join(ROOT, ref)):
            errs.append(f"{os.path.relpath(md, ROOT)}: broken reference `{ref}`")

print("\n".join(errs) if errs else "✓ skills lint clean")
sys.exit(1 if errs else 0)
