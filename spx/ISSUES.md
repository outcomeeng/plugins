# ISSUES — product-level hygiene

Cross-cutting imperfections noticed in the marketplace that do not belong to a single spec node. Each entry names a file, the exact rule it violates, and the smallest unit of work that resolves it.

`/contextualizing` reads this file at product-root context-load time; the entries are visible to any session that enters `spx/`.

## Lint and format drift in `outcomeeng_*` and `outcomeeng/vendor/`

`uv run ruff check .` reports 5 errors, all fixable with `--fix`:

- `outcomeeng/scripts/validate_plugins.py` — `F541` extraneous `f` prefix on a literal-only f-string.
- `outcomeeng/vendor/anthropics_skills/quick_validate.py` — `F401` unused import (vendored third-party code — `pyproject.toml` already excludes the directory from mypy via `tool.mypy.overrides`; consider adding a ruff `per-file-ignores` entry for `outcomeeng/vendor/**` instead of editing the vendored file).
- `outcomeeng_evals/cli/commands/run.py` — `F401`.
- `outcomeeng_testing/generators/directives.py` — `F401`.
- `spx/32-distribution.enabler/tests/test_distribute_skills.scenario.l1.py` — `F401` (`import os` unused).

`uv run ruff format --check .` reports 4 files needing reformat (same set as above plus `outcomeeng_evals/cli/commands/run.py`).

**Resolution shape**: small `chore(repo): ruff --fix + ruff format` PR. Vendored code gets a `per-file-ignores` rather than an in-file edit. Audit gate: re-run `uv run ruff check . && uv run ruff format --check .` after the fix.

## Stale relative links in spec-tree spec files (RESOLVED)

`spx validation markdown` no longer reports relative-link errors. The session
handoff plan now points at `src/plugins/spec-tree/...`, matching the authored
plugin source tree.

**Resolution evidence**: `spx validation markdown` passes.

## `just check` does not run ruff or `spx validation markdown` (RESOLVED)

`spx/15-validation.enabler/65-check-pipeline.enabler/` declares a signal-safe Python orchestrator at `outcomeeng/scripts/check.py` that replaces the prior bash heredoc. The new step list includes `fmt-check → ruff → manifests → skills → docs-check → markdown → pytest`, so the two previously-missing checks now run on every `just check`. The lint and format entry above remains in scope for a separate `chore(repo): ruff --fix + ruff format` PR if the current branch does not resolve it directly.
