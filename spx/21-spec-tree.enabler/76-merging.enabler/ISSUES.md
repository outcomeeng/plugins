# Issues — Merging

Known follow-ups for the merging node. Coordination note; not spec truth.

## Transport-selection status message exposes classifier internals

`/merge` can report the selected transport with raw classifier counts and a mechanical delegation sentence:

```text
Transport selected: GitHub PR, because the classification has 2 changed files and 2 non-coordination-note files. I'm delegating to /manage-github-pr, which owns branch creation, commit, PR opening, checks, review, and merge.
```

The status is technically traceable to the transport-selection policy in `spx/21-spec-tree.enabler/76-merging.enabler/merging.md`, but it is the wrong operator surface. It leaks count-level classifier implementation detail, over-narrates delegation, and reads as a handoff rather than a lifecycle step the merge skill continues to own. A future merging-skill change should adjust the `/merge` transport-selection wording and eval expectations so the message names the selected transport and the policy reason at the user-facing level: coordination-note-only changes use direct-push, overlay-declared transport wins, otherwise GitHub PR. The message should avoid raw changed-file counts unless the count is itself the decision boundary the operator needs to inspect.

## Codex rendering for Claude-authored argument syntax

Source skills under `src/plugins/` are authored in Claude Code's supported SKILL.md syntax. `src/plugins/develop/skills/skill-standards/references/command-capabilities.md` now permits `$ARGUMENTS` for whole-string instruction capture and keeps `arguments` / `$name` for stable positional tokens. This resolves the former skill-auditor contradiction that treated bare `$ARGUMENTS` as command-only syntax.

The remaining concern belongs to generated Codex output: when authored source uses a Claude-supported form that Codex does not consume directly, the build renderer must adapt `dist/codex/` without weakening the authored source. The source policy is:

- Use `$ARGUMENTS` for free-form, multi-word instructions and forwarding between lifecycle skills (`merge`, `manage-github-pr`, `pickup`).
- Use `arguments` / `$name` when a stable token boundary improves reliability for Claude or wrapper-agent invocation (`audit-subagents`, `audit`, `handoff`).
- Prefer the Claude/Codex intersection only when it improves reliability for agent-invoked skills or convenience for user-invoked skills; otherwise, keep authored source clear and make Codex rendering responsible for runtime adaptation.

Required handling: audit the build renderer and generated `dist/codex/` argument surfaces so Claude-only authored forms render into Codex-consumable syntax where needed. Surfaced by the argument-syntax review during `feat/guide-filename-runtime-token` (2026-06-26).
