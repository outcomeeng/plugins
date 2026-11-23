# Issues: Product Tree Enabler

Known defects, contradictions, and gaps of the product-tree enabler, each with its evidence and settlement condition.

## 8. Multi-language test discovery missing from methodology (PARTIAL)

Multi-language discovery is documented in `excluded-nodes.md` and `sync-exclude.md` spec (mapping assertions for pytest/vitest). The `status.yaml` reference in `test-foundation.md` was removed in commit `391e9e5`.

**Remaining:** upstream `outcomeeng/methodology` repo still needs the multi-language principle added to `product-tree-reference.md`.

## 9. `commit-changes` references `just check`

`skill-structure.md` line 457: "Run product validation (e.g., `just check`)." Should reference `spx` validation as the product-tree quality gate. `just check` is the product's own concern, separate from product-tree.

## 10. Spec headers diverged from upstream methodology

Plugin uses `PROVIDES ... SO THAT ... CAN ...` and `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`. Upstream `outcomeeng/methodology/reference/product-tree-reference.md` uses `## Enables...` and `## We believe that...`. Plugin leads; upstream needs to catch up.

## 11. Upstream methodology still references `spx-lock.yaml`

`outcomeeng/methodology/reference/product-tree-reference.md` lines 86-108 describe a lock-file model (`spx-lock.yaml`, blob hashes, "Needs work / Stale / Valid" states) that the plugin replaced with the EXCLUDE + derived-state model. The upstream needs to be rewritten to match.

## 15. `commit-changes` example uses uppercase `L1` instead of canonical `l1`

`plugins/product-tree/skills/commit-changes/SKILL.md` example commit body says "L1 testing" while every other spec assertion, filename, and convention reference uses lowercase `l1`. The current level tokens were retained at the user's direction during PR 14, but the example body should eventually be brought into line so it does not teach the uppercase form to readers who skim examples without reading the surrounding skill.

Surfaced by `claude-review` on PR 14 rounds 2–3 (2026-05-13).

## 16. Product Tree structure mapping tests still have small API-coverage gaps

PR 25 added `outcomeeng/product_tree_structure.py`, `outcomeeng_testing/harnesses/product_tree.py`, and focused scenario, mapping, and conformance tests under `spx/21-product-tree.enabler/tests/`. Review identified additional mapping contracts that remain worth pinning:

- `iter_node_directories_from_tracked_paths(...)` is exercised through `marketplace_tracked_spx_node_directories(...)`, but lacks a direct mapping test over explicit tracked-path inputs.
- `format_node_directory_name(...)` is used to construct valid inputs, but lacks a direct assertion for its valid output mapping.
- `node_directory_name(...)` is used in scenario tests, but lacks a direct rejection test for an invalid node directory.

Governed by `spx/21-product-tree.enabler/product-tree.md`, especially the mapping assertions for node directory parsing, formatting, traversal, and slug spec-file paths.

Required handling:

- Add direct `l1` mapping tests for these contracts.
- Keep expected values source-derived from `outcomeeng/product_tree_structure.py`; do not introduce test-owned structure constants.
- Run `just test spx/21-product-tree.enabler/tests/`, `uv run ruff check ...`, `uv run mypy ...`, and `just check`.

Surfaced by `claude-review` on PR 25 (2026-05-14).

## 17. Product Tree structure API should choose one public spelling for node kinds

`outcomeeng/product_tree_structure.py` exports both `NodeKind.ENABLER` / `NodeKind.OUTCOME` and module-level aliases `NODE_KIND_ENABLER` / `NODE_KIND_OUTCOME`. Tests import the alias form. The dual spelling is harmless but leaves unclear whether the aliases are intentional source-owned protocol constants or convenience names.

Governed by `spx/21-product-tree.enabler/product-tree.md` and the source-ownership rules in [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md).

Required handling:

- Decide whether callers use the enum members directly or source-owned module aliases.
- If aliases remain, document their API purpose in source and keep tests on the chosen spelling.
- If aliases are removed, update tests and regex construction without preserving backward-compatibility shims.

Surfaced by `claude-review` on PR 25 (2026-05-14).

## 18. Invalid node-name mapping cases need clearer source-owned construction

`spx/21-product-tree.enabler/tests/test_product_tree.mapping.l1.py` constructs invalid node names through inline transformations such as removing separators, stripping the kind suffix, and prefixing a formatted valid name. The tests are behaviorally correct, but some cases are hard to audit because the invalid shape is implicit in string operations rather than named by a source-owned invalid-case generator or a small explanatory comment.

Governed by `spx/21-product-tree.enabler/product-tree.md` and [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md).

Required handling:

- Prefer source-owned parser/formatter metadata plus a small generator or helper that names each invalid shape.
- If a case remains inline, add the minimal comment that explains the malformed grammar shape being constructed.
- Keep the assertion as mapping evidence, not property evidence.

Surfaced by `claude-review` on PR 25 (2026-05-14).

## 19. Placeholder notation mixed across inline and code-block commands in merging-standards

`plugins/product-tree/skills/merging-standards/SKILL.md` uses angle-bracket placeholders (`<pr-number>`, `<branch>`, `<base>`) inside both code blocks and inline backtick snippets. The convention is consistent within the file but the inline form reads as runnable shell when copied without context. Choosing a single convention — angle-brackets in code blocks only, named placeholders inline — would improve copy-paste safety for a reader who pastes an inline snippet into a terminal.

Required handling:

- Decide which form is canonical (angle-bracket everywhere vs. named placeholder inline).
- Sweep `merging-standards/SKILL.md` and any other PR-flow skill that mixes the conventions.

Deferred from `feat/rebase-merge-default` (2026-05-24) because the change widens scope across multiple PR-flow skills; the rebase-merge PR scope is intentionally narrow.

## 22. PR #329 surfaced instruction gaps in product-tree operations

PR #329 exposed avoidable workflow failures where clearer local instructions or skill guidance would have forced the right action earlier. The incidents below are known defects; each item needs a follow-up change in the named surface.

- **Verification-kind vocabulary.** Treated `reviewing` as a skill-naming violation when it was the verification-kind vocabulary, predating the gerund-to-imperative skill rename.
  Preventing instruction: when a term can belong to both a skill-name grammar and the verification taxonomy, inspect the governing vocabulary source and file history before classifying it as a naming defect.
  Suggested surfaces: inline `product-tree:understand` `<verification_model>`; `instructions:skill-standards`; `spx/AGENTS.md` historical-context guidance.

- **Declared source first.** Looked at implementation/code surfaces before resolving the user-named source of truth.
  Preventing instruction: for vocabulary, taxonomy, and methodology questions, read the declared source first, then use implementation as lower-layer evidence.
  Suggested surfaces: `spx/AGENTS.md`; `product-tree:understand`; `product-tree:align`.

- **Mutation status wording.** Used operator-facing shorthand such as "direct config patch" without explaining the exact file and lifecycle impact.
  Preventing instruction: status updates for repository mutations must name the target file, the intended edit, and why it is local enough to proceed.
  Suggested surfaces: `spx/AGENTS.md` clarity rules; `product-tree:merge`; `product-tree:manage-pr`.

- **Hosted-service verification.** Answered the SonarQube wildcard question from weak references before testing SonarQube Cloud behavior.
  Preventing instruction: for hosted-tool behavior that differs between cloud and server products, verify against the hosted surface or an experiment before recommending config.
  Suggested surfaces: `spx/AGENTS.md`; a future SonarQube validation note under `spx/15-validation.enabler`.

- **Sibling config comparison.** Set the SonarQube Python version from `/Users/shz/Code/outcomeeng/spx/spx/.sonarcloud.properties` only after explicit correction.
  Preventing instruction: when importing a config pattern from a sibling Outcome Engineering repository, compare the full relevant property set alongside the property under active discussion.
  Suggested surfaces: `spx/AGENTS.md`; `spx/15-validation.enabler` SonarQube guidance.

- **Tool-reported issues.** Saw SonarQube Cloud issue output and continued PR management instead of fixing surfaced issues immediately.
  Preventing instruction: PR management must treat tool-reported issue links and PR comments as actionable review surfaces when they name new-code defects.
  Suggested surfaces: `product-tree:manage-pr`; `product-tree:inspect-github-actions`; `spx/AGENTS.md` imperfection protocol examples.

- **Rendered floor output.** Advanced `REQUIRED_SPX_VERSION` and `.github/workflows/check.yml` without immediately rebuilding generated diagnose skill output.
  Preventing instruction: any floor rendered into shipped skill content requires `just build-skills` in the same edit batch before push.
  Suggested surfaces: `product-tree:commit-changes`; `spx/local/commit-changes.md`; `outcomeeng/validation/spx_version.py` module doc.

- **Ship request status.** Failed to translate "ship it" into the exact current gate state until after another CI pass.
  Preventing instruction: a ship request during an open PR should report the live gate tuple first: head SHA, current-head review state, required checks, production-readiness rule, and next autonomous action.
  Suggested surfaces: `product-tree:merge`; `product-tree:manage-pr`; `spx/AGENTS.md` status-update examples.

Suggested `spx/AGENTS.md` additions:

- Add a **source-of-truth first** rule for methodology vocabulary: read specs, decisions, local skill policy, and file history before treating implementation or generated output as authority.
- Add a **hosted-service verification** rule: when a tool has Cloud and Server variants, test or cite the exact hosted variant before changing config.
- Add a **mutation status shape** for operator-facing updates: target path, action, reason, validation plan, and gate impact.
- Add a **rendered-output reminder** for source constants that build into `dist/`: source edits that affect generated plugin content require `just build-skills` before any push.
- Add a **PR gate status shape** for terse prompts such as "check" or "ship it": full head SHA, current-head review verdict, required-check rollup, and the next allowed action token.

## 23. Shipped node shape omits the knowledge-root profile rules the methodology declares

The methodology this repository adopts declares that a node may carry one knowledge root — a `knowledge/` directory holding an Open Knowledge Format v0.2 bundle, with the product root carrying `spx/knowledge/` the same way — in the `versions/4.0/methodology/knowledge.md` chapter of the `outcomeeng/methodology` repository. The profile requires `index.md` and `log.md` in every bundle, requires typed frontmatter on every non-reserved markdown file, and delivers a node's knowledge root to context loading as its `index.md` listing alone.

The canonical node shape in the inline `/understand` `<files_in_a_node>` (authored in `src/plugins/product-tree/skills/understand/SKILL.md`) declares the `knowledge/` root, and `<artifact_placement>` admits it in the closed taxonomy. The shipped grammar still omits the profile rules above, and `/contextualize` delivers no knowledge index for a node that carries one.

Required handling: amend `<files_in_a_node>` to declare the profile rules above — `index.md` and `log.md` required in every bundle, typed frontmatter on non-reserved markdown files, and `index.md`-only context delivery — with the plugin version bump, `just build-skills`, and the `skill-auditor` gate that a shipped-skill edit requires. The knowledge root directory itself is declared: `<files_in_a_node>` names `knowledge/` in the canonical node shape and `<artifact_placement>` admits it in the closed taxonomy; the profile rules remain the open work.

Why separate: the amendment changes the shipped methodology's node grammar for every consumer repository and carries its own gate chain, while the changeset that surfaced it conforms one bundle inside this repository's own `spx/` tree.

Surfaced by the local `changes-reviewer` (run `2026-07-24_18-55-59-928-7b385135ae6b`) and the CI reviewer on the eval-brief knowledge changeset, then narrowed to the shipped-grammar gap once the methodology's knowledge chapter settled the directory's standing.

## 24. The eval-lane bullet states the producer-source boundary as harness-enforced

The `/understand` `<files_in_a_node>` eval-lane bullet (authored in `src/plugins/product-tree/skills/understand/SKILL.md`, mirrored in both generated runtime trees and asserted by the `eval-lane-file-set` Audit row in `spx/21-product-tree.enabler/product-tree.md`) states "A declared producer source is a repository path outside the eval directory, never a co-located artifact." The "never" clause is convention, not an enforced invariant: `_resolve_repo_relative_path` in `outcomeeng_evals/producer_prompt.py` (the resolver for `prompt_source.producer`/`producers`) rejects absolute paths and parent traversal and requires repo-root containment, but never checks that the resolved path falls outside the eval directory — unlike the template resolver, whose eval-directory containment is code-backed.

**Resolution shape**: either add an eval-directory-exclusion check to producer-path resolution in `outcomeeng_evals/producer_prompt.py` so the code matches the stated invariant, or soften the bullet (and the mirrored spec assertion and changelog entry) to state the boundary as convention across every current usage. The choice spans the eval-harness node's code, so it is not a wording-only edit.

**Why tracked**: surfaced by the CI changeset review on PR #517 (DEBT, head `42d0a9c865ea338a5e0cd259ba9387544b4a094a`); dispositioned as tracked debt by operator direction on that PR's round-six findings under a recorded expense concern.

## 26. Inline-foundation preservation refs are unreconciled

The canonical comparison baseline is `origin/main`. PR 465 is closed as superseded; the restart branch carries the repaired history forward and ships through a fresh pull request.

Preserved refs and observed heads:

- `work/skill-naming-and-subagent-cluster` — repaired PR content rebased onto the current `origin/main`; its tip SHA is checkout-local and changes on each rebase. The pre-rebase preserved head `35001274a20170236016f45aa6403a3fb132f5c4` identifies `work/inline-foundation-salvage`, not this branch. The stale `work/inline-foundation-salvage-restart` ref on origin predates the rename and the rebase; it carries no content this branch lacks.
- `work/inline-understand-foundation-squash` — `701694b1311a176d1de9b16de7498e6181b820b4`.
- `work/foundation-audit-followups` — `f99014054686b47b584ab36311c021755b8c2d8f`.
- `work/inline-understand-foundation-audit-expanded` — `a909ec0494c8e465aa1af126bcf7c83c32581efb`.

`work/inline-understand-foundation-parked` was proven redundant and deleted. No other preservation ref is deleted until every unique change on it has a recorded disposition and every retained change is reachable from a merged changeset. Ship the subagent-creator track through the instructions-node work first.

**Resolution shape.** Contextualize `spx/21-product-tree.enabler`, `spx/21-product-tree.enabler/16-verification.enabler`, `spx/21-product-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`, `spx/43-instructions.enabler/21-skills.enabler`, and `spx/31-outcomeeng.enabler/31-verification.enabler`; fetch the base and derive each ref's complete commit and patch sets against `origin/main`, comparing the refs pairwise; classify every unique change as already merged, carried by the subagent-creator changeset, retained for a new changeset, superseded by current product truth, or blocked on an explicit product decision, recording full commit identity, affected node, and evidence; group retained changes into dependency-ordered, independently reviewable changesets, keeping skill-content, review-journal, and broader methodology changes separate; ship each through its deterministic lane, typed auditors, changeset review, and `/merge`; delete a ref only after a final comparison proves it carries no unique work.

## The tree migration has not retagged every `[audit]` assertion into the row form the foundation declares

**Evidence:** The `/understand` foundation, `references/grammar.md`, and `/verify` write a spec assertion as a row that opens with its slug under a group heading naming its verification type, with no tag, as [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) declares, and `spx/21-product-tree.enabler/product-tree.md` writes that form. Every other `[audit]` assertion in this tree keeps the pathless `([audit])` tail the installed SPX CLI parses. `/verify` routes an eval to `product-tree:eval`, and no such skill is installed.

**Impact:** A reader meets two assertion forms across the tree, and `/verify` reports `capability-required` for an eval assertion until a specialist is installed.

**Settlement condition:** The tree migration this repository's consumer Change carries retags the remaining `([audit])` assertions into the row form, and a `product-tree:eval` skill is installed or the eval route is removed.

## The tree carries the 3.x grammar while the foundation declares 4.0

**Evidence:** Every node directory in this tree is `.enabler` or `.outcome`, every spec is `{slug}.md`, the root spec is `outcomeeng.product.md`, no spec carries a status claim, front matter is partial and unprojected — every node spec under `spx/21-product-tree.enabler` and `spx/43-coding-agents.enabler`, and `spx/31-outcomeeng.enabler/32-changes.enabler/changes.md`, carries an `id` and `malleability: spec`, and `spx/21-product-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md` also carries a `tier` field, all of which `spx validation markdown` accepts and `spx spec status` does not project, while the node specs of every other subtree carry no front matter. The node's own Test rows in `spx/21-product-tree.enabler/product-tree.md` write the 4.0 row form, and their subject is `{slug}.md` and the enabler directory, the parser this repository ships and runs today. The `/understand` foundation, `spx.config.yaml`, and this node's Compliance assertions declare the 4.0 grammar: seven kinds, `{slug}.spec.md`, front matter, the status claim, `ISSUES.md` as the only note, and work ordering in a Change.

**Impact:** `/contextualize`, `/align`, and `/refactor` parse both forms; a reader of this tree sees the prior form until the migration.

**Settlement condition:** The SPX CLI admits the seven suffixes, `{slug}.spec.md`, front matter, and the status claim; this repository's consumer Change migrates every directory and spec, and these Test rows state the 4.0 grammar against the migrated parser.

## DEBT [payload]: the foundation renders 94 and 171 code points under its eager ceiling

Defect class: `payload`.

Finding: the rendered `understand` SKILL.md holds 39,906 code points in the Claude tree and 39,829 in the Codex tree against the 40,000 ceiling of `/skill-standards` `<eager_foundation_exception>`, which leaves 94 and 171 code points of headroom. The typed skill audit of `understand` on the Change Lifecycle changeset (head `a28a5be91fc2ea04151c283059caa9cb9a11fd12`) also found `references/product-domain-shapes.md` pointing at `kind-decision.md` by bare filename, and self-trigger statements at the operational-continuation and note-discovery sentences.

Evidence: the rendered payload measurements above, taken after the Change's Activity 22; `instructions:skill-auditor` findings f-008, f-009, f-010 on `src/plugins/product-tree/skills/understand/SKILL.md`; the second pass added that the passing-scope-list clause is stated three times (line 45, line 175, `references/status-claims.md`) and that every node template and example writes the `[test]` path in one language's filename form where `references/grammar.md` admits three.

Impact: 94 code points of headroom in the Claude tree and 171 in the Codex tree leave room for no wording edit; the next one can push the rendered payload over the ceiling and turn an approval into a must-fix.

Successor: a Proposed Change filed after outcomeeng/changes#91 merges.

Revisit and settlement condition: one conditional paragraph moved into the reference that owns its detail, the bare pointer spelled through `${CLAUDE_SKILL_DIR}`, the self-trigger clauses dropped, and one typed skill audit approving with headroom above 1,000 code points.

## The refocus skill body carries skill-standards conformance debt

**Evidence:** typed skill-auditor run `/root/audit_refocus_skill_round_1` reported the following findings against `src/plugins/product-tree/skills/refocus/SKILL.md` while its amended activation description passed:

- Warning f-004: the success criteria do not name an observable handoff or verification state.
- Warning f-005: the success criteria repeat the requirement to stop further ad hoc commands.
- Round 2 warning f-003: the phrase “a monumental waste of effort” is motivational prose without an operational condition or verification signal.
- Finding f-006: unrestricted `Bash` admits the uncontrolled operations the workflow is intended to stop.
- Finding f-007: the ordered recovery procedure uses `<process>` instead of the canonical `<workflow>` section.
- Finding f-008: deletion of undefined ad hoc scripts or debug code lacks deterministic ownership and target criteria.
- Finding f-009: the skill requires `/apply` without declaring and authorizing that composition.

**Impact:** the unchanged body and tool grant do not fully conform to the skill standards, leaving completion partly uncheckable, recovery structure noncanonical, deletion targets underspecified, shell authority broader than the workflow needs, and the required composed workflow unavailable through the declared contract.

**Settlement condition:** a Change on the refocus skill body's conformance to the skill standards resolves all six findings and receives an approving typed skill-auditor verdict.

## The refocus skill has no direct product-tree coverage link

**Evidence:** a governance search for `src/plugins/product-tree/skills/refocus/SKILL.md` and `refocus` under `spx/` found no spec assertion or linked test that names the skill surface; its placement under the product-tree plugin is the only ownership signal.

**Impact:** the skill can change without invalidating node-specific evidence, and its governing node must be inferred from plugin ownership instead of derived from a declared audit assertion or linked verification path.

**Settlement condition:** a spec assertion under the owning Product Tree node names the refocus skill surface and routes its activation and workflow contract to current evidence.

## DEBT [duplication]: two harnesses each derive the traceback header

Evidence: at head 1e709fbcdcf3d6f793730e4f394d2b48e91e4bbe, `outcomeeng_testing/harnesses/instruction_block.py` and `outcomeeng_testing/harnesses/reviewing_changes.py` each define the same `_standard_traceback_header` function and bind its result to `TRACEBACK_HEADER`. The agent-token load tests of `spx/21-product-tree.enabler/43-instruction-block.enabler` and `spx/21-product-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler` read it to show that a load failure prints no traceback. Both copies came with https://github.com/outcomeeng/plugins/pull/694.

Impact: one observation has two homes, so a change to how the header is derived edits two harnesses.

Settlement condition: one harness module both nodes import, such as `outcomeeng_testing/harnesses/agent_tokens.py`, owns the traceback header, and neither node's harness defines its own copy.

## The one-spec-per-node Conformance Assertion names no contract file

Evidence: at `f83f39569`, `product-tree.md` (lines 33 to 35) declares `one-spec-per-node` under `### Conformance` and links `tests/test_product_tree.conformance.l1.py`. That test checks that every node directory holds its slug spec file, through `outcomeeng.product_tree_structure.node_spec_file`, and reads no contract file. The Node holds no `contracts/` directory. A Conformance Assertion checks one Node's output against a contract a file defines, and the Node that owns that contract keeps the file in its `contracts/` directory, where the Assertion links it.

Impact: the row's type promises validation against a contract that no file states, so no reader or Verifier can check the test against a contract, and the Assertion's type does not match its Evidence.

Settlement condition: the Node keeps the contract file in its `contracts/` directory and the row links it, or the row is retyped and its test carries the type of its new heading.

## DEBT [consistency]: understand's Change summary omits the decision to work `src/plugins/product-tree/skills/understand/SKILL.md` `change-summary` `consistency`

Evidence: at head 47d39419b1b9c6732f2e13e12e6e9168f46644cb of https://github.com/outcomeeng/plugins/pull/810, line 356 of `src/plugins/product-tree/skills/understand/SKILL.md` lists the Lifecycle values and says that `/manage-change` makes every Transition. It does not say that recording a decision to work on a Submitted Change returns it to `Available` without a Transition, or that an advance takes an Available Change, as the `lifecycle`, `submit` and `advance` rows of `spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md` state.

Impact: a reader who learns the Change model from the foundation does not learn that a Change stays `Available` while it waits for an advance, or that manage-change records the decision to work with `work`.

Settlement condition: the Change summary of the foundation states the decision to work and the advance from an Available Change, as the change-record PDR states them.
