# Session Skill Invocation

PROVIDES the declared invocation surface of the `/handoff` and `/pickup` session skills — their argument-hint flags, argument bindings, and bounded queue reads
SO THAT an agent closing or resuming spec-tree work
CAN select the supported flags and reach session queue state only at the workflow step that consumes it

## Assertions

### Compliance

- ALWAYS: the `/handoff` skill declares `argument-hint: "[--no-session] [--prune]"` in its frontmatter ([audit])
- ALWAYS: the `/handoff` skill declares `arguments: [session_mode, prune_mode]` in its frontmatter, binding supported flags to `$session_mode` and `$prune_mode` ([audit])
- ALWAYS: the `/pickup` skill declares `argument-hint: "[--list] [--auto-continue]"` in its frontmatter ([audit])
- NEVER: the `/handoff` skill injects `spx session list` output into its context block; session queue reads occur only in the workflow step that consumes them and use status filters when queue inspection is needed ([audit])
- ALWAYS: the `/pickup` skill injects `spx session todo` into its context block, surfacing available sessions at invocation ([audit])
- ALWAYS: the `/pickup` workflow invokes `/understand` before processing session details, and leaves node-local `PLAN.md` / `ISSUES.md` content reads to `/contextualize` before those coordination notes steer work ([audit])
- NEVER: expose the `/handoff` or `/pickup` session workflows through a slash-command shim — session workflows are reached only through their skills ([test](tests/test_session_skill_invocation.compliance.l1.py))
- ALWAYS: `--prune` deletes archive sessions only after the canonical continuation is written ([audit])
