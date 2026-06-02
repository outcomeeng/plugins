# Verification Architecture

Every agentic verification skill — reviewing and auditing per `src/plugins/spec-tree/skills/understanding/references/verification-kinds.md` — and the thin wrapper agent that drives it conform to one architecture: thread-store persistence, a machine-readable result paired with a markdown surface, a `scripts/` Python policy module exposed through a CLI arbiter the agent invokes before persistence, and a wrapper agent that holds no policy and declares a model identifier, `tools: Bash, Read, Skill`, and `skills:` listing the skill. The wrapper agent's model is an identifier the distribution pipeline resolves per runtime — the authored default is Sonnet on Claude Code, substituted per target by the build, because Codex offers no Sonnet model.

## Rationale

Thread-store makes the storage surface a configuration concern, so a kind that persists locally and one that persists to a PR thread share one interface. A deterministic CLI arbiter keeps result validity an exit code rather than a second model judgment over the JSON the model just produced. A model identifier the build resolves lets one authored agent render correctly for runtimes with non-overlapping model catalogs; a pinned `model: sonnet` breaks the generated Codex agent. Models cannot reliably hand-validate the JSON they emit, and skills run against `python3` only in consumer projects per the Plugin Portability Constraints in `AGENTS.md`.

## Verification

### Audit

- ALWAYS: an agentic verification skill persists its result and surface through thread-store (`spx/21-spec-tree.enabler/16-verification.enabler/21-thread-store.enabler/thread-store.md`) ([audit])
- ALWAYS: an agentic verification skill emits one machine-readable result conforming to its own JSON schema alongside one markdown surface ([audit])
- ALWAYS: an agentic verification skill encodes its policy in a `scripts/` Python module exposed through a CLI arbiter the wrapper agent invokes before persistence ([audit])
- ALWAYS: a thin wrapper agent under `src/plugins/spec-tree/agents/` drives each agentic verification skill, holds no verification or I/O policy, and declares a model identifier, `tools: Bash, Read, Skill`, and `skills:` listing the skill ([audit])
- ALWAYS: a wrapper agent's model is an identifier the distribution pipeline resolves per runtime — the authored default is Sonnet on Claude Code, substituted per target by the build ([audit])
- ALWAYS: changeset-scoped records are addressed through the slug helper re-exported by thread-store ([audit])
- NEVER: read or write a backend-specific path directly from skill or agent prose ([audit])
- NEVER: hand-validate emitted JSON in agent prose — the arbiter's exit code is the validity signal ([audit])
- NEVER: pin a single runtime's model name (such as a literal `sonnet`) the build cannot substitute — Codex has no Sonnet model ([audit])
- NEVER: duplicate or reinvent the changeset-slug derivation rule ([audit])
