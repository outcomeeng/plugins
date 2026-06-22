# PLAN — runtime parameterization

Coordination note; not spec truth. Reconcile before use.

## Phase 1 (complete)

Registry-backed `tool(...)` token + runtime-explicit form, implemented in
`outcomeeng/distribution/build.py` with the registry populated from the `AGENTS.md` Agent
Runtime Guidance table. Every plugin's content is converted to tokens, and the runtime-token
validation lint (`outcomeeng/validation/runtime_tokens.py`, governed by
`spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`) enforces every authored
file under `src/plugins/` and `src/_shared/` with `RUNTIME_TOKEN_IGNORE` empty — no exemptions.
The registry is seeded with `ask_user` (`AskUserQuestion`/`request_user_input`) and the
no-Codex-equivalent `ScheduleWakeup`; the ignore-list mechanism remains as the tracked exemption
surface for any future not-yet-converted plugin.

## Phase 2 (declared in the ADR, not yet implemented)

The build-architecture ADR (`spx/18-plugin-build.enabler/15-build-architecture.adr.md`)
declares the full symmetric model. These parts are declared ahead of implementation:

- **Symmetric frontmatter strip.** `spx/18-plugin-build.enabler/43-target-emission.enabler`
  strips Claude-only fields from Codex today. Generalize `strip_frontmatter_fields` to a
  per-target frontmatter schema (strip fields not in the target's schema, either direction)
  once a real Codex-only field exists; until then the one-directional strip is the only
  populated direction.
- **`field(...)` and `term(...)` tokens.** Extend the registry beyond tool names to
  frontmatter field names and concept terms, so `develop`'s subject-matter teaching renders
  per runtime.
- **Concept-term conversion in `develop`.** The subagent model (~224 mentions) and
  fact-level claims need term tokens and per-runtime conditional blocks; needs consolidated
  Codex agent-model facts.
