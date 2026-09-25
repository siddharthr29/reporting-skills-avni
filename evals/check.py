#!/usr/bin/env python3
"""Score agent answers against evals/cases/*.json. Answers: evals/answers/<case>.txt"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
passed = total = 0
for path in sorted(glob.glob(os.path.join(HERE, "cases", "*.json"))):
    name = os.path.splitext(os.path.basename(path))[0]
    ans = os.path.join(HERE, "answers", f"{name}.txt")
    if not os.path.exists(ans):
        print(f"  ·  {name}: no answer file"); continue
    case, text = json.load(open(path)), open(ans).read().lower()
    miss = [p for p in case["must_include"] if p.lower() not in text]
    bad = [p for p in case.get("must_not_include", []) if p.lower() in text]
    total += 1
    ok = not miss and not bad
    passed += ok
    print(f"  {'✓' if ok else '✗'}  {name}" + (f"  missing={miss}" if miss else "") + (f"  forbidden={bad}" if bad else ""))
print(f"\n{passed}/{total} passed")
sys.exit(0 if total and passed == total else 1)
