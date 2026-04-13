# Issues: Spec Tree Enabler

Issues discovered during contradiction analysis of `spx/EXCLUDE`, sync-exclude, and the quality gate mechanism. Source: `methodology/skills/skill-structure.md` stale content + cross-file contradiction audit.

## ~~1. State terminology disagrees across three layers~~ (FIXED)

Fixed: `methodology/skills/skill-structure.md` now uses "Declared / Specified / Failing / Passing" matching `durable-map.md`. Also replaced "three phases: spec-tree maintenance, implementation, commit" with "three steps: declare, spec, apply" across all docs and skills. Upstream `outcomeeng/methodology` repo still needs updating.

## 2. spx CLI must own all quality gate concerns

No document states that `spx` owns test execution, linting, type checking, and validation for spec-tree artifacts. The current model has `spx spec apply` writing exclusions into `pyproject.toml` — the new design has `spx` invoking tools directly with the right flags at runtime.

**Design decision:** `spx` discovers tests by walking `spx/**/tests/`, groups by file extension, dispatches to the correct runner per group. `spx test passing` skips EXCLUDE entries. `spx test` runs everything. Same pattern for lint, type check, validate.

**Files to update:** `methodology/skills/skill-structure.md` (add quality gate section). Plugin references: `excluded-nodes.md`, `durable-map.md`. Skills: `testing`, `authoring`, `bootstrapping/templates/spx-claude.md`.

## 3. Spec-tree must never write project config files

Core principle missing from all layers: spec-tree tools never write to `pyproject.toml`, `package.json`, `tsconfig.json`, or any project-owned config. The project's own tools tell the truth about the whole project. `spx` handles scoping at invocation time.

**Consequence:** `spx spec apply` in its current form (writing to `pyproject.toml`) becomes deprecated. The `LanguageAdapter.applyExclusions()` interface evolves from "write config" to "build command flags".

**Files to update:** `excluded-nodes.md` (remove config-writing description). `sync-exclude.md` spec (rewrite to reflect invocation-time filtering). `spx` CLI `spec/apply/` module (redesign).

## 4. `excluded-nodes.md` falsely claims language plugins own sync implementation

Line 31: "the spec-tree plugin defines the convention, language plugins define the implementation." The implementation lives in `outcomeeng/scripts/sync_exclude.py` (marketplace package), not in any language plugin. Under the new design, `spx` CLI owns it entirely.

**File to update:** `plugins/spec-tree/skills/understanding/references/excluded-nodes.md`

## 5. `sync-exclude.md` spec overpromises reusability

Says "SO THAT Python projects using spec-tree CAN..." but the script is embedded in `outcomeeng/scripts/`, uses `Path(__file__).parents[2]` for repo root, and requires the `outcomeeng` package. No external project can use it.

Under the new design, `spx` CLI replaces this script entirely. The spec needs rewriting to describe `spx`'s invocation-time filtering, not a distributable sync script.

**File to update:** `spx/21-spec-tree.enabler/32-evidence.enabler/21-sync-exclude.enabler/sync-exclude.md`

## 6. TypeScript plugin has zero EXCLUDE support

The Python plugin (`testing-python`, `standardizing-python-testing`) documents the EXCLUDE pattern. The TypeScript plugin has no mention of `spx/EXCLUDE`, no sync script, no "specified nodes" step in its testing skill. A TypeScript project using spec-tree would hit a wall after authoring specs and tests.

**Resolution:** `spx` CLI owning quality gate makes this moot — `spx test passing` works regardless of language. But until that's implemented, the gap exists.

## 7. Conflicting sync commands across Python skills

- `spx/CLAUDE.md` line 163: `just sync-exclude`
- `testing-python/SKILL.md` line 113: `just sync-exclude`
- `standardizing-python-testing/SKILL.md` line 927: `uv run python scripts/sync_exclude.py` (wrong path)
- Actual script: `uv run python -m outcomeeng.scripts.sync_exclude`

**Resolution:** All references become `spx test passing` (or similar) once `spx` CLI owns quality gate. Until then, the wrong path in `standardizing-python-testing` is a bug.

## 8. Multi-language test discovery missing from methodology

`spx` should walk the tree and dispatch to the correct runner per file extension. A single `spx/` tree can have Python and TypeScript tests. The `15-test-language.adr.md` ("Python for all nodes") is a project-local choice, not a methodology constraint.

**Files to update:** `methodology/skills/skill-structure.md` (add multi-language principle). `methodology/testing/testing-foundation.md` mentions `status.yaml` (line 510) which is dead — status is derived from test results.

## 9. `committing-changes` references `just check`

`skill-structure.md` line 457: "Run project validation (e.g., `just check`)." Should reference `spx` validation as the spec-tree quality gate. `just check` is the project's own concern, separate from spec-tree.

## 10. Spec headers diverged from upstream methodology

Plugin uses `PROVIDES ... SO THAT ... CAN ...` and `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`. Upstream `outcomeeng/methodology/reference/spec-tree-reference.md` uses `## Enables...` and `## We believe that...`. Plugin leads; upstream needs to catch up.

## 11. Upstream methodology still references `spx-lock.yaml`

`outcomeeng/methodology/reference/spec-tree-reference.md` lines 86-108 describe a lock-file model (`spx-lock.yaml`, blob hashes, "Needs work / Stale / Valid" states) that the plugin replaced with the EXCLUDE + derived-state model. The upstream needs to be rewritten to match.
