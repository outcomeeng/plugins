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

## Stale relative links in spec-tree spec files

`uv run spx validation markdown spx/**/*.md` reports 5 relative-link errors:

- `spx/21-spec-tree.enabler/76-sessions.enabler/PLAN.md:95` → `../../../../plugins/spec-tree/skills/handing-off/references/scope-resolution.md` (path no longer exists).
- `spx/21-spec-tree.enabler/76-sessions.enabler/PLAN.md:96` → `../../../../plugins/spec-tree/bin/session-start` (path no longer exists).
- `spx/21-spec-tree.enabler/spec-tree.md:11` → `tests/test_spec_tree.unit.py` (file does not exist).
- `spx/21-spec-tree.enabler/spec-tree.md:12` → same.
- `spx/21-spec-tree.enabler/spec-tree.md:16` → same.

**Resolution shape**: either remove the broken links (if the referenced artefacts were deliberately deleted) or restore the paths under their correct locations. The session-related links date from earlier handing-off-skill restructuring; the `test_spec_tree.unit.py` links point at a test file that has never existed and may be a copy-paste from a template. Audit gate: re-run `uv run spx validation markdown` after the fix.

## `just check` does not run ruff or `spx validation markdown` (RESOLVED)

`spx/15-validation.enabler/65-check-pipeline.enabler/` declares a signal-safe Python orchestrator at `outcomeeng/scripts/check.py` that replaces the prior bash heredoc. The new step list includes `fmt-check → ruff → manifests → skills → docs-check → markdown → pytest`, so the two previously-missing checks now run on every `just check`. The two entries above are still open imperfections the orchestrator surfaces — they remain in scope for a separate `chore(repo): ruff --fix + ruff format` PR and a follow-up that fixes or removes the broken markdown links.
