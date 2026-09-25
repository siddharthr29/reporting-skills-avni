# Evals — does an agent actually "get" this pack?

Each `cases/*.json` has a `prompt`, phrases the answer **must include**, and phrases it **must not include** (dangerous or wrong advice).

## Run
1. Open a fresh agent session in this repo (Claude Code, Cursor, Codex…).
2. Paste a case's `prompt`. Save the agent's answer to `answers/<case>.txt` (gitignored folder is fine).
3. `python3 evals/check.py` scores every case that has an answer file.

## When to run
- After `/curate` or any skill edit.
- When trying a new agent/model (compare scores).
- Every **correction** learning must add a case here so the mistake can't come back.

Matching is case-insensitive substring matching. Keep phrases short and unambiguous.
