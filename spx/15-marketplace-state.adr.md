# Marketplace State Ownership

The marketplace synchronization toolchain operates only on the repository checkout it runs from: it reconciles that checkout's committed runtime configuration and never mutates a developer's user-scope marketplace registrations, plugin caches, or agent directories. Each coding-agent runtime owns its marketplace state as committed repository configuration — Codex in `.agents/plugins/marketplace.json`, `.codex/config.toml`, and `.codex/agents/`; Claude Code in project-scope `.claude/settings.json`. The guarantee that every catalog plugin installs and enables across both runtimes is established by an isolated installation harness that provisions real runtimes in disposable homes, not by mutating a maintainer's live installation.

## Rationale

A developer's user-global runtime state belongs to that developer; a repository-scoped tool that reaches into it strands running sessions, couples the tool to one machine's ambient configuration, and makes install verification depend on whatever that machine already holds. Bounding synchronization to the invocation checkout and establishing the every-plugin-installs guarantee in a disposable harness makes the tool safe to run from any worktree and the guarantee reproducible anywhere. The rejected alternative maintains the maintainer's user-scope caches and registrations in place, which entangles repository tooling with per-machine global state and forces cache-preservation machinery to protect the sessions that entanglement puts at risk.

## Invariants

- Each runtime's marketplace registration and plugin selection is fully determined by the checkout's committed configuration.

## Verification

### Testing

- NEVER: marketplace synchronization mutates a path outside the invocation checkout — a developer's user-scope marketplace registrations, plugin caches, and agent directories are unchanged after every run ([compliance])
- ALWAYS: each coding-agent runtime's marketplace registration and plugin selection is declared in committed repository configuration of the checkout — Codex in `.agents/plugins/marketplace.json` and `.codex/config.toml`, Claude Code in project-scope `.claude/settings.json` ([conformance])
- ALWAYS: converted Codex custom-agent files are written under the checkout's `.codex/agents/` directory ([conformance])
- ALWAYS: marketplace-install diagnosis derives expected plugin state from the checkout's per-runtime project declarations rather than from a plugin catalog embedded in shipped diagnostic output ([compliance])
- ALWAYS: install completeness — every catalog plugin installed and enabled in both runtimes — is verified by an isolated harness that provisions real `claude` and `codex` binaries in disposable runtime homes and mutates no user-scope state ([compliance])
