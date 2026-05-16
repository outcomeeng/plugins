# Issues: Installation

## 2. Claude cache preservation step is declared but not yet implemented

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

## 1. Codex cache preservation warns for plugins with Codex manifests

During `just push-marketplace origin main` on 2026-05-14, the Codex cache preservation step printed:

```text
warning: no current cache version found for frontend
warning: no current cache version found for hdl
```

Both plugins have `plugins/<plugin>/.codex-plugin/plugin.json` manifests in the working tree, and the overall install validation still ended with `all checks passed` and `installed skills valid`.

Governed by:

- `spx/13-infrastructure.enabler/32-installation.enabler/installation.md`
- `spx/13-infrastructure.enabler/32-installation.enabler/21-codex-cache-preservation.adr.md`

Required handling:

- Determine whether `preserve_codex_plugin_cache` is warning about intentionally uninstalled Codex plugins, a stale marketplace clone, or missing cache state.
- If the warning is expected, classify it as informational and make the diagnostic explicit.
- If the warning indicates missing preservation coverage, add a scenario test and fix the preservation logic.
