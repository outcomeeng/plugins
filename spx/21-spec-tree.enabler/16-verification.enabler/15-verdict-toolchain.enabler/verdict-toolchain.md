# Verification Run Payload Validation

PROVIDES the SPX-owned verification-run payload and projection contract consumed by audit and review skills
SO THAT agentic verification skills
CAN record validated scope evidence, finding evidence, terminal state, and rendered projections without shipping plugin-side verdict schema or rollup scripts

## Assertions

### Compliance

- ALWAYS: audit skills record audit evidence through `spx verification run start`, `spx verification run scope add`, `spx verification run finding add`, `spx verification run finish`, and `spx verification run render` ([test](tests/test_verification_run_payload_contract.compliance.l1.py))
- ALWAYS: the shipped SPX floor is at least the published release that provides the `spx verification run` lifecycle used by audit skills ([test](tests/test_verification_run_payload_contract.compliance.l1.py))
- ALWAYS: verdict format validation, audit finding validation, terminal projection rendering, and authoritative finding count are delegated to SPX verification-run commands rather than plugin-side Python scripts ([test](tests/test_verification_run_payload_contract.compliance.l1.py))
- NEVER: the spec-tree plugin ships `verdict.py`, `aggregate_verdicts.py`, `pass_results.py`, `journal_emit.py`, or `audit_orchestrator.py` under the audit skill ([test](tests/test_verification_run_payload_contract.compliance.l1.py))
- NEVER: the audit skill invokes `python3 "${CLAUDE_SKILL_DIR}/scripts/..."` to validate verdicts, aggregate child results, or render audit projections ([test](tests/test_verification_run_payload_contract.compliance.l1.py))
