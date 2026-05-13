# Issues: Verdict Toolchain Enabler

## 1. `tests/_helpers.py` violates the test-infrastructure PDR

`spx/21-spec-tree.enabler/32-evidence.enabler/65-verdict-toolchain.enabler/tests/_helpers.py` holds shared test scaffolding (paths, JSON block delimiters, runner imports). Per `spx/15-test-infrastructure.pdr.md` and the test-infrastructure section of `plugins/spec-tree/skills/understanding/references/what-goes-where.md`, shared harness/generator code is production code and lives outside `tests/` — for this marketplace, under `outcomeeng_testing/`.

**Migration:**

- Move the helpers to `outcomeeng_testing/harnesses/verdict_toolchain.py` (or a more granular module per concern).
- Import from the new location in each `tests/test_*.scenario.l1.py` file under this node.
- Delete `tests/_helpers.py`.
- Verify with `just check`.

Discovered by `claude-review` on PR 14 (2026-05-13). The PDR's trade-off table acknowledged that pre-existing scaffolding would need a migration sweep; this entry tracks the specific case so `/aligning` surfaces it.
