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

## 23. Shipped node shape omits the knowledge-root profile rules the methodology declares

The methodology this repository adopts declares that a node may carry one knowledge root — a `knowledge/` directory holding an Open Knowledge Format v0.1 bundle, with the product root carrying `spx/knowledge/` the same way — in the `versions/next/13-knowledge.md` chapter of the `outcomeeng/methodology` repository. The profile requires `index.md` and `log.md` in every bundle, requires typed frontmatter on every non-reserved markdown file, and delivers a node's knowledge root to context loading as its `index.md` listing alone.

The canonical node shape in the inline `/understand` `<files_in_a_node>` (authored in `src/plugins/spec-tree/skills/understand/SKILL.md`) declares the `knowledge/` root, and `<artifact_placement>` admits it in the closed taxonomy. The shipped grammar still omits the profile rules above, and `/contextualize` delivers no knowledge index for a node that carries one.

Required handling: amend `<files_in_a_node>` to declare the profile rules above — `index.md` and `log.md` required in every bundle, typed frontmatter on non-reserved markdown files, and `index.md`-only context delivery — with the plugin version bump, `just build-skills`, and the `skill-auditor` gate that a shipped-skill edit requires. The knowledge root directory itself is declared: `<files_in_a_node>` names `knowledge/` in the canonical node shape and `<artifact_placement>` admits it in the closed taxonomy; the profile rules remain the open work.

Why separate: the amendment changes the shipped methodology's node grammar for every consumer repository and carries its own gate chain, while the changeset that surfaced it conforms one bundle inside this repository's own `spx/` tree.

Surfaced by the local `changes-reviewer` (run `2026-07-24_18-55-59-928-7b385135ae6b`) and the CI reviewer on the eval-brief knowledge changeset, then narrowed to the shipped-grammar gap once the methodology's knowledge chapter settled the directory's standing.

## 24. The eval-lane bullet states the producer-source boundary as harness-enforced

The `/understand` `<files_in_a_node>` eval-lane bullet (authored in `src/plugins/spec-tree/skills/understand/SKILL.md`, mirrored in both generated runtime trees and asserted by the eval-lane `[audit]` assertion in `spx/21-spec-tree.enabler/spec-tree.md`) states "A declared producer source is a repository path outside the eval directory, never a co-located artifact." The "never" clause is convention, not an enforced invariant: `_resolve_repo_relative_path` in `outcomeeng_evals/producer_prompt.py` (the resolver for `prompt_source.producer`/`producers`) rejects absolute paths and parent traversal and requires repo-root containment, but never checks that the resolved path falls outside the eval directory — unlike the template resolver, whose eval-directory containment is code-backed.

**Resolution shape**: either add an eval-directory-exclusion check to producer-path resolution in `outcomeeng_evals/producer_prompt.py` so the code matches the stated invariant, or soften the bullet (and the mirrored spec assertion and changelog entry) to state the boundary as convention across every current usage. The choice spans the eval-harness node's code, so it is not a wording-only edit.

**Why tracked**: surfaced by the CI changeset review on PR #517 (DEBT, head `42d0a9c865ea338a5e0cd259ba9387544b4a094a`); dispositioned as tracked debt by operator direction on that PR's round-six findings under a recorded expense concern.

## 25. The `spx/EXCLUDE` mechanism is still shipped while this repository carries no such file

This repository has no `spx/EXCLUDE` and no root `conftest.py`: no node is in specified state, every declared `[test]` and `[eval]` link resolves, and the `eval-links` validation step fails the gate on a dangling link. The `apply`, `test`, `handoff`, `manage-github-pr`, and `test-typescript` skills still describe exclusion as the specified-state mechanism — the `/understand` foundation states the status-claim model and names the list only as a passing-scope list a toolchain without the claim still reads — and `spx test passing` reads it. The specs `spx/21-spec-tree.enabler/65-apply.enabler/apply.md`, `spx/21-spec-tree.enabler/76-sessions.enabler/25-handoff.enabler/20-closure.enabler/closure.md`, and `spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md` name the file as a mechanism.

The target model replaces the file with committed per-node `spx.status.json` claims: `spx spec status --update` folds available local evidence into the claims and never runs verification; a claim rests as `passed`, `failed`, or `not-run`; CI reproduces every passing claim and refutes what it cannot reproduce; state derives from the claim (no references → `declared`, not-run → `specified`, passed → `passing`, failed or refuted → `failing`). "No passing claim ⇒ not run" is the automatic exclusion, so the file has no remaining content.

**Gate.** The `spx` CLI ships the claim-and-reproduction model (filed in the `outcomeeng/spx` session queue as `2026-07-05_19-20-16`); an `@outcomeeng/spx` release carrying it is published; `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` and `SPX_VERSION` in `.github/workflows/check.yml` advance to it. The installed CLI 0.6.26 already exposes `spx spec status --update` ("refresh each node's `spx.status.json`") while the floor is 0.6.15; whether that release satisfies the first gate is unverified. Committed `spx.status.json` files are not adopted here until the gate holds.

**Resolution shape.** The `/understand` foundation already carries the status-claim model — `references/status-claims.md` replaces `excluded-nodes.md`, and `<malleability_and_state>` and `<decision_to_spec_alignment>` state it. Once the gate holds: sweep the seven skills above (each plugin takes the `skill-auditor` gate and a bump) and the `/apply` fallback sentence in `docs/tutorial.md` that describes the mechanism to consumers; re-point the three specs above from the file to the `specified` state; drop `EXCLUDE` from `PORTABLE_SPX_FILES` in `outcomeeng/validation/reference_portability.py` once no shipped text names it. Per-mechanism evidence readers for eval and audit, and a cost-reward CI reproduction policy, are not required for the retirement.

## 26. Inline-foundation preservation refs are unreconciled

The canonical comparison baseline is `origin/main`. PR 465 is closed as superseded; the restart branch carries the repaired history forward and ships through a fresh pull request.

Preserved refs and observed heads:

- `work/skill-naming-and-subagent-cluster` — repaired PR content rebased onto the current `origin/main`; its tip SHA is checkout-local and changes on each rebase. The pre-rebase preserved head `35001274a20170236016f45aa6403a3fb132f5c4` identifies `work/inline-foundation-salvage`, not this branch. The stale `work/inline-foundation-salvage-restart` ref on origin predates the rename and the rebase; it carries no content this branch lacks.
- `work/inline-understand-foundation-squash` — `701694b1311a176d1de9b16de7498e6181b820b4`.
- `work/foundation-audit-followups` — `f99014054686b47b584ab36311c021755b8c2d8f`.
- `work/inline-understand-foundation-audit-expanded` — `a909ec0494c8e465aa1af126bcf7c83c32581efb`.

`work/inline-understand-foundation-parked` was proven redundant and deleted. No other preservation ref is deleted until every unique change on it has a recorded disposition and every retained change is reachable from a merged changeset. Ship the subagent-creator track through the instructions-node work first.

**Resolution shape.** Contextualize `spx/21-spec-tree.enabler`, `spx/21-spec-tree.enabler/16-verification.enabler`, `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`, `spx/43-instructions.enabler/21-skills.enabler`, and `spx/31-outcomeeng.enabler/31-verification.enabler`; fetch the base and derive each ref's complete commit and patch sets against `origin/main`, comparing the refs pairwise; classify every unique change as already merged, carried by the subagent-creator changeset, retained for a new changeset, superseded by current product truth, or blocked on an explicit product decision, recording full commit identity, affected node, and evidence; group retained changes into dependency-ordered, independently reviewable changesets, keeping skill-content, review-journal, and broader methodology changes separate; ship each through its deterministic lane, typed auditors, changeset review, and `/merge`; delete a ref only after a final comparison proves it carries no unique work.

## The tree's audit assertions keep the pathless tag while the foundation declares the slug form

**Evidence:** The `/understand` foundation and `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` declare the audit tag as `[audit:{rule-slug}]`, the rule slug keying the result in the status claim. Every `[audit]` assertion in this tree, including the ones those two artifacts carry, uses the pathless `([audit])` form, which is the form the installed SPX CLI parses; `spx validation markdown` rejects no other form because it recognizes no other form.

**Impact:** An audit result in this tree has no rule slug to key on, so the status claim the 4.0 projector writes cannot attribute an audit verdict to its assertion until the tree retags.

**Settlement condition:** The SPX CLI release that admits `[audit:{rule-slug}]` is published and the repository floor advances to it, and every audit assertion in this tree carries a rule slug unique within its spec, in the tree migration this repository's consumer Change carries.

## The tree carries the 3.x grammar while the foundation declares 4.0

**Evidence:** Every node directory in this tree is `.enabler` or `.outcome`, every spec is `{slug}.md`, the root spec is `outcomeeng.product.md`, no spec carries front matter or a status claim, and thirty-odd `PLAN.md` files carry work ordering. The node's own `[test]` assertions on `{slug}.md` and the enabler directory describe the parser this repository ships and runs today. The `/understand` foundation, `spx.config.yaml`, and this node's Compliance assertions declare the 4.0 grammar: seven kinds, `{slug}.spec.md`, front matter, the status claim, `ISSUES.md` as the only note, and work ordering in a Change.

**Impact:** `/contextualize`, `/align`, and `/refactor` parse both forms; a reader of this tree sees the prior form until the migration, and a `PLAN.md` here is a note the 4.0 grammar does not admit.

**Settlement condition:** The SPX CLI admits the seven suffixes, `{slug}.spec.md`, front matter, and the status claim; this repository's consumer Change migrates every directory, spec, and `PLAN.md` — the latter into Changes — and these `[test]` assertions state the 4.0 grammar against the migrated parser.
