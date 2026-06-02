# Verification

PROVIDES the architecture shared by the agentic verification types — reviewing and auditing — under which their skills and thin wrapper agents produce changeset-scoped results
SO THAT authors of agentic verification skills and the wrapper agents that drive them
CAN compose against one persistence model, one validation discipline, and one wrapper-agent shape

## Verification types

The five verification types and the two axes that classify them — verdict mode and purpose — are declared in the `/understanding` foundation reference `src/plugins/spec-tree/skills/understanding/references/verification-kinds.md` and grounded for this product in `spx/14-verification.pdr.md`. This enabler is the home of the agentic types' shared architecture, decided in `spx/21-spec-tree.enabler/16-verification.enabler/13-architecture.adr.md`; reviewing and auditing implement it.

## Assertions

### Compliance

Each rule enforces a guarantee of `spx/21-spec-tree.enabler/16-verification.enabler/13-architecture.adr.md`.

- ALWAYS: every agentic verification skill persists its result and markdown surface through thread-store ([audit])
- ALWAYS: every agentic verification skill emits one machine-readable result conforming to its own JSON schema alongside one markdown surface ([audit])
- ALWAYS: every agentic verification skill encodes its policy in a `scripts/` Python module exposed through a CLI arbiter its wrapper agent invokes before persistence ([audit])
- ALWAYS: a thin wrapper agent under `src/plugins/spec-tree/agents/` drives each agentic verification skill, holds no verification or I/O policy, and declares a model identifier, `tools: Bash, Read, Skill`, and `skills:` listing the skill ([audit])
- ALWAYS: a wrapper agent's model is an identifier the distribution pipeline resolves per runtime — the authored default is Sonnet on Claude Code, substituted per target by the build ([audit])
- ALWAYS: every agentic verification skill addresses changeset-scoped records through the slug helper re-exported by thread-store ([audit])
- NEVER: an agentic verification skill reads or writes a backend-specific path directly from skill or agent prose ([audit])
- NEVER: an agentic verification skill hand-validates the JSON it emitted — the arbiter's exit code is the validity signal ([audit])
- NEVER: a wrapper agent pins a single runtime's model name the distribution pipeline cannot substitute ([audit])
- NEVER: an agentic verification skill duplicates or reinvents the changeset-slug derivation rule ([audit])
