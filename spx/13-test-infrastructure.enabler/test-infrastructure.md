# Test Infrastructure

PROVIDES a unified quality gate covering static analysis, type checking, linting, and test execution for all implementation code
SO THAT the marketplace's Python scripts, validation tools, and test harnesses
CAN be verified for correctness before changes reach the main branch

## Assertions

### Compliance

- ALWAYS: `just check` runs all quality steps defined by child enablers and exits 0 on a clean main branch — gate integrity requires every step to pass ([test](tests/test_test_infrastructure.integration.py))
