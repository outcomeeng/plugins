# PLAN — runtime parameterization

Coordination note; not spec truth. Reconcile before use.

## Phase 1 (complete)

Registry-backed `tool(...)` token + runtime-explicit form, implemented in
`outcomeeng/distribution/build.py` with the registry populated from the `AGENTS.md` Agent
Harness Guidance table. Every plugin's content is converted to tokens, and the runtime-token
validation lint (`outcomeeng/validation/runtime_tokens.py`, governed by
`spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`) enforces every authored
file under `src/plugins/` and `src/_shared/`, except the explicit files named in
`RUNTIME_TOKEN_IGNORE` because they must name harness guide filenames as data.
The registry is seeded with `ask_user` (`AskUserQuestion`/`request_user_input`) and the
no-Codex-equivalent `ScheduleWakeup`; the ignore-list mechanism remains as the tracked exemption
surface for any future not-yet-converted plugin.

## Phase 2

The build-architecture ADR (`spx/18-plugin-build.enabler/15-build-architecture.adr.md`)
declares the full symmetric model.

### `field()`, `term()`, and `file()` token mechanism (complete)

`RUNTIME_TOKEN_REGISTRY` in `outcomeeng/distribution/build.py` is keyed by token kind. A
`RuntimeTokenKind(lint_enforced, names)` carries each kind's per-runtime names and whether
the source-layer guard enforces them. The `tool`, `field`, `term`, and `file` kinds are each
exposed as their own build template global (`tool(…)`, `field(…)`, `term(…)`, `file(…)`)
rendering through one `resolve_runtime_token` path. The configured-agent concept terms and
the configured-agent prompt field are populated in the source-owned registry and consumed by
the `develop` plugin sources. The runtime-token lint
(`outcomeeng/validation/runtime_tokens.py`, `forbidden_names`) derives its forbidden set from
the lint-enforced kinds (`tool`, `field`, `file`) only — the review-only `term` kind is
excluded because its common-word concept terms would false-positive across prose.

### Remaining (declared ahead of implementation)

- **Symmetric frontmatter strip.** `spx/18-plugin-build.enabler/43-target-emission.enabler`
  strips Claude-only fields from Codex today. Generalize `strip_frontmatter_fields` to a
  per-target frontmatter schema (strip fields not in the target's schema, either direction)
  once a real Codex-only field exists; until then the one-directional strip is the only
  populated direction.
