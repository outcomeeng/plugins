# Catalog

PROVIDES the plugin catalog generator that emits a sentinel-bounded markdown table summarizing every plugin's skills, agents, and commands
SO THAT the README and any other repository documentation that surfaces the catalog
CAN reflect the plugin set deterministically without manual edits to the catalog section

The catalog is a Markdown block bounded by `BEGIN_SENTINEL` and `END_SENTINEL` comments and derived from the marketplace catalog plus each plugin's skills, agents, and commands. Its command writes the block to stdout by default, rewrites the sentinel-bounded `README.md` region with `--write`, and reports drift with a non-zero exit through `--check`.

## Assertions

### Compliance

- ALWAYS: generate the catalog deterministically from `.claude-plugin/marketplace.json` and the live plugin directories — the same input produces byte-identical output ([test](tests/test_plugin_catalog.compliance.l1.py))
- ALWAYS: bound the catalog block with the sentinel comments declared as `BEGIN_SENTINEL` and `END_SENTINEL` in `outcomeeng.catalog.plugin_catalog` ([test](tests/test_plugin_catalog.compliance.l1.py))
- ALWAYS: `--check` mode exits non-zero when the on-disk `README.md` differs from the generated content — the validation pipeline's `docs-check` step depends on this exit-code contract ([test](tests/test_plugin_catalog.compliance.l1.py))
- ALWAYS: catalog-visible frontmatter renders against every emitted runtime target, and a purpose that differs by target names each target rather than silently selecting one runtime's wording ([test](tests/test_plugin_catalog.compliance.l1.py))
- NEVER: purpose shortening rewrites punctuation inside an untrimmed catalog purpose; em dashes stay em dashes unless they are the selected sentence boundary ([test](tests/test_plugin_catalog.compliance.l1.py))
