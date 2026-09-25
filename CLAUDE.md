@AGENTS.md

## Claude Code specifics
- Skills live in `skills/*/SKILL.md`. To use them as Claude Code skills globally: `ln -s "$PWD/skills/"* ~/.claude/skills/`.
- Auto-mode may block writes to Metabase/Superset. Stage the change as a script and give the user the command to run with `! python3 tools/<script> --apply`.
- Use sub-agents (Explore) for wide searches, and keep only conclusions in the main context.
