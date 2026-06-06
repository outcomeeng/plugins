# Plugin Packaging and Execution Safety

Every plugin ships dual manifests (`.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`) with version fields in lockstep, every skill conforms to `/standardizing-skills`, every helper under a skill's `scripts/` directory is Python, every path inside skill content resolves via `${CLAUDE_SKILL_DIR}`, every scratch directory comes from a unique-per-invocation source (`tempfile.mkdtemp`, `mktemp -d`, or a test fixture) with caller-owned cleanup, and no plugin code spawns long-lived subprocesses or implements polling waits. Skills prefer stdin/stdout pipes between scripts over intermediate files when fanout does not demand a directory.

## Rationale

The dual-manifest lockstep exists because the Codex marketplace cache resolves plugin versions independently of the Claude Code cache, so a single-file version bump causes Codex cache drift; lockstep is the simplest mechanical guarantee. The `/standardizing-skills` conformance invariant holds because skill activation depends on directive descriptions, frontmatter discipline, and pure-XML structure — one non-conformant skill lowers the activation rate of the whole surface. Helpers are Python because the marketplace manages Python via `uv`, helpers cross the Codex and Claude Code surfaces unchanged, and shell portability consumes more author time than it saves; hook scripts remain shell because they are coding-agent contracts, not plugin code.

`${CLAUDE_SKILL_DIR}` is the only path expression that resolves to the skill directory when the agent runs a command through the Bash tool — `$0`-derived expressions resolve to the calling shell. The execution-safety invariants exist because the Bash tool does not reliably reap subprocess trees across turns, so `gh run watch`, polling waits, and long-lived subprocesses accumulate into host exhaustion. The scratch-storage invariants exist because hardcoded `/tmp/<fixed-name>/` paths collide under concurrent runs and `atexit` cleanup behaves inconsistently across coding agents, so the orchestrator that creates a scratch directory owns its removal. Leaving these conventions implicit in `CLAUDE.md` and `/standardizing-skills` would force every node spec to restate them to make them testable, producing cross-cutting placement debt.

## Verification

### Audit

- ALWAYS: each plugin ships `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` with `version` fields in lockstep — a single-file bump causes Codex cache drift ([audit])
- ALWAYS: every skill conforms to `/standardizing-skills` — directive description, lowercase-hyphenated name matching its directory, pure-XML body with `<objective>` and `<success_criteria>`, restricted `allowed-tools` ([audit])
- ALWAYS: helpers under a skill's `scripts/` directory are Python — shell scripts ship only as hook contracts (`SessionStart` and similar), never as plugin helpers ([audit])
- ALWAYS: paths in skill content resolve via `${CLAUDE_SKILL_DIR}` — `$0`-derived expressions do not resolve to the skill directory under the Bash tool ([audit])
- ALWAYS: scratch directories come from a unique-per-invocation source, and the orchestrator that creates one removes it on every exit path including failure — helper modules register no `atexit` handlers ([audit])
- ALWAYS: skills prefer stdin/stdout pipes between scripts over intermediate files; an intermediate file is valid only when fanout demands a directory ([audit])
- NEVER: invoke or document `gh run watch` as an actionable instruction — unreaped subprocess trees exhaust the host across turns ([audit])
- NEVER: write polling waits in helpers (`while … time.sleep(N)`, `until <check>; do sleep N; done`) — per-iteration process trees accumulate until host resources are exhausted ([audit])
- NEVER: spawn subprocesses whose lifetime exceeds a single tool call — persistent watchers, daemons, and streaming-log commands are forbidden in helpers and skill instructions ([audit])
