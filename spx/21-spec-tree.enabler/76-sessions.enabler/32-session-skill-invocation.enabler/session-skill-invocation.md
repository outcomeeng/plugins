# Session Skill Invocation

PROVIDES the declared invocation surface of the `/handoff` and `/pickup` session skills — their argument-hint flags, argument bindings, and bounded queue reads
SO THAT an agent closing or resuming spec-tree work
CAN select the supported flags and reach session queue state only at the workflow step that consumes it

## Assertions

### Compliance

- ALWAYS: the `/handoff` skill declares `argument-hint: "[--no-session] [--prune]"` in its frontmatter ([audit])
- ALWAYS: the `/handoff` skill parses the whole `$ARGUMENTS` string once, treats empty input as both flags absent, accepts only `--no-session` and `--prune` in either order, rejects unknown or duplicate flags before mutation, and emits one normalized `<HANDOFF_OPTIONS>` marker for option-dependent workflows ([audit])
- ALWAYS: the `/pickup` skill declares `argument-hint: "[--list] [--auto-continue]"` in its frontmatter ([audit])
- NEVER: the `/handoff` skill injects `spx session list` output into its context block; session queue reads occur only in the workflow step that consumes them and use status filters when queue inspection is needed ([audit])
- ALWAYS: the `/pickup` skill injects `spx session todo` into its context block, surfacing available sessions at invocation ([audit])
- ALWAYS: the `/pickup` workflow invokes `/understand` before processing session details, and leaves node-local `PLAN.md` / `ISSUES.md` content reads to `/contextualize` before those coordination notes steer work ([audit])
- NEVER: expose the `/handoff` or `/pickup` session workflows through a slash-command shim — session workflows are reached only through their skills ([test](tests/test_session_skill_invocation.compliance.l1.py))
- ALWAYS: when `--prune` applies to a closure that creates a fresh continuation, its approval covers the exact union of existing archive IDs and IDs the closure will archive, and deletion occurs only after the canonical continuation is written and those selected sessions are archived ([audit])
