# Python Code Quality

PROVIDES ruff linting, mypy strict type checking, and pyright standard type checking for all Python source files
SO THAT validation scripts, test harnesses, and utility modules in `outcomeeng/`
CAN maintain type-correct, lint-clean code enforced by `just check`

## Assertions

### Conformance

- All Python source files pass `ruff check` with the configured rule set ([test](tests/test_python_code_quality.integration.py))
- All Python source files pass `mypy --strict` ([test](tests/test_python_code_quality.integration.py))
- All Python source files pass `pyright` in standard mode ([test](tests/test_python_code_quality.integration.py))

### Compliance

- ALWAYS: `ruff check`, `mypy`, and `pyright` run as named steps in `just check` — static analysis must block the quality gate ([test](tests/test_python_code_quality.integration.py))
