# Sync

PROVIDES marketplace sync orchestration that reconciles only the invocation checkout's committed runtime marketplace configuration
SO THAT marketplace maintainers and CI workflows
CAN bring a checkout's committed Claude Code and Codex configuration into a consistent state without mutating any developer's user-scope marketplace registrations, plugin caches, or agent directories.

Sync operates only on the repository checkout it runs from: it reconciles that checkout's committed runtime marketplace configuration and never mutates a developer's user-scope marketplace registrations, plugin caches, or agent directories. The guarantee that every catalog plugin installs and enables across both runtimes is established by the isolated real-runtime installation harness, which provisions real runtimes in disposable homes rather than refreshing a maintainer's live installation.

## Assertions

### Compliance

- NEVER: sync mutates a path outside the invocation checkout — a developer's user-scope marketplace registrations, plugin caches, and agent directories are unchanged after every run ([audit])
- ALWAYS: sync reconciles only the checkout's committed runtime marketplace configuration — Codex `.agents/plugins/marketplace.json` and `.codex/config.toml`, Claude Code `.claude-plugin/marketplace.json` and project-scope `.claude/settings.json` ([audit])
- ALWAYS: install completeness across both runtimes is established by the isolated real-runtime installation harness, not by refreshing a maintainer's live installation ([audit])
