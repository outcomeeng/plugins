# Issues: Spec Tree Enabler

Issues discovered during contradiction analysis of `spx/EXCLUDE`, sync-exclude, and the quality gate mechanism. Source: `methodology/skills/skill-structure.md` stale content + cross-file contradiction audit.

## 8. Multi-language test discovery missing from methodology (PARTIAL)

Multi-language discovery is documented in `excluded-nodes.md` and `sync-exclude.md` spec (mapping assertions for pytest/vitest). The `status.yaml` reference in `test-foundation.md` was removed in commit `391e9e5`.

**Remaining:** upstream `outcomeeng/methodology` repo still needs the multi-language principle added to `spec-tree-reference.md`.

## 9. `commit-changes` references `just check`

`skill-structure.md` line 457: "Run product validation (e.g., `just check`)." Should reference `spx` validation as the spec-tree quality gate. `just check` is the product's own concern, separate from spec-tree.

## 10. Spec headers diverged from upstream methodology

Plugin uses `PROVIDES ... SO THAT ... CAN ...` and `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`. Upstream `outcomeeng/methodology/reference/spec-tree-reference.md` uses `## Enables...` and `## We believe that...`. Plugin leads; upstream needs to catch up.

## 11. Upstream methodology still references `spx-lock.yaml`

`outcomeeng/methodology/reference/spec-tree-reference.md` lines 86-108 describe a lock-file model (`spx-lock.yaml`, blob hashes, "Needs work / Stale / Valid" states) that the plugin replaced with the EXCLUDE + derived-state model. The upstream needs to be rewritten to match.

## 12. Repo-wide evidence links still contain legacy test naming (RESOLVED)

Resolved 2026-05-13. Every filename-shaped legacy reference (`*.unit.test.{ext}`, `*.integration.test.{ext}`, `*.e2e.test.{ext}`, `test_*.unit.{ext}`, `test_*.integration.{ext}`, `test_*.e2e.{ext}`) in spec assertions, spec-tree templates, examples, and methodology references was rewritten to the canonical `<subject>.<evidence>.<level>[.<runner>]` form, splitting mixed-evidence specs across one file per evidence type. Remaining mentions of the legacy tokens are scoped to:

- `plugins/{python,typescript}/skills/{python,typescript}-test-standards/SKILL.md` — the forbidden-patterns lists that define what counts as legacy.
- `plugins/typescript/skills/audit-typescript-tests/SKILL.md` and `plugins/develop/skills/audit-skills/references/operational-effectiveness-examples.md` — historical failure cases that contrast legacy with canonical naming.
- `plugins/spec-tree/skills/author/SKILL.md` and `plugins/spec-tree/skills/test/SKILL.md` — authoring/audit checklists that name the forbidden patterns so agents recognize and reject them.

## 13. Marketplace-scoped test-infrastructure evidence needs product-specific checks (RESOLVED)

Resolved 2026-06-15. `spx/13-infrastructure.enabler/21-test-infrastructure.enabler` now carries an `ALWAYS` compliance assertion backed by `tests/test_infra_placement.compliance.l1.py`: the marketplace's `outcomeeng_testing/` home is verified — against the repository's git-tracked files and against synthetic violating placements — to live outside `spx/` and outside any `tests/` directory. `tests/` filename-shape conformance stays with `spx/15-test-language.adr.md` and the validator under `spx/15-validation.enabler/`, not duplicated; `[audit]` remains correct in `spx/15-test-infrastructure.pdr.md` for the cross-product natural-placement rule this repository cannot structurally assert for other products.

## 14. PDR Rust row lacks the hyphen→underscore explanation

`spx/15-test-infrastructure.pdr.md` shows both `<product>-testing` (Cargo package name) and `<product>_testing` (Rust import path) in the per-language table. Cargo normalizes hyphens to underscores in import paths, but readers unfamiliar with this convention may read the two forms as a contradiction. A single inline sentence — *Cargo normalizes hyphens to underscores in the import path: package `product-testing` → `use product_testing::...`* — closes the gap.

Surfaced by `claude-review` on PR 14 round 3 (2026-05-13).

## 15. `commit-changes` example uses uppercase `L1` instead of canonical `l1`

`plugins/spec-tree/skills/commit-changes/SKILL.md` example commit body says "L1 testing" while every other spec assertion, filename, and convention reference uses lowercase `l1`. The current level tokens were retained at the user's direction during PR 14, but the example body should eventually be brought into line so it does not teach the uppercase form to readers who skim examples without reading the surrounding skill.

Surfaced by `claude-review` on PR 14 rounds 2–3 (2026-05-13).

## 16. Spec Tree structure mapping tests still have small API-coverage gaps

PR 25 added `outcomeeng/spec_tree_structure.py`, `outcomeeng_testing/harnesses/spec_tree.py`, and focused scenario, mapping, and conformance tests under `spx/21-spec-tree.enabler/tests/`. Review identified additional mapping contracts that remain worth pinning:

- `iter_node_directories_from_tracked_paths(...)` is exercised through `marketplace_tracked_spx_node_directories(...)`, but lacks a direct mapping test over explicit tracked-path inputs.
- `format_node_directory_name(...)` is used to construct valid inputs, but lacks a direct assertion for its valid output mapping.
- `node_directory_name(...)` is used in scenario tests, but lacks a direct rejection test for an invalid node directory.

Governed by `spx/21-spec-tree.enabler/spec-tree.md`, especially the mapping assertions for node directory parsing, formatting, traversal, and slug spec-file paths.

Required handling:

- Add direct `l1` mapping tests for these contracts.
- Keep expected values source-derived from `outcomeeng/spec_tree_structure.py`; do not introduce test-owned structure constants.
- Run `just test spx/21-spec-tree.enabler/tests/`, `uv run ruff check ...`, `uv run mypy ...`, and `just check`.

Surfaced by `claude-review` on PR 25 (2026-05-14).

## 17. Spec Tree structure API should choose one public spelling for node kinds

`outcomeeng/spec_tree_structure.py` exports both `NodeKind.ENABLER` / `NodeKind.OUTCOME` and module-level aliases `NODE_KIND_ENABLER` / `NODE_KIND_OUTCOME`. Tests import the alias form. The dual spelling is harmless but leaves unclear whether the aliases are intentional source-owned protocol constants or convenience names.

Governed by `spx/21-spec-tree.enabler/spec-tree.md` and the source-ownership rules in `spx/15-test-infrastructure.pdr.md`.

Required handling:

- Decide whether callers use the enum members directly or source-owned module aliases.
- If aliases remain, document their API purpose in source and keep tests on the chosen spelling.
- If aliases are removed, update tests and regex construction without preserving backward-compatibility shims.

Surfaced by `claude-review` on PR 25 (2026-05-14).

## 18. Invalid node-name mapping cases need clearer source-owned construction

`spx/21-spec-tree.enabler/tests/test_spec_tree.mapping.l1.py` constructs invalid node names through inline transformations such as removing separators, stripping the kind suffix, and prefixing a formatted valid name. The tests are behaviorally correct, but some cases are hard to audit because the invalid shape is implicit in string operations rather than named by a source-owned invalid-case generator or a small explanatory comment.

Governed by `spx/21-spec-tree.enabler/spec-tree.md` and `spx/15-test-infrastructure.pdr.md`.

Required handling:

- Prefer source-owned parser/formatter metadata plus a small generator or helper that names each invalid shape.
- If a case remains inline, add the minimal comment that explains the malformed grammar shape being constructed.
- Keep the assertion as mapping evidence, not property evidence.

Surfaced by `claude-review` on PR 25 (2026-05-14).

## 19. Placeholder notation mixed across inline and code-block commands in standardizing-merging

`plugins/spec-tree/skills/merging-standards/SKILL.md` uses angle-bracket placeholders (`<pr-number>`, `<branch>`, `<base>`) inside both code blocks and inline backtick snippets. The convention is consistent within the file but the inline form reads as runnable shell when copied without context. Standardizing on a single convention — angle-brackets in code blocks only, named placeholders inline — would improve copy-paste safety for a reader who pastes an inline snippet into a terminal.

Required handling:

- Decide which form is canonical (angle-bracket everywhere vs. named placeholder inline).
- Sweep `merging-standards/SKILL.md` and any other PR-flow skill that mixes the conventions.

Deferred from `feat/rebase-merge-default` (2026-05-24) because the change widens scope across multiple PR-flow skills; the rebase-merge PR scope is intentionally narrow.

## 20. Hook output-contract vocabulary is not source-owned across hooks and their tests

The five spec-tree hook scripts (`src/plugins/spec-tree/scripts/{session-start,post-compact,pre-compact,enforce-gates,load-gate}.py`) each define their stdout-contract vocabulary — markers such as `<SPEC-TREE_SESSION_START>` / `<SPEC-TREE_RESUMED>`, their attribute names, the `export CLAUDE_SESSION_ID=` env line, and `load-gate.py`'s `spx gate check` argv tokens (`gate`, `check`, `--tool`, `--session-id`, `--transcript`, `--path`, `--command`) and `PreToolUse` decision keys — inline, and their tests hand-write the same literals to assert on subprocess stdout and argv (e.g. `spx/21-spec-tree.enabler/76-sessions.enabler/tests/test_sessions.scenario.l1.py:559`, the `13-agent-environment.enabler` tests, and `spx/21-spec-tree.enabler/13-agent-environment.enabler/54-load-gating.enabler/tests/test_load_gating.scenario.l1.py`). `python:python-test-auditor` flagged this against `spx/15-test-infrastructure.pdr.md` "source contracts come first" on PR for the agent-environment base-staleness work, and again on the load-gating work.

It is not fixed in place because the hook scripts are hyphenated standalone files invoked as `python3 .../<name>.py` — not importable modules — and they ship stdlib-only into consumer repos, so neither the test suite nor a shared constant module can import from them without restructuring how every hook is packaged. The tokens are also spec-declared contract vocabulary (named in `agent-environment.md` / `sessions.md`), so the spec is arguably their source of truth. A proper fix spans all five hooks plus their tests (extract an importable, shippable constants module each hook and each test imports, or generate the tokens from a shared source), which is larger than any single node's changeset and would otherwise leave the agent-environment tests inconsistent with the established, audit-passed sessions-test convention.

**Resolution shape:** decide whether hook output-contract tokens get a single importable source (a stdlib-only module co-located in `scripts/` that both the hyphenated hook entry and the tests import) applied uniformly across all five hooks, or whether spec-declared marker tokens asserted against subprocess stdout are accepted as spec-owned and the rule is scoped to exclude them. Apply the decision to all five hooks and their tests together.

Surfaced by `python-test-auditor` on the `feat/session-start-base-staleness` work (2026-06-14).
