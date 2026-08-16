# Catalog

PROVIDES the plugin catalog generator that emits a sentinel-bounded markdown table summarizing every plugin's skills and thin agents
SO THAT the README and any other repository documentation that surfaces the catalog
CAN reflect the plugin set deterministically without manual edits to the catalog section

The `outcomeeng.catalog.plugin_catalog` module reads the marketplace catalog at `.claude-plugin/marketplace.json`, each plugin's authored `SKILL.md` and agent definitions, and the lifecycle skill emitted from `src/templates/plugin/SKILL.md`, then emits a Markdown block bounded by the source-owned `BEGIN_SENTINEL` and `END_SENTINEL` comments. The module supports three modes: stdout (default), `--write` (rewrite `README.md` in place between the sentinels), and `--check` (compare `README.md` against the generated content and exit non-zero on drift).

## Assertions

### Compliance

- ALWAYS: generate the catalog deterministically from `.claude-plugin/marketplace.json`, the live plugin directories, and `src/templates/plugin/SKILL.md`; every marketplace plugin includes its emitted lifecycle skill, and the same input produces byte-identical output ([test](tests/test_plugin_catalog.compliance.l1.py))
- ALWAYS: bound the catalog block with exact sentinel-comment lines declared as `BEGIN_SENTINEL` and `END_SENTINEL` in `outcomeeng.catalog.plugin_catalog`; a quoted marker, an inline marker, or a line-start marker with trailing text bounds nothing ([test](tests/test_plugin_catalog.compliance.l1.py))
- ALWAYS: `--check` mode exits non-zero when the on-disk `README.md` differs from the generated content — the validation pipeline's `docs-check` step depends on this exit-code contract ([test](tests/test_plugin_catalog.compliance.l1.py))
- ALWAYS: catalog-visible frontmatter renders against every emitted runtime target, and a purpose that differs by target names each target rather than silently selecting one runtime's wording ([test](tests/test_plugin_catalog.compliance.l1.py))
- NEVER: purpose shortening rewrites punctuation inside an untrimmed catalog purpose; em dashes stay em dashes unless they are the selected sentence boundary ([test](tests/test_plugin_catalog.compliance.l1.py))
