# Skill Surface

PROVIDES the declared invocation surface of the `/handoff` and `/pickup` session skills — their argument-hint flags and the live `spx session` queue state each skill injects into its context block
SO THAT an agent closing or resuming spec-tree work
CAN select the supported flags and read the current session queue at the moment of invocation, reaching the session workflows only through their skills

## Assertions

### Compliance

- ALWAYS: the `/handoff` skill declares `argument-hint: "[--no-session] [--prune]"` in its frontmatter ([test](tests/test_skill_surface.compliance.l1.py))
- ALWAYS: the `/pickup` skill declares `argument-hint: "[--list] [--auto-continue]"` in its frontmatter ([test](tests/test_skill_surface.compliance.l1.py))
- ALWAYS: the `/handoff` skill injects `spx session list` into its context block, surfacing the session queue at invocation ([test](tests/test_skill_surface.compliance.l1.py))
- ALWAYS: the `/pickup` skill injects `spx session todo` into its context block, surfacing available sessions at invocation ([test](tests/test_skill_surface.compliance.l1.py))
- NEVER: expose the `/handoff` or `/pickup` session workflows through a slash-command shim — session workflows are reached only through their skills ([test](tests/test_skill_surface.compliance.l1.py))
- ALWAYS: `--prune` deletes archive sessions only after the canonical continuation is written ([review])
