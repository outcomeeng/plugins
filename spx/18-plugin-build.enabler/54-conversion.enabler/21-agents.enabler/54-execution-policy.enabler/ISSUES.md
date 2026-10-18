# ISSUES — execution policy enabler

Coordination note; not spec truth.

## Permission-mode mapping test reads its oracle from the converter table

- **Severity:** WARNING (non-blocking)
- **Source:** test-evidence audit, finding f-001, property oracle-independence
- **Evidence:** `tests/test_execution_policy.mapping.l1.py`, line 33, covering the assertion "Source `permissionMode` values with a declared Codex equivalent map to `sandbox_mode`, and values the declared rows leave unmapped map to manual-review guidance in `developer_instructions`".

Audit text: "test_permission_modes_map_to_codex_sandbox_or_manual_review compares map_permission_mode(source) with PERMISSION_MODE_MAPPINGS, the table the function reads. Mutating a table value passes this test and the downstream convert_agent tests. The spec assigns agreement between the declared rows and the converter table to [audit:declared-values-match-converter], so this is non-blocking. The test still fails if the mapping function or the convert_agent wiring is mutated."

- **Why it stands:** the `[audit:declared-values-match-converter]` assertion holds the converter table to the spec's declared rows, so table agreement is verified there and not by this test.
- **Impact:** a mutated table value passes this test and the downstream `convert_agent` tests; only the audit assertion catches it.
- **Settlement condition:** the mapping test derives its expected values from an oracle independent of the converter table, or the audit assertion is replaced by deterministic evidence that the converter table equals the declared rows.
