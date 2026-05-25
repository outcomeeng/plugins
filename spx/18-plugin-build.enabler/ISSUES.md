# Issues

Tracked imperfections in the 18-plugin-build subtree. Remove items as they
are resolved.

## 1. Final sync verification must prove generated Codex agents install

The sync path now includes `codex_agent_install`, but the repository outcome
requires proving that the local marketplace sync writes generated agent TOML
files under `~/.codex/agents` and records them in
`.outcomeeng-generated-agents.json`.

Resolution: after local checks pass, run `just sync-marketplace <previous-main-ref>`
and inspect `~/.codex/agents` for generated agent TOML plus the manifest file.
