# Session Skill Invocation

PROVIDES the declared invocation surface of the `/handoff` and `/pickup` session skills — their argument-hint flags and the live `spx session` queue state each skill injects into its context block
SO THAT an agent closing or resuming spec-tree work
CAN select the supported flags and read the current session queue at the moment of invocation, reaching the session workflows only through their skills

## Assertions

### Compliance

- ALWAYS: the `/handoff` skill declares `argument-hint: "[--no-session] [--prune]"` in its frontmatter ([audit])
- ALWAYS: the `/pickup` skill declares `argument-hint: "[--list] [--auto-continue]"` in its frontmatter ([audit])
- NEVER: the `/handoff` skill injects an unbounded `spx session list` into its context block; session queue reads occur only in the workflow step that consumes them and use status filters when queue inspection is needed ([audit])
- ALWAYS: the `/pickup` skill injects `spx session todo` into its context block, surfacing available sessions at invocation ([audit])
- ALWAYS: the `/pickup` workflow invokes `/understand` before processing session details, and leaves node-local `PLAN.md` / `ISSUES.md` content reads to `/contextualize` before those coordination notes steer work ([audit])
- NEVER: expose the `/handoff` or `/pickup` session workflows through a slash-command shim — session workflows are reached only through their skills ([test](tests/test_session_skill_invocation.compliance.l1.py))
- ALWAYS: `--prune` deletes archive sessions only after the canonical continuation is written ([audit])
