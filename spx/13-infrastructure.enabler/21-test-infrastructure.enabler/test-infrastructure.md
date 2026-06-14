# Test Infrastructure

PROVIDES a unified quality gate covering static analysis, type checking, linting, and test execution for all implementation code
SO THAT the marketplace's Python scripts, validation tools, and test harnesses
CAN be verified for correctness before changes reach the main branch

## Assertions

### Compliance

- ALWAYS: GitHub Actions runs the full quality gate on `pull_request` and on push to `main` by invoking the gate recipe (`just check`, equivalently `uv run python -m outcomeeng.validation`) with the gate's toolchain provisioned at the project's declared Python version, never an inlined or filtered subset and never a soft-passed step, per [15-ci-gate.adr.md](15-ci-gate.adr.md) ([test](tests/test_ci_gate.compliance.l1.py))
- ALWAYS: the gate `check` job runs unconditionally — it carries no job-level `if:` and no job-level `continue-on-error`, so neither a gate step nor the enclosing job can skip or soft-pass the gate, per [15-ci-gate.adr.md](15-ci-gate.adr.md) ([test](tests/test_ci_gate.compliance.l1.py))
