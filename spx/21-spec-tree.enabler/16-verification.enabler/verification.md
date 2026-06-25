# Verification

PROVIDES the run-journal architecture shared by the agentic verification types — review and audit — under which their skills and thin wrapper agents record changeset-scoped runs
SO THAT authors of agentic verification skills and the wrapper agents that drive them
CAN compose against one append-only run-journal contract, one projection discipline, and one wrapper-agent shape

## Verification types

The five verification types and the two axes that classify them — verdict mode and purpose — are declared in the `/understand` foundation reference `src/plugins/spec-tree/skills/understand/references/verification-kinds.md` and grounded for this product in `spx/14-verification.pdr.md`. This enabler is the home of the agentic types' shared architecture, decided in `spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`; review and audit implement it.

## Assertions

### Compliance

Each rule enforces a guarantee of `spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`.

- ALWAYS: every agentic verification run records its durable facts as appended events on one journal that is the run's sole source of truth ([audit])
- ALWAYS: every output surface an agentic verification run produces — markdown report, pull-request comment, findings JSON, check summary — is a projection rendered from the journal's event history ([audit])
- ALWAYS: every agentic verification skill addresses the journal through one backend-neutral channel and hard-codes no storage path, backend, or surface ([audit])
- ALWAYS: appended events carry strictly increasing, contiguous sequence numbers, and reads resume from a cursor ([audit])
- ALWAYS: a correction to a prior finding is a later event referencing the original, never a mutation of a persisted event ([audit])
- ALWAYS: a terminal seal makes a run's sequence final — no append succeeds on a sealed journal ([audit])
- ALWAYS: a thin wrapper agent under `src/plugins/spec-tree/agents/` drives each agentic verification skill, holds no verification or I/O policy, and declares a model identifier, `tools: Bash, Read, Skill`, and `skills:` listing the skill ([audit])
- ALWAYS: every wrapper agent declares `model: sonnet` or `model: inherit` — omitting the field falls back to the session model (Opus 4.8), which is unacceptable for verification agents ([test](tests/test_agent_model_field.mapping.l1.py))
- ALWAYS: every agentic verification skill derives its changeset scope through the shared changeset-scope primitives (`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/changeset-scope.md`) ([audit])
- NEVER: an agentic verification skill reads authoritative run state from a rendered surface rather than from the journal ([audit])
- NEVER: an agentic verification skill hand-validates the records it emitted — the channel's exit code is the validity signal ([audit])
- NEVER: a wrapper agent hard-codes a storage path, backend, or surface in its prose — backend selection is bound at the edge and swappable without changing the agent ([audit])
- NEVER: a wrapper agent omits the model identifier — the missing-field fallback is Opus 4.8, which is unacceptable for verification agents ([test](tests/test_agent_model_field.mapping.l1.py))
- NEVER: an agentic verification skill duplicates or reinvents the changeset-scope derivation ([audit])
