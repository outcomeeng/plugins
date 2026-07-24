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

Governed by `spx/21-spec-tree.enabler/spec-tree.md` and the source-ownership rules in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`.

Required handling:

- Decide whether callers use the enum members directly or source-owned module aliases.
- If aliases remain, document their API purpose in source and keep tests on the chosen spelling.
- If aliases are removed, update tests and regex construction without preserving backward-compatibility shims.

Surfaced by `claude-review` on PR 25 (2026-05-14).

## 18. Invalid node-name mapping cases need clearer source-owned construction

`spx/21-spec-tree.enabler/tests/test_spec_tree.mapping.l1.py` constructs invalid node names through inline transformations such as removing separators, stripping the kind suffix, and prefixing a formatted valid name. The tests are behaviorally correct, but some cases are hard to audit because the invalid shape is implicit in string operations rather than named by a source-owned invalid-case generator or a small explanatory comment.

Governed by `spx/21-spec-tree.enabler/spec-tree.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`.

Required handling:

- Prefer source-owned parser/formatter metadata plus a small generator or helper that names each invalid shape.
- If a case remains inline, add the minimal comment that explains the malformed grammar shape being constructed.
- Keep the assertion as mapping evidence, not property evidence.

Surfaced by `claude-review` on PR 25 (2026-05-14).

## 19. Placeholder notation mixed across inline and code-block commands in merging-standards

`plugins/spec-tree/skills/merging-standards/SKILL.md` uses angle-bracket placeholders (`<pr-number>`, `<branch>`, `<base>`) inside both code blocks and inline backtick snippets. The convention is consistent within the file but the inline form reads as runnable shell when copied without context. Choosing a single convention — angle-brackets in code blocks only, named placeholders inline — would improve copy-paste safety for a reader who pastes an inline snippet into a terminal.

Required handling:

- Decide which form is canonical (angle-bracket everywhere vs. named placeholder inline).
- Sweep `merging-standards/SKILL.md` and any other PR-flow skill that mixes the conventions.

Deferred from `feat/rebase-merge-default` (2026-05-24) because the change widens scope across multiple PR-flow skills; the rebase-merge PR scope is intentionally narrow.

## 22. PR #329 surfaced instruction gaps in spec-tree operations

PR #329 exposed avoidable workflow failures where clearer local instructions or skill guidance would have forced the right action earlier. The incidents below are coordination notes; each item needs a follow-up change in the named surface.

- **Verification-kind vocabulary.** Treated `reviewing` as a skill-naming violation when it was the verification-kind vocabulary, predating the gerund-to-imperative skill rename.
  Preventing instruction: when a term can belong to both a skill-name grammar and the verification taxonomy, inspect the governing vocabulary source and file history before classifying it as a naming defect.
  Suggested surfaces: inline `spec-tree:understand` `<verification_model>`; `instructions:skill-standards`; `spx/AGENTS.md` historical-context guidance.

- **Declared source first.** Looked at implementation/code surfaces before resolving the user-named source of truth.
  Preventing instruction: for vocabulary, taxonomy, and methodology questions, read the declared source first, then use implementation as lower-layer evidence.
  Suggested surfaces: `spx/AGENTS.md`; `spec-tree:understand`; `spec-tree:align`.

- **Mutation status wording.** Used operator-facing shorthand such as "direct config patch" without explaining the exact file and lifecycle impact.
  Preventing instruction: status updates for repository mutations must name the target file, the intended edit, and why it is local enough to proceed.
  Suggested surfaces: `spx/AGENTS.md` clarity rules; `spec-tree:merge`; `spec-tree:manage-pr`.

- **Hosted-service verification.** Answered the SonarQube wildcard question from weak references before testing SonarQube Cloud behavior.
  Preventing instruction: for hosted-tool behavior that differs between cloud and server products, verify against the hosted surface or an experiment before recommending config.
  Suggested surfaces: `spx/AGENTS.md`; a future SonarQube validation note under `spx/15-validation.enabler`.

- **Sibling config comparison.** Set the SonarQube Python version from `/Users/shz/Code/outcomeeng/spx/spx/.sonarcloud.properties` only after explicit correction.
  Preventing instruction: when importing a config pattern from a sibling Outcome Engineering repository, compare the full relevant property set alongside the property under active discussion.
  Suggested surfaces: `spx/AGENTS.md`; `spx/15-validation.enabler` SonarQube guidance.

- **Tool-reported issues.** Saw SonarQube Cloud issue output and continued PR management instead of fixing surfaced issues immediately.
  Preventing instruction: PR management must treat tool-reported issue links and PR comments as actionable review surfaces when they name new-code defects.
  Suggested surfaces: `spec-tree:manage-pr`; `spec-tree:inspect-github-actions`; `spx/AGENTS.md` imperfection protocol examples.

- **Rendered floor output.** Advanced `REQUIRED_SPX_VERSION` and `.github/workflows/check.yml` without immediately rebuilding generated diagnose skill output.
  Preventing instruction: any floor rendered into shipped skill content requires `just build-skills` in the same edit batch before push.
  Suggested surfaces: `spec-tree:commit-changes`; `spx/local/commit-changes.md`; `outcomeeng/validation/spx_version.py` module doc.

- **Ship request status.** Failed to translate "ship it" into the exact current gate state until after another CI pass.
  Preventing instruction: a ship request during an open PR should report the live gate tuple first: head SHA, current-head review state, required checks, production-readiness rule, and next autonomous action.
  Suggested surfaces: `spec-tree:merge`; `spec-tree:manage-pr`; `spx/AGENTS.md` status-update examples.

Suggested `spx/AGENTS.md` additions:

- Add a **source-of-truth first** rule for methodology vocabulary: read specs, decisions, local skill policy, and file history before treating implementation or generated output as authority.
- Add a **hosted-service verification** rule: when a tool has Cloud and Server variants, test or cite the exact hosted variant before changing config.
- Add a **mutation status shape** for operator-facing updates: target path, action, reason, validation plan, and gate impact.
- Add a **rendered-output reminder** for source constants that build into `dist/`: source edits that affect generated plugin content require `just build-skills` before any push.
- Add a **PR gate status shape** for terse prompts such as "check" or "ship it": full head SHA, current-head review verdict, required-check rollup, and the next allowed action token.

## 23. `knowledge/` node subdirectory is not declared in the canonical node shape

`spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/knowledge/oe-skill-eval-brief.md` preserves the external research brief that seeded the eval-verification redesign, placed there by explicit operator instruction. The canonical node shape in the inline `/understand` `<common_structure>` (authored in `src/plugins/spec-tree/skills/understand/SKILL.md`) declares only `{slug}.md`, `tests/`, `evals/{rule-slug}/`, `PLAN.md`, `ISSUES.md`, decision files, and child node directories — no `knowledge/` kind. This is the first `knowledge/` directory in the tree.

Required handling — one of:

- Amend `<common_structure>` in `src/plugins/spec-tree/skills/understand/SKILL.md` to declare `knowledge/` as an optional node artifact (placement, lifecycle, and provenance rules), with the plugin version bump, `just build-skills`, and the `skill-auditor` gate that shipped-skill edit requires.
- Relocate the knowledge content into an already-sanctioned location and remove the directory.

Why deferred: sanctioning a new node-directory kind changes the shipped methodology's node grammar for every consumer repository — a methodology decision with its own gate chain, not a bounded fix inside the spx-only changeset that surfaced it.

Surfaced by the local `changes-reviewer` (run `2026-07-24_18-55-59-928-7b385135ae6b`, debt) on the eval-brief knowledge changeset (2026-07-24).
