# Plugin Packaging and Runtime Safety

## Purpose

This decision governs the packaging conventions and runtime-safety boundaries that every marketplace plugin and skill conforms to. It covers manifest packaging, skill authoring conformance, helper-language uniformity, path-variable resolution, and limits on subprocess lifetime and polling behavior.

## Context

**Business impact:** The marketplace ships a combined Codex + Claude Code product from a single source tree. Heterogeneous packaging or runtime patterns across plugins surface as silent failures — Codex cache drift after single-file version bumps, helpers whose paths fail outside the skill directory, shell scripts that work in bash and break in zsh, and `gh`/process invocations that fork-bomb the host workstation across turns.

**Technical constraints:** Skill loaders expand `${CLAUDE_SKILL_DIR}` to the skill's installation path before tool execution; bash `$0` and `${0%/*}` do not resolve to that directory when the agent runs commands through the Bash tool. The Bash tool does not reliably reap subprocess trees spawned by long-lived watchers or by per-iteration polling loops, so fork-bomb-class accumulation occurs across turns even when each individual command appears short. The marketplace standardizes on Python via `uv` for helper code; shell scripts ship only as runtime hooks (such as `SessionStart`) not as plugin helpers.

## Decision

Every plugin ships dual manifests with version fields in lockstep, every skill conforms to `/standardizing-skills`, every helper under a skill's `scripts/` directory is Python, every path inside skill content resolves via `${CLAUDE_SKILL_DIR}`, and no plugin code spawns long-lived subprocesses or implements polling waits.

## Rationale

The dual-manifest invariant exists because the Codex marketplace cache resolves plugin versions independently of the Claude Code cache, and single-file version bumps cause Codex cache drift. Lockstep is the simplest mechanical guarantee.

The `/standardizing-skills` conformance invariant exists because skill activation depends on directive descriptions, frontmatter discipline, and pure-XML body structure; a single non-conformant skill in the marketplace lowers the activation rate of the entire surface and makes auditing inconsistent.

The Python-only invariant for helpers exists because the marketplace manages Python via `pyproject.toml` and `uv`, helpers cross between Codex and Claude Code surfaces unchanged, and shell-script portability (`export -f`, `status` builtin in zsh, locale-dependent `sed`) consumes more author time than the helpers save. Shell scripts remain valid for runtime hooks — `SessionStart` and similar — because hooks are runtime contracts, not plugin code.

The `${CLAUDE_SKILL_DIR}` invariant exists because helper-script path resolution via `$(dirname "$0")` or `${0%/*}` returns the calling shell's location, not the skill directory, when the agent runs the command through the Bash tool. The skill loader expands the variable before tool execution; that is the only path expression that resolves correctly across runtimes.

The runtime-safety invariants — no `gh run watch`, no polling waits, no long-lived subprocesses — exist because the Bash tool does not reliably reap subprocess trees across turns, and fork-bomb-class accumulation results when these patterns are repeated across an agent session. The marketplace's `<no_gh_run_watch>` and `<no_until_polling>` rules in `CLAUDE.md` are the agent-runtime expression of this ADR; codifying them here anchors the rules in a decision record so node specs do not have to restate them.

The alternative — leaving these conventions implicit in `CLAUDE.md` and `/standardizing-skills` references — was rejected because implicit conventions force node specs to restate the rules locally to make them testable, producing cross-cutting placement debt that grows with every new node.

## Trade-offs accepted

| Trade-off                                                                                              | Mitigation / reasoning                                                                                                                  |
| ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| Dual manifests double the edit surface for version bumps                                               | Lockstep is mechanically enforceable by `just check`; the marketplace memory captures the drift failure mode to prevent regression      |
| Python-only helpers exclude familiar shell idioms                                                      | The marketplace manages Python via `uv`; runtime hooks (e.g., `SessionStart`) remain valid shell because they are not helpers           |
| Forbidding `gh run watch` removes a convenient monitoring command                                      | One-shot `gh run view --json status,conclusion` plus `ScheduleWakeup` covers the same need without the unreaped-subprocess risk         |
| Forbidding polling waits removes a familiar pattern for waiting on processes, ports, or HTTP endpoints | Background commands with completion notifications, `Monitor`, or `ScheduleWakeup` cover the same need with bounded subprocess lifetimes |
| `${CLAUDE_SKILL_DIR}` resolution depends on the skill loader expanding the variable before execution   | Both Codex and Claude Code expand it; helper authors do not need to know the absolute path                                              |

## Compliance

### Recognized by

A conformant plugin has both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` with matching `version` fields. Its skills carry directive descriptions, pure-XML bodies with `<objective>` and `<success_criteria>` tags, and lowercase-hyphenated names matching their directories. Its helpers are Python files under `scripts/`. Its skill content references paths via `${CLAUDE_SKILL_DIR}`. Its helpers do not invoke `gh run watch`, do not include polling-wait constructs, and do not spawn watchers or persistent subprocess trees.

### MUST

- Each plugin ships `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` with `version` fields in lockstep — single-file bumps cause Codex cache drift, captured in the marketplace memory `feedback_manifest_bump_completeness` ([review])
- Every skill conforms to `/standardizing-skills` — directive description without `when:` colon mid-sentence, lowercase-hyphenated name matching the directory, pure-XML body containing `<objective>` and `<success_criteria>`, restricted `allowed-tools` ([review])
- Helpers under a skill's `scripts/` directory are Python (`*.py`) — the marketplace standardizes on Python via `uv`; shell scripts ship only as runtime hooks (`SessionStart` and similar contract surfaces), never as plugin helpers ([review])
- Paths in skill content (SKILL.md, references, helper invocations) resolve via `${CLAUDE_SKILL_DIR}` — bash `$0`-derived expressions do not resolve to the skill directory when the Bash tool runs the command ([review])

### NEVER

- Invoke or document `gh run watch` as an actionable instruction or include it in a code fence — unreaped subprocess trees exhaust the host across turns; explicit prohibition language naming the command as forbidden remains permitted ([review])
- Write polling waits in helpers — `while ... : time.sleep(N)` in Python, `until <check>; do sleep N; done` or `while ! <check>; do sleep N; done` in shell — per-iteration process trees accumulate until host resources are exhausted ([review])
- Spawn subprocesses whose lifetime exceeds a single tool call's expected duration — persistent watchers, daemons, and streaming-log commands are forbidden inside helpers and skill instructions ([review])
