# PLAN — runtime parameterization

Coordination note; not spec truth. Reconcile before use.

## Phase 1 (current)

Registry-backed `tool(...)` token + runtime-explicit form + the source-layer guard for
runtime-divergent unique tokens, implemented in `outcomeeng/distribution/build.py` with the
registry populated from the `AGENTS.md` Agent Runtime Guidance table. Piloted on the
`develop` plugin (see `spx/43-develop.enabler/PLAN.md`). Registry seeded with the
capabilities `develop` needs: `ask_user` (`AskUserQuestion`/`request_user_input`) and the
no-Codex-equivalent unique token `ScheduleWakeup` (guard-only, no render).

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
- **Marketplace-wide rollout.** Apply the token + guard to the other plugins whose
  `dist/codex/` output still carries raw Claude tool names (spec-tree and others); extend the
  guard's enforcement scope beyond `src/plugins/develop/` once they are converted.
