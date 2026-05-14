# Issues: Python Standards

## 1. Python skills still use marketplace-local command defaults as generic guidance

`plugins/python/skills/testing-python/SKILL.md` and `plugins/python/skills/auditing-python-tests/SKILL.md` include generic verification snippets using `uv run pytest`, `uv run ruff`, and `uv run mypy`. `plugins/python/skills/coding-python/SKILL.md` includes `just run mypy product/` and `just run ruff check product/`. The Python plugin is installed into consumer products that may not use `uv` or `just`.

Governed by:

- `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/54-execution-level-guidance.enabler/execution-level-guidance.md`
- `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/21-source-testability.enabler/source-testability.md`

Required handling:

- Teach product-canonical command discovery first.
- Use portable fallbacks only when the product lacks a wrapper and the tool is available.
- Keep marketplace-local commands in PR test plans or repository-local docs, not consumer skill defaults.

## 2. Python architecture references still use "test utilities" as a governing category

`plugins/python/skills/architecting-python/SKILL.md` and `plugins/python/skills/architecting-python/references/test-infrastructure-patterns.md` still describe `*_testing/` as "test utilities" in positive guidance. The PDR reserves the governing category term "test infrastructure" and rejects "support", "helpers", "utilities", and "tools" as category names.

Governed by:

- `spx/15-test-infrastructure.pdr.md`
- `spx/43-python.enabler/python.md`
- `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/python-tests.md`

Required handling:

- Replace positive category language with "test infrastructure".
- Keep anti-pattern names only in rejected examples.
- Ensure every positive package-layout example names `generators`, `fixtures`, and `harnesses`.

## 3. Python architecture references understate generators in package-layout guidance

Some positive guidance names `fixtures` and `harnesses` while omitting `generators`, even though the PDR defines the canonical test-infrastructure package as the three-category set `generators`, `fixtures`, and `harnesses`.

Governed by:

- `spx/15-test-infrastructure.pdr.md`
- `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/32-test-data-ownership.enabler/test-data-ownership.md`

Required handling:

- Update positive layout prose and diagrams so `product_testing/` always presents the three categories together.
- Confirm `fixtures` are described as inert files, not importable fixture modules.

## 4. Python skill examples need a final source-testability audit across the whole plugin

PR #25 aligned the main testing and auditing skills, but the broader Python plugin still contains older examples around pytest fixtures, package setup, command execution, and code-standard remediation. Those examples need a full-chain audit against the source-testability stance: tests for existing code normally improve source architecture first.

Governed by:

- `spx/15-test-infrastructure.pdr.md`
- `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/21-source-testability.enabler/source-testability.md`
- `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/43-test-infrastructure-auditing.enabler/test-infrastructure-auditing.md`

Required handling:

- Review every Python skill and reference for copied source vocabulary, constant-only generator guidance, replacement mocks, fixture-body laundering, `sys.path` tricks, and test-owned example bags.
- Fix source guidance first where examples preserve a hard-to-test source shape.
- Validate the edited skills and run `just check`.
