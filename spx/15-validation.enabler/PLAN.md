# PLAN — enforce "no spec references in code" in the gate

## Goal

Wire enforcement of the `spx/13-plugin-and-runtime-conventions.adr.md` rule —
*"NEVER reference specs or decisions from code; no `ADR-21`, `PDR-13`, or a path
to a specific `*.pdr.md`/`*.adr.md` in code comments or docstrings"* — into
`just check`. The rule is currently **unenforced**: `AGENTS.md` claims "the
semgrep rule enforces this", but no semgrep config exists and the gate runs no
such step. The init-worktrees PR (#143) shipped PDR references in docstrings
that the **CI reviewer** caught, not the gate — proof of the gap.

## Current state (investigated 2026-06-08)

- **No semgrep** anywhere: no `.semgrep/`, no `semgrep` token in any
  `*.md/*.yml/*.toml/justfile`. The AGENTS.md claim is aspirational/stale.
- **ast-grep is not installed** (`command not found`).
- The gate `just check` = `uv run python -m outcomeeng.validation`. Steps are a
  declared list: `outcomeeng/validation/_steps.py` exports `STEPS` (each a frozen
  `Step(label, argv)`); `_engine.py` runs them in order, stops at first failure,
  prints a timing summary. **Adding a check = add a `Step` to `STEPS`.**
- The repo already runs non-Python binaries in tooling (`dprint` is Rust;
  ESLint/vitest for TS), so a Rust binary in the gate is not unprecedented.

## The crux (get the rule scope right)

The toolchain legitimately handles `.pdr.md`/`.adr.md` as **file-extension
patterns** (e.g. `outcomeeng/spec_tree_structure.py`, validation, distribution).
A naive "flag any `.pdr.md`/`.adr.md` string" check **false-positives across the
toolchain.** The rule must target a **specific decision reference**
(`PDR-13`, `ADR-21`, or a path to a specific decision file) appearing in a
**comment or docstring**, not the extension patterns used in code logic.

## Design decision to settle FIRST (with the operator)

Does TypeScript need coverage now, or is Python-first acceptable?

- **ast-grep** (operator's stated preference): tree-sitter; one YAML rule matches
  comment/docstring nodes precisely across **Python + TS**; can autofix. Cost: a
  new Rust-binary dependency — must be installed in the CI `check` workflow under
  `.github/workflows/` and documented as a local prereq.
- **stdlib-Python validation step**: a new `outcomeeng/validation` (or
  `outcomeeng/hygiene`) module; no new dependency; matches the existing stdlib
  pattern. Python comment/docstring extraction is easy (`ast`/`tokenize`); **TS**
  extraction in stdlib is awkward (regex or defer TS to an ESLint rule).

Recommendation: if TS must be covered now → ast-grep (one rule, both languages).
If Python-first is acceptable → a stdlib step is faster and dependency-free, with
TS handled by an ESLint rule later. Either way: scope to comments/docstrings,
exclude the toolchain's extension-pattern handling, add as a new `Step`, and run
it in CI.

## Steps

1. Work in a **pool worktree** (`plugins-a`), never the `main` worktree (it is
   the marketplace source; branching there breaks skill resolution machine-wide).
2. `/understanding` then `/contextualizing spx/15-validation.enabler`; read
   `spx/13-plugin-and-runtime-conventions.adr.md` (the rule's source).
3. Settle ast-grep-vs-stdlib (TS-coverage question above).
4. Implement the rule + a new `Step` in `outcomeeng/validation/_steps.py`;
   if ast-grep, add its install to the CI `check` workflow.
5. Verify it flags violating fixtures AND does **not** flag the toolchain's
   legitimate `.pdr.md`/`.adr.md` pattern handling.
6. Add `[test]` evidence (rule exercised against violating fixtures + the
   false-positive cases), governed by a node under `15-validation.enabler`.
7. Audit gates → `just check` → `/committing-changes` → `/opening-pr` →
   `/managing-pr` to autonomous merge.

## Versioning

This touches `outcomeeng/` + CI/justfile, not `src/plugins/<plugin>/` — so **no
plugin version bump** unless a plugin distribution surface changes.
