# Plan: Python Standards Skill Hardening

## Purpose

Align the Python plugin skill surface with `spx/15-test-infrastructure.pdr.md` and the Python standards subtree after PR #25. The standards now declare the right methodology; the remaining work is to make every Python skill and reference teach it without marketplace-specific command assumptions, legacy category language, or partial test-infrastructure examples.

## Scope

- `plugins/python/skills/standardizing-python-tests/SKILL.md`
- `plugins/python/skills/testing-python/SKILL.md`
- `plugins/python/skills/auditing-python-tests/SKILL.md`
- `plugins/python/skills/standardizing-python/SKILL.md`
- `plugins/python/skills/coding-python/SKILL.md`
- `plugins/python/skills/auditing-python/SKILL.md`
- `plugins/python/skills/architecting-python/SKILL.md`
- `plugins/python/skills/architecting-python/references/*.md`
- `plugins/python/skills/auditing-python-tests/references/*.md`
- `spx/43-python.enabler/25-python-standards.enabler/**`

## Required Skills

Use these in order for the implementation PR:

1. `spec-tree:understanding`
2. `spec-tree:contextualizing` for `spx/43-python.enabler/25-python-standards.enabler`
3. `develop:creating-skills` before editing Python `SKILL.md` files
4. `python:testing-python` before changing Python test guidance
5. `python:auditing-python-tests` after changing Python test guidance
6. `python:coding-python` before changing implementation guidance
7. `python:auditing-python` after changing implementation guidance
8. `spec-tree:committing-changes` before committing
9. GitHub PR workflow skills before publishing, review handling, and merge

## Work Plan

### 1. Freeze The Current Skill Surface

- Inventory all Python skill and reference files that mention test infrastructure, fixtures, generators, harnesses, pytest discovery, command execution, `uv`, `just`, `src.*`, `tests/helpers`, `tests/support`, or `test utilities`.
- Classify each hit as accepted anti-pattern example, consumer-facing guidance, repository-local instruction, or stale wording.
- Keep a short audit table in the PR body; do not encode audit state in specs.

### 2. Remove Consumer-Portability Drift

- Replace generic `uv run ...`, `just run ...`, and `just check` fallback guidance in Python skills with product-canonical command discovery.
- When a fallback is necessary, prefer Python-portable shapes such as `python3 -m pytest` only when the product has pytest installed and no canonical wrapper exists.
- Keep marketplace-only commands in marketplace validation notes or PR test plans, not in consumer skill instructions.
- Preserve the rule that tools unavailable in the product are reported explicitly rather than silently skipped.

### 3. Normalize Test-Infrastructure Language

- Replace governing-category uses of "test utilities", "support", "helpers", and similar terms with "test infrastructure".
- Ensure every package-layout example includes all three PDR categories: `generators`, `fixtures`, and `harnesses`.
- Keep rejected examples that name `tests/helpers`, `tests/support`, or fixture body code in `conftest.py`, but mark them clearly as rejected shapes.
- Ensure fixture examples describe inert files consumed by path, reading, or copying.

### 4. Tighten Source-Testability Guidance Across All Python Skills

- Ensure `/testing-python` and `/auditing-python-tests` both force source architecture changes before accepting copied literals, constant-only generators, replacement mocks, or fixture-file laundering.
- Ensure `/coding-python` treats source-owned protocols, registries, schemas, constructors, and dependency boundaries as implementation obligations, not test conveniences.
- Ensure `/architecting-python` teaches thin command/script boundaries, injectable side-effect protocols, and `product_testing/` packaging without old helper language.
- Ensure `/auditing-python` opens relevant test-infrastructure imports when code quality findings depend on test evidence.

### 5. Reconcile Execution-Level Guidance

- Verify the skill prose matches `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/54-execution-level-guidance.enabler/execution-level-guidance.md`.
- Ensure examples choose `l1`, `l2`, and `l3` from dependency cost and locality, not runner names or perceived end-to-end depth.
- Determine whether separate reference files named `l1-local-deterministic.md`, `l2-local-infrastructure.md`, and `l3-remote-credentialed.md` are needed for the Python plugin; if added, keep them as skill references, not spec files.

### 6. Validate And Publish

- Run skill validation for every edited Python skill.
- Run frontmatter validation for every edited `SKILL.md`.
- Run `just check` from the marketplace root.
- Open a focused PR that only changes Python standards skills, references, and node-local coordination files.
- Request adversarial review focused on PDR alignment, consumer portability, source-testability stance, and literal-laundering resistance.

## Acceptance Criteria

- No Python skill teaches `uv`, `just`, or marketplace-local commands as generic consumer fallbacks.
- No Python skill uses "test utilities", "support", or "helpers" as a governing category for test infrastructure.
- Every positive test-infrastructure layout includes `generators`, `fixtures`, and `harnesses`.
- Every positive generator example has meaningful variation or explicitly imports a source-owned singleton directly.
- Every fixture example is inert and consumed by path, reading, or copying.
- Every harness example manages resources or access to real behavior and does not own domain truth.
- `just check` passes on the PR branch.
