# PLAN — Reorganize `outcomeeng/` by domain

`outcomeeng/` today is a single flat `scripts/` directory holding ten unrelated entry points plus the `check_pipeline/` engine. The package gives no structural signal about which scripts validate, which package and distribute, which generate documentation, and which fix hygiene issues. New work either lands in `scripts/` (extending the flat dump) or invents a fresh top-level home (creating proliferation).

This plan reorganizes `outcomeeng/` by purpose so future work has a default home. The reorganization also lifts the gate engine from its current shape-named location (`outcomeeng/scripts/check_pipeline/`) into private infrastructure inside the domain that consumes it.

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

## Phases

Each phase is one PR. Phases land in order; each is independently merge-ready and reversible.

### Phase 1 — Validation domain (FIRST, refactor the just-merged orchestrator)

- Move package: `outcomeeng/scripts/check_pipeline/` → `outcomeeng/validation/`, renaming `_runner.py` → `_engine.py`.
- Move siblings: `outcomeeng/scripts/validate_*.py` → `outcomeeng/validation/*.py` (drop the `validate_` prefix; the domain owns the verb).
- Move CLI entry: `outcomeeng/scripts/check.py` → `outcomeeng/validation/__main__.py`.
- Update Justfile recipes: `check`, `check-manifests`, `check-skills`, `check-installed` invocations.
- Update `lefthook.yml` hook commands.
- Update `pyproject.toml` `[project.scripts]` entries.
- Spec-tree changes:
  - `spx/15-validation.enabler/65-check-pipeline.enabler/` renames to `65-gate.enabler` (or folds into the parent's spec if the assertions are now general enough; decide during the phase).
  - `15-process-injection.adr.md` updates its path references to `outcomeeng/validation/`.
  - Compliance tests update their `inspect.getfile(pkg)` target.
- Remove the lingering `outcomeeng/scripts/` directory once empty.

### Phase 2 — Distribution domain

- Move: `outcomeeng/distribution/{build,distribute,codex_cache}.py` from current `outcomeeng/scripts/`.
- Add: `outcomeeng/distribution/sync.py` and `outcomeeng/distribution/push.py`, replacing the bash heredocs in the Justfile's `sync-marketplace` and `push-marketplace` recipes.
- Update Justfile, lefthook, pyproject scripts.
- Spec-tree changes: `spx/32-distribution.enabler/` gains assertions for the new `sync` and `push` operations; existing tests under that node continue to apply for `build`/`distribute`/`codex_cache`.

### Phase 3 — Catalog and hygiene domains

- Move: `outcomeeng/catalog/plugin_catalog.py` from `outcomeeng/scripts/generate_plugin_catalog.py`.
- Move: `outcomeeng/hygiene/xml_spacing.py` from `outcomeeng/scripts/fix_xml_spacing.py`.
- Add: `outcomeeng/hygiene/clean.py` replacing the Justfile's `clean` find-loop. Prefer `git clean -fdX` semantics (respects `.gitignore`) over the current `find -delete` chain.
- Update Justfile, lefthook, pyproject scripts.
- Spec-tree changes: new enabler nodes for catalog and hygiene if neither already covers the scope; decide during the phase.

## Naming decisions deferred to the relevant phase

- `validation/` vs `gate/` vs `checks/` — Phase 1 picks the final name. Current preference is `validation/` because it lines up with `spx/15-validation.enabler` and the existing spec-tree name.
- `catalog/` vs `docs/` vs `generation/` — Phase 3.
- `hygiene/` vs `formatting/` vs `pre_commit/` — Phase 3.
- Engine lift to a shared home — deferred until a second domain demonstrates need.

## Constraints

- Each phase is one PR that moves the modules and updates every caller in lockstep — `Justfile`, `lefthook.yml`, `pyproject.toml` `[project.scripts]`, CI workflows under `.github/workflows/`, and any in-tree script that invokes the moved path. No shims, no compatibility re-exports, no two-step migrations.
- `Justfile` recipes are the contract every contributor uses; they must continue to work on every merge. Each phase PR runs `just --list` and the affected recipes locally before opening.
- No phase changes the public behavior of any validator, builder, or fixer. The PRs are pure rename + rewire; behavior is verified by the existing tests passing unchanged at the new module paths.
- Each phase's compliance and conformance tests update their import paths in lockstep with the move; no test references a stale path after the phase merges.

## Removal

This `PLAN.md` is removed once all three phases land and the spec-tree changes that each phase implies are merged. Until then, future sessions read this file at product-root context-load time.
