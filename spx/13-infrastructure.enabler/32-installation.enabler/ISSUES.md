# Issues: Installation

## 1. Claude cache preservation step is declared but not yet implemented

The PDR `spx/13-infrastructure.enabler/32-installation.enabler/21-claude-cache-preservation.pdr.md` declares the Claude Code cache preservation behavior. The corresponding implementation does not yet exist:

- `outcomeeng/distribution/sync.py` `STEPS` does not include a `claude_cache_preserve` entry.
- `outcomeeng/distribution/claude_cache.py` does not exist.
- `installation.md` carries no scenario or property assertions for Claude cache preservation.

Governed by:

- `spx/13-infrastructure.enabler/32-installation.enabler/21-claude-cache-preservation.pdr.md`
- `spx/13-infrastructure.enabler/32-installation.enabler/installation.md`

Required handling:

- Add `claude_cache.py` mirroring `codex_cache.py` with the differences declared in the PDR (no time window, no git history walk, derive the preservation set from the cache directory listing plus the manifest's current published version).
- Add a `claude_cache_preserve` step to `sync.py` `STEPS` between `claude_marketplace_update` and `install_validate`.
- Extend `installation.md` with scenario, property, and compliance assertions covering Claude cache preservation, each linked to co-located tests.
- Update the `Recognized by` section of the PDR's Compliance once the implementation lands, so a future `auditing-product-decisions` run can attribute compliance to a concrete code surface.
