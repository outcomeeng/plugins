# Execution Level Guidance

PROVIDES the Python expression of the neutral execution-level semantics
SO THAT Python test authors
CAN choose `l1`, `l2`, or `l3` through Python's tools and dependency surfaces without re-deriving the neutral level rules

## Assertions

### Compliance

- ALWAYS: Python execution-level specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md` for the neutral execution-level semantics — the level definitions, runner independence, lowest-level selection, the level floor, and fail-loud evidence availability — and declare only the Python delta ([audit])
- ALWAYS: Python execution-level guidance realizes the neutral levels through Python surfaces — `tmp_path` and `tmp_path_factory` handles for `l1` filesystem work, dependency-injected Stage 5 collaborators behind `Protocol` boundaries at `l1`, bootstrap-installed product binaries at `l2`, credentialed remote services reached through injected typed client collaborators at `l3` — and never restates the neutral category lists, whose semantics derive from `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md` ([audit])
- ALWAYS: level documentation names files by operational meaning, such as `l1-local-deterministic.md`, `l2-local-infrastructure.md`, and `l3-remote-credentialed.md` — filenames describe the level rather than repeating the level token ([audit])
- ALWAYS: pytest, Playwright, or another runner receives a runner token when it is not the default runner, while its level still derives from the neutral semantics ([audit])
- ALWAYS: level examples obey source-testability and test-data ownership rules — execution level does not permit copied literals, constant-only generators, replacement mocks, or `conftest.py` fixture-body laundering ([audit])
- NEVER: let missing mandatory credentials, base URLs, binaries, or local services produce a passing test — a Python suite realizes the optional-evidence skip only through an explicit pytest skip marker (`pytest.skip` or `pytest.mark.skip`/`skipif`) on evidence the suite declares optional ([audit])
