# CI Execution

PROVIDES Python-owned execution of CI eval plans
SO THAT the eval workflow
CAN run selected suites and cases through one source-owned command instead of assembling `outcomeeng-evals run` invocations inside shell heredocs

## Assertions

### Mappings

- Each CI plan item maps to one `uv run outcomeeng-evals run` argv containing the suite path, plugin directory, worker count, budget ceiling, timeout, and case selectors in plan order ([test](tests/test_ci_execution.mapping.l1.py))
- Empty plans exit successfully without launching a suite command, and any failing suite makes the aggregate command exit non-zero after attempting every selected suite ([test](tests/test_ci_execution.mapping.l1.py))

### Compliance

- ALWAYS: the `outcomeeng-evals` CLI exposes a `ci` subcommand that builds the CI plan and executes it through the Python executor using the same default cost ceilings as the repository eval recipes ([test](tests/test_ci_execution.compliance.l1.py))
