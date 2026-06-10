# Python Code Quality

PROVIDES ruff linting for Python files and strict mypy plus standard pyright type checking for the importable product packages
SO THAT validation scripts, test harnesses, and utility modules in `outcomeeng`, `outcomeeng_testing`, and `outcomeeng_evals`
CAN maintain type-correct, lint-clean code enforced by `just check`

## Assertions

### Conformance

- Python files pass `ruff check` with the configured rule set ([test](tests/test_python_code_quality.conformance.l2.py))
- The importable product packages pass `mypy --strict` ([test](tests/test_python_code_quality.conformance.l2.py))
- The importable product packages pass `pyright` in standard mode ([test](tests/test_python_code_quality.conformance.l2.py))

### Compliance

- ALWAYS: `ruff check`, `mypy --strict` over the importable product packages, and `pyright` over the importable product packages run as named steps in `just check` — static analysis must block the quality gate ([test](tests/test_python_code_quality.compliance.l2.py))
