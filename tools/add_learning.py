#!/usr/bin/env python3
"""Append a learning to LEARNINGS.md — refuses anything the public-safety scan flags.

  python3 tools/add_learning.py --type pitfall --tool metabase --org "Khel Mel" \
      --title "Crossfilter does nothing on scalar cards" \
      --symptom "Clicking a scalar did not filter the line list" \
      --cause "crossfilter click_behavior unreliable on scalar dashcards" \
      --fix "used link-to-question to a per-metric drill; verified metric==drill" \
      --source "ticket <number>"
"""
import argparse, datetime, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(ROOT, "LEARNINGS.md")
END = "<!-- LEARNINGS END -->"
TYPES = ["pitfall", "fix", "pattern", "correction", "org-fact", "tool-behaviour"]
TOOLS = ["metabase", "superset", "jasper", "sql", "etl", "process"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--type", choices=TYPES, required=True)
    ap.add_argument("--tool", choices=TOOLS, required=True)
    ap.add_argument("--org", default="-")
    for f in ("title", "symptom", "cause", "fix"):
        ap.add_argument(f"--{f}", required=True)
    ap.add_argument("--source", default="-")
    a = ap.parse_args()

    block = (f"### {datetime.date.today()} · {a.type} · {a.tool} · {a.org} — {a.title}\n"
             f"- **Symptom:** {a.symptom}\n- **Cause:** {a.cause}\n- **Fix:** {a.fix}\n- **Source:** {a.source}\n\n")

    # Safety scan on the new text before it touches the repo.
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as t:
        t.write(block)
    scan = subprocess.run(["bash", os.path.join(ROOT, "scripts", "check_public_safety.sh"), t.name],
                          capture_output=True, text=True)
    os.unlink(t.name)
    if scan.returncode:
        sys.exit("REFUSED — remove secrets / emails / hosts / raw IDs (use <DB_ID> etc.):\n" + scan.stdout + scan.stderr)

    text = open(INBOX).read()
    if a.title.lower() in text.lower():
        sys.exit("Looks like a duplicate (same title already in LEARNINGS.md). Edit that entry instead.")
    if END not in text:
        sys.exit(f"{END} marker missing in LEARNINGS.md")
    open(INBOX, "w").write(text.replace(END, block + END))
    print(f"✓ added to LEARNINGS.md: {a.title}")
    if a.type == "correction":
        print("! correction: also fix the wrong skill text now and add an evals/cases/*.json case (see /curate).")


if __name__ == "__main__":
    main()
