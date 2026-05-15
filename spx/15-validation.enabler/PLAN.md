# PLAN — Reorganize `outcomeeng/` by domain

`outcomeeng/` today is a single flat `scripts/` directory holding ten unrelated entry points plus the `check_pipeline/` engine. The package gives no structural signal about which scripts validate, which package and distribute, which generate documentation, and which fix hygiene issues. New work either lands in `scripts/` (extending the flat dump) or invents a fresh top-level home (creating proliferation).

This plan lives at the validation enabler because the first PR (PR-1) anchors here and the gate engine that spans the whole reorg currently lives inside this node's child. Subsequent PRs touch sibling enablers (`spx/32-distribution.enabler/`, new nodes for catalog and hygiene); their per-PR detail stays in this file until the matching node has its own committed coordination need.

## Target shape

```text
outcomeeng/
├── validation/       ← validators + gate orchestrator (matches spx/15-validation.enabler)
│   ├── __init__.py
│   ├── __main__.py            ← `python -m outcomeeng.validation` runs the full gate
│   ├── plugins.py             ← was scripts/validate_plugins
│   ├── skill_frontmatter.py   ← was scripts/validate_skill_frontmatter
│   ├── install.py             ← was scripts/validate_install
│   ├── eval_links.py          ← was scripts/validate_eval_links
│   ├── _engine.py             ← was scripts/check_pipeline/_runner
│   ├── _model.py              ← was scripts/check_pipeline/_model
│   ├── _spawner.py            ← was scripts/check_pipeline/_spawner
│   └── _steps.py              ← was scripts/check_pipeline/_steps
├── distribution/     ← packaging + marketplace ops (matches spx/32-distribution.enabler)
│   ├── __init__.py
│   ├── build.py               ← was scripts/build_plugins
│   ├── distribute.py          ← was scripts/distribute_skills
│   ├── codex_cache.py         ← was scripts/preserve_codex_plugin_cache
│   ├── sync.py                ← new; replaces the `sync-marketplace` heredoc
│   └── push.py                ← new; replaces the `push-marketplace` heredoc
├── catalog/          ← documentation generators
│   ├── __init__.py
│   └── plugin_catalog.py      ← was scripts/generate_plugin_catalog
├── hygiene/          ← pre-commit fixers + cleanup
│   ├── __init__.py
│   ├── xml_spacing.py         ← was scripts/fix_xml_spacing
│   └── clean.py               ← new; replaces the `clean` find-loop in the Justfile
└── vendor/                    ← unchanged
```

No flat `scripts/` directory survives. Every module exposes `if __name__ == "__main__":` so direct invocations (lefthook hooks, `uv run python -m outcomeeng.validation.skill_frontmatter`, `gh` CI calls) keep working.

The gate engine (`_engine.py`, `_model.py`, `_spawner.py`, `_steps.py`) lives inside `validation/` because that is its only consumer. `distribution/sync.py` and `distribution/push.py` are simple sequential functions; signal forwarding and per-step timing do not earn their weight for one-shot maintenance ops. The engine lifts to a shared home only when a second domain demands it — at which point the second use case drives the extraction shape, not speculation.

## PR sequence

Six PRs, ordered for forward-only landing. Each is independently mergeable, reversible, and ≤300 diff lines where possible. Run `just check` locally before opening each PR; run `just --list` and the affected recipes to confirm the Justfile contract still holds.

| PR | Title                                                         | Net change                                                      | Spec-tree change                                                     | New tests?                                           |
| -- | ------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------- |
| 1  | `refactor(validation): extract validation domain`             | Engine + 4 validators + CLI entry into `outcomeeng/validation/` | Rename `65-check-pipeline.enabler` (decide in PR); ADR paths updated | No — existing tests follow their subjects            |
| 2  | `refactor(distribution): move build, distribute, codex_cache` | 3 existing scripts → `outcomeeng/distribution/`                 | Existing tests update import paths                                   | No                                                   |
| 3  | `feat(distribution): replace sync-marketplace heredoc`        | New `outcomeeng/distribution/sync.py` + spec node + tests       | New enabler under `spx/32-distribution.enabler/`                     | Yes — l1 scenario, l1 compliance                     |
| 4  | `feat(distribution): replace push-marketplace heredoc`        | New `outcomeeng/distribution/push.py` + spec node + tests       | New enabler under `spx/32-distribution.enabler/`                     | Yes — l1 scenario, l1 compliance                     |
| 5  | `refactor(catalog): move plugin_catalog`                      | 1 script → `outcomeeng/catalog/`                                | Confirm or add `spx/15-catalog.enabler/`                             | No                                                   |
| 6  | `refactor(hygiene): xml_spacing move + clean.py`              | xml_spacing rename + new `clean.py` (git-clean-fdX semantics)   | Add `spx/15-hygiene.enabler/`; new node for `clean`                  | Yes — for clean.py (semantics differ from find-loop) |

### PR-1 — validation domain

**Moves (one PR, all callers updated in lockstep):**

- `outcomeeng/scripts/check_pipeline/_runner.py` → `outcomeeng/validation/_engine.py`
- `outcomeeng/scripts/check_pipeline/{_model,_spawner,_steps}.py` → `outcomeeng/validation/{_model,_spawner,_steps}.py`
- `outcomeeng/scripts/check_pipeline/__init__.py` → `outcomeeng/validation/__init__.py`
- `outcomeeng/scripts/validate_plugins.py` → `outcomeeng/validation/plugins.py`
- `outcomeeng/scripts/validate_skill_frontmatter.py` → `outcomeeng/validation/skill_frontmatter.py`
- `outcomeeng/scripts/validate_install.py` → `outcomeeng/validation/install.py`
- `outcomeeng/scripts/validate_eval_links.py` → `outcomeeng/validation/eval_links.py`
- `outcomeeng/scripts/check.py` → `outcomeeng/validation/__main__.py`

**Caller updates in the same PR:**

- `Justfile`: `check`, `check-manifests`, `check-skills`, `check-installed` recipes
- `lefthook.yml`: `validate-skill-frontmatter`, `validate-plugins` hook commands
- `pyproject.toml`: any `[project.scripts]` entries
- `.github/workflows/*.yml`: any reference to old paths
- `outcomeeng/validation/_steps.py`: STEPS argv tuples point at `outcomeeng.validation.X` instead of `outcomeeng.scripts.validate_X`
- `spx/15-validation.enabler/65-check-pipeline.enabler/tests/test_check_pipeline.compliance.l1.py`: `inspect.getfile(pkg)` target updates

**Spec-tree:**

- Rename `spx/15-validation.enabler/65-check-pipeline.enabler/` to the final name (decided in this PR). Candidates: `65-gate.enabler` (matches "quality gate"), or fold the assertions up into `spx/15-validation.enabler/validation.md`. Preference: `65-gate.enabler` — the spec asserts the gate's behavior, not the validation domain's contract.
- Update `15-process-injection.adr.md` path references throughout (the ADR currently names `outcomeeng/scripts/check_pipeline/` in multiple places).

**Test plan:** existing 24 tests pass at new locations; `just check` runs end-to-end; `lefthook run pre-commit` fires hooks against the new paths.

**Estimated diff:** ~250 lines moved + ~50 caller updates.

### PR-2 — distribution existing-script moves

**Moves:**

- `outcomeeng/scripts/build_plugins.py` → `outcomeeng/distribution/build.py`
- `outcomeeng/scripts/distribute_skills.py` → `outcomeeng/distribution/distribute.py`
- `outcomeeng/scripts/preserve_codex_plugin_cache.py` → `outcomeeng/distribution/codex_cache.py`

**Caller updates (every importer of the moved modules; complete list, not "any in-tree script"):**

- `Justfile`: `sync-marketplace` recipe references `outcomeeng.distribution.codex_cache` (still bash for now — PR-3 collapses the heredoc)
- `.github/workflows/distribute-skills.yml`: path reference
- Test imports — importers of `outcomeeng.scripts.build_plugins`:
  - `spx/18-plugin-build.enabler/21-source-and-templating.enabler/tests/test_parse_directives.property.l1.py`
  - `spx/18-plugin-build.enabler/21-source-and-templating.enabler/tests/test_parse_directives.scenario.l1.py`
  - `spx/18-plugin-build.enabler/21-source-and-templating.enabler/tests/test_expand_include.scenario.l1.py`
  - `spx/18-plugin-build.enabler/21-source-and-templating.enabler/tests/test_render_text.scenario.l1.py`
- Test imports — importer of `outcomeeng.scripts.preserve_codex_plugin_cache`:
  - `spx/13-infrastructure.enabler/32-installation.enabler/tests/test_codex_plugin_cache.scenario.l1.py`
- Test imports — importers of `outcomeeng.scripts.distribute_skills`:
  - `spx/32-distribution.enabler/tests/test_distribute_skills.scenario.l1.py`
  - `spx/32-distribution.enabler/tests/test_distribute_skills.property.l1.py`
- `outcomeeng_testing/` importers of `outcomeeng.scripts.build_plugins`:
  - `outcomeeng_testing/harnesses/src_tree.py` (also a prose reference in the module docstring)
  - `outcomeeng_testing/harnesses/dist_tree.py`
  - `outcomeeng_testing/harnesses/scenarios.py`
  - `outcomeeng_testing/generators/directives.py`
- Embedded literal references to `outcomeeng.scripts.build_plugins` in test diagnostics (the four `spx/18-plugin-build.enabler/21-source-and-templating.enabler/tests/` files above carry `"outcomeeng.scripts.build_plugins is a stub; implement it before "` in stub-guard messages); update the literals in the same commit so the diagnostics stay accurate
- Prose references in committed coordination files: `spx/18-plugin-build.enabler/PLAN.md` and `spx/18-plugin-build.enabler/ISSUES.md` mention the old module path — sweep these in the same PR so the escape hatches do not point at a renamed target

**Spec-tree:** the test moves above are spec-tree-internal — no node files move. The four `spx/18-plugin-build.enabler/.../tests/` files and the one `spx/13-infrastructure.enabler/32-installation.enabler/tests/` file stay in their nodes; only their `from outcomeeng.scripts.<X>` imports change to `from outcomeeng.distribution.<Y>`. The `spx/32-distribution.enabler/tests/` files do the same. No additions, deletions, or renames at the node level.

**Test plan:** `just check` runs end-to-end after the move; the nine importing files above pass with the new import paths; `pytest spx/18-plugin-build.enabler` and `pytest spx/13-infrastructure.enabler` both pass.

### PR-3 — `distribution.sync.py`

Replaces this Justfile heredoc:

```bash
sync-marketplace base_ref="":
    # 18 lines: tool-availability check, git-diff change detection,
    # claude plugin update, codex_cache call, validate_install, just check-installed
```

**New module** at `outcomeeng/distribution/sync.py` with a small, sequential orchestration. Does not reuse the gate engine — sync is one-shot maintenance and does not need timing summaries or process-group signal forwarding. Implementation is ~30 lines of Python: argparse for `base_ref`, conditional git-diff change detection, ordered subprocess calls, fail-fast.

**Spec-tree:** new enabler at `spx/32-distribution.enabler/21-sync.enabler/`:

- Scenario: given no plugin distribution changes since base_ref, when sync runs, then it exits 0 without invoking marketplace mutations
- Scenario: given plugin distribution changes, when sync runs, then it invokes (in order) `claude plugin marketplace update`, codex cache preservation, install validation, and installed-skill checks
- Compliance: ALWAYS check tool availability (`claude`, `codex`, `uv`) before any orchestration call
- Compliance: NEVER skip validation steps when changes are present

**Tests:** l1 scenario, l1 compliance. Engine reuse decision: declined. Sync's shape is small and one-shot; pulling the validation domain's engine into `distribution/` would be a speculative extraction.

**Caller updates:** `Justfile` `sync-marketplace` recipe collapses to `uv run python -m outcomeeng.distribution.sync {{base_ref}}`.

### PR-4 — `distribution.push.py`

Replaces this Justfile heredoc:

```bash
push-marketplace *push_args:
    # 16 lines: tool check, upstream ref capture, git push, conditional sync call
```

**New module** at `outcomeeng/distribution/push.py`. Same shape as PR-3: small sequential orchestration, no engine reuse.

**Spec-tree:** new enabler at `spx/32-distribution.enabler/21-push.enabler/` (same-index peer of sync; independent).

**Tests:** l1 scenario, l1 compliance. Assertions cover: upstream ref capture before push, conditional sync invocation only when the pushed range changed plugin distribution paths.

**Caller updates:** `Justfile` `push-marketplace` recipe collapses to `uv run python -m outcomeeng.distribution.push {{push_args}}`.

### PR-5 — catalog domain

**Move:**

- `outcomeeng/scripts/generate_plugin_catalog.py` → `outcomeeng/catalog/plugin_catalog.py`

**Caller updates:**

- `Justfile`: `docs`, `docs-check` recipes
- `.github/workflows/`: any reference

**Spec-tree:** the plugin catalog feature has no current enabler. Decide in this PR: confirm it fits under `spx/15-validation.enabler/` (since `docs-check` is a validation step) or add a new `spx/15-catalog.enabler/`. Preference: new node — the catalog is a documentation generator, not a validator; `docs-check` consumes it but does not define it.

**Test plan:** existing tests for `generate_plugin_catalog` pass at new location.

### PR-6 — hygiene domain

**Moves:**

- `outcomeeng/scripts/fix_xml_spacing.py` → `outcomeeng/hygiene/xml_spacing.py`

**New module:**

- `outcomeeng/hygiene/clean.py` — replaces the Justfile's `find -delete` chain with `git clean -fdX` semantics

**Spec-tree:** new enabler at `spx/15-hygiene.enabler/` with two child nodes: existing xml-spacing tests move; new clean node gets its own assertions.

**Tests:** xml-spacing tests move; new tests for `clean.py`. The behavior diff (`git clean -fdX` removes gitignored files; the find-loop removed specific patterns) needs assertions confirming the new semantics match the user's intent.

**Caller updates:**

- `Justfile`: `clean` recipe collapses to `uv run python -m outcomeeng.hygiene.clean`
- `lefthook.yml`: `fix-xml-spacing` hook command

## Dependency graph

```text
PR-1 (validation)
   │
   └─► PR-2 (distribution moves)
            │
            ├─► PR-3 (sync.py)
            └─► PR-4 (push.py)

PR-5 (catalog) — independent; can land in parallel with any of PR-1..4
PR-6 (hygiene) — independent; can land in parallel with any of PR-1..4
```

Realistic serial order: PR-1 → PR-2 → PR-3 → PR-4 → PR-5 → PR-6. PR-5 and PR-6 can land in parallel with the later distribution PRs if reviewer bandwidth permits.

## Naming decisions deferred to the relevant phase

- `validation/` vs `gate/` vs `checks/` — PR-1 picks the final package name. Current preference is `validation/` because it lines up with `spx/15-validation.enabler` and the existing spec-tree name.
- `65-check-pipeline.enabler` rename target — PR-1. Preference: `65-gate.enabler`.
- `catalog/` vs `docs/` vs `generation/` — PR-5.
- `hygiene/` vs `formatting/` vs `pre_commit/` — PR-6.
- Engine lift to a shared home — deferred until a second domain demonstrates need. Current expectation: declined permanently; sync.py and push.py do not justify reuse.

## Constraints

- Each PR moves the modules and updates every caller in lockstep — `Justfile`, `lefthook.yml`, `pyproject.toml` `[project.scripts]`, CI workflows under `.github/workflows/`, and any in-tree script that invokes the moved path. No shims, no compatibility re-exports, no two-step migrations.
- `Justfile` recipes are the contract every contributor uses; they must continue to work on every merge. Each phase PR runs `just --list` and the affected recipes locally before opening.
- No PR changes the public behavior of any validator, builder, or fixer. The rename PRs are pure rewire; behavior is verified by the existing tests passing unchanged at the new module paths.
- Each PR's compliance and conformance tests update their import paths in lockstep with the move; no test references a stale path after the PR merges.

## Removal

This `PLAN.md` is removed in PR-6 once all six PRs have landed and the spec-tree changes each PR implies are merged. Until then, `/contextualizing` reads it when entering `spx/15-validation.enabler/` or any descendant.
