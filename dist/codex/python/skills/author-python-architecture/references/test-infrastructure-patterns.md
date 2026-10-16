# Test Infrastructure Patterns

Test infrastructure is an architectural concern. Design it once in ADRs, not ad hoc during implementation.

## Contents

- [Vocabulary](#vocabulary)
- [Packaging](#packaging)
- [pytest Import Mode](#pytest-import-mode)
- [ADR Verification Rules](#adr-verification-rules)

## Vocabulary

The governing category is **test infrastructure**, never "test utilities", "support", "helpers", or "tools". It has three kinds: `generators` (variable input domains), `harnesses` (resource lifecycle and access to real behavior), and `fixtures` (inert whole-payload input files consumed by path).

## Packaging

Co-located tests under `spx/.../tests/` are not a package, so they cannot import shared code from a sibling `tests/` directory, and `sys.path` edits in `conftest.py` are forbidden. Test infrastructure lives in an installable `{product}_testing/` package beside the main package.

```text
product/
├── pyproject.toml
├── mypackage/
├── mypackage_testing/
│   ├── generators/        # for example Hypothesis strategies
│   ├── harnesses/         # for example a CLI harness
│   └── fixtures/          # inert files consumed by path
└── spx/.../tests/
```

```toml
[tool.hatch.build.targets.wheel]
packages = ["mypackage", "mypackage_testing"]
```

Tests import generators and harnesses from the package (`from mypackage_testing.generators import valid_users`) and consume fixtures by path, never as imported modules. The product's editable install (portable fallback `python3 -m pip install -e ".[dev]"`) makes both packages importable.

## pytest Import Mode

Co-located test files share names across nodes, so pytest runs with `--import-mode=importlib`:

```toml
[tool.pytest.ini_options]
addopts = "-v --tb=short --import-mode=importlib"
pythonpath = ["."]
```

## ADR Verification Rules

```markdown
## Verification

### Audit

- ALWAYS: test infrastructure is packaged as `{product}_testing/` with `generators/`, `harnesses/`, and inert fixture data under `fixtures/` ([audit])
- ALWAYS: `pyproject.toml` includes `{product}` and `{product}_testing` as installable packages ([audit])
- ALWAYS: pytest uses `--import-mode=importlib` when co-located test files can share module names ([audit])
- NEVER: tests mutate `sys.path` to import shared generators or harnesses ([audit])
```
