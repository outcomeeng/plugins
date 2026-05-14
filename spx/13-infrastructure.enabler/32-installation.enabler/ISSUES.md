# Issues: Installation

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
