# Agentic Verification Run Journal

Every agentic verification run — review or audit per `src/plugins/spec-tree/skills/understand/references/verification-kinds.md` — is one append-only event journal, and that journal is the run's sole source of truth. The skill appends domain events as the run advances — scope entered, finding reported, run completed — and resumes reads from a cursor; it never reads authoritative run state from a rendered surface. Every output surface — the markdown report, the pull-request comment, the findings JSON, the check summary — is a projection rendered from the journal's event history, never authoritative state. The skill addresses the journal through one backend-neutral channel and hard-codes no storage path, backend, or surface; the channel binds the backend at the edge — a local run-journal file on a developer machine, a hosted pull-request comment under CI — and is swappable without changing the skill. The contract is invariant across backends: appended events carry strictly increasing, contiguous sequence numbers; a correction is a later event referencing the original, never a mutation of a persisted event; a read resumes from any cursor; a terminal seal makes the sequence final, after which no append succeeds; and a projection is a pure function of an event prefix, identical on every backend. The run is driven by a thin wrapper agent under `src/plugins/spec-tree/agents/` that holds no verification or I/O policy and declares a model identifier (`model: sonnet` or `model: inherit`), `tools: Bash, Read, Skill`, and `skills:` listing the skill.

## Rationale

A contract phrased in facts and derivations — append, read, cursor, seal, render — survives backend substitution because no backend's storage shape appears in it, so the same run is observable in the same shape whether it streams to a local file or a pull-request comment. Separating the canonical event history from its projections keeps a mutable, size-bounded display surface — a pull-request comment is edited in place and capped in length — from contaminating the run's source of truth: the journal accumulates facts, and a projection re-renders from them on demand and serves as the run's final output. A skill that names its own backend couples to one environment and cannot run unchanged across local and hosted surfaces, so backend selection stays an edge concern reached through one channel. The channel's append and seal return an exit code, which keeps record validity a deterministic signal rather than a second model judgment over the events the model just produced — a model cannot reliably hand-validate its own output. The wrapper agent holds no policy because the skill is the single behavior surface shared across Claude Code-authored source and generated Codex output, and the model identifier is declared explicitly because the missing-field fallback is the session model (Opus 4.8), unacceptable for verification agents.

## Verification

### Audit

- ALWAYS: an agentic verification run records its durable facts — scope entered, finding reported, run completed — as appended events on one journal that is the run's sole source of truth ([audit])
- ALWAYS: every output surface an agentic verification run produces — markdown report, pull-request comment, findings JSON, check summary — is a projection rendered from the journal's event history ([audit])
- ALWAYS: the skill addresses the journal through one backend-neutral channel and hard-codes no storage path, backend, or surface — backend selection is bound at the edge and swappable without changing the skill ([audit])
- ALWAYS: appended events carry strictly increasing, contiguous sequence numbers, and a read resumes from any cursor ([audit])
- ALWAYS: a correction to a prior finding is expressed as a later event referencing the original, never as a mutation of a persisted event ([audit])
- ALWAYS: a terminal seal makes a run's sequence final — no append succeeds on a sealed journal ([audit])
- ALWAYS: a thin wrapper agent under `src/plugins/spec-tree/agents/` drives each agentic verification skill, holds no verification or I/O policy, and declares a model identifier, `tools: Bash, Read, Skill`, and `skills:` listing the skill ([audit])
- ALWAYS: an agentic verification run derives its changeset scope — branch, slug, base ref, changed-file set — through the shared changeset-scope primitives (`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/changeset-scope.md`) ([audit])
- NEVER: the skill reads authoritative run state from a rendered surface — a pull-request comment body or a rendered report — rather than from the journal ([audit])
- NEVER: the skill hand-validates the records it emitted — the channel's exit code is the validity signal ([audit])
- NEVER: the skill or wrapper agent hard-codes a storage path, backend, or surface in its prose ([audit])
- NEVER: an agentic verification skill duplicates or reinvents the changeset-scope derivation ([audit])

### Testing

- ALWAYS: every wrapper agent declares `model: sonnet` or `model: inherit` — omitting the field falls back to the session model (Opus 4.8), which is unacceptable for verification agents ([test](tests/test_agent_model_field.mapping.l1.py))
- NEVER: a wrapper agent omits the model identifier — the missing-field fallback is Opus 4.8, which is unacceptable for verification agents ([test](tests/test_agent_model_field.mapping.l1.py))
