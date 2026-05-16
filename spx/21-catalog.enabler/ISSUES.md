# Issues: Catalog

## 1. Compliance assertions tagged `[review]` for behavior a test can falsify

`catalog.md` carries three compliance assertions tagged `[review]`:

- Deterministic generation: same input produces byte-identical output.
- Sentinel-bounded output: catalog block wraps in `BEGIN_SENTINEL` / `END_SENTINEL`.
- `--check` exit-code contract: non-zero on drift, zero on match.

All three are automatable against fixture inputs (a fake `marketplace.json` plus
a small set of fake plugin directories). The tag is deferred to `[review]` only
because PR-5 (catalog domain extraction) was scoped as a pure refactor with no
new tests.

Resolution: in a follow-up PR, add `tests/test_plugin_catalog.scenario.l1.py`
and `tests/test_plugin_catalog.compliance.l1.py` against fixture
directories. Promote the three assertions from `[review]` to `[test]` and link
them to the new test files. The `docs-check` pipeline step is operational
coverage but does not count as `[test]` evidence on the spec node itself.
