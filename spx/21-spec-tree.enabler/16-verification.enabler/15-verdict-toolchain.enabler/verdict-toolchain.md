# Verification Run Payload Validation

PROVIDES the SPX-owned verification-run payload and projection contract consumed by audit and review skills
SO THAT agentic verification skills
CAN record validated scope evidence, finding evidence, terminal state, and rendered projections without shipping plugin-side verdict schema or rollup scripts

## Assertions

### Scenarios

- Given the exact published SPX minimum release, when an implementation-audit verification-run lifecycle executes `start`, `scope add`, `finding add`, `finish`, and `render`, then every command accepts its payload and returns structured output ([test](tests/test_minimum_spx_release.scenario.l3.py))

### Compliance

- ALWAYS: the shipped SPX floor and CI pin are at least the minimum release for the `spx verification run` lifecycle used by audit skills ([test](tests/test_verification_run_payload_contract.compliance.l1.py))
- NEVER: the spec-tree plugin ships `verdict.py`, `aggregate_verdicts.py`, `pass_results.py`, `journal_emit.py`, or `audit_orchestrator.py` under the audit skill ([test](tests/test_verification_run_payload_contract.compliance.l1.py))

### Audit

- ALWAYS: audit skills record audit evidence through `spx verification run start`, `spx verification run scope add`, `spx verification run finding add`, `spx verification run finish`, and `spx verification run render` ([audit])
- ALWAYS: verdict format validation, audit finding validation, terminal projection rendering, and authoritative finding count are delegated to SPX verification-run commands rather than plugin-side Python scripts ([audit])
- NEVER: the audit skill invokes `python3 "${CLAUDE_SKILL_DIR}/scripts/..."` to validate verdicts, aggregate child results, or render audit projections ([audit])
