# Issues: Sessions

## 1. Claim-verification extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/pickup/scripts/verify_session_claims.py` runs to several hundred lines, an order of magnitude past the fifty-line threshold — reconciliation of a handoff session's recorded claims against current repository state, resolving each claim to exactly one verdict (`Confirmed`, `Discrepancy`, `Unverifiable`) and emitting the verdicts as JSON for `/pickup` to render. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; the verifier has proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product, and the plugins product may depend on the resulting capability only once it is published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts the fix outside any changeset confined to this repository. The session store this script reconciles against is already SPX-owned, so the port moves claim verification beside the state it reads.

**Resolution shape**: port claim reconciliation and the three-verdict resolution into the SPX CLI beside `spx session`, publish it, advance the floor, and reduce the shipped skill to its instruction with no script. Preserve the total verdict mapping across the move — every recorded claim resolves to exactly one verdict, and an unverifiable check stays distinguishable from a discrepancy. The port also carries the node-status lookup, which resolves the target node's record by tree-relative id inside the projection's node tree; a CLI-side implementation reads that record directly rather than re-deriving it from the CLI's own JSON output. Revisit when the capability publishes.

## 2. The foundation-marker exemption is stated twice

`spx/21-spec-tree.enabler/76-sessions.enabler/15-session-store.enabler/session-store.md` asserts that an operator's explicit `spx session` request runs as operational-state management without a live `SPEC_TREE_FOUNDATION` marker. `spx/21-spec-tree.enabler/18-context-loading.enabler/context-loading.md` asserts the same exemption over a wider command set — `spx session`, `spx worktree status`, `spx diagnose`, and no-patch Git status, history, and topology — with the same `[audit]` evidence mechanism.

Same content, same evidence mechanism, two nodes: duplication under `/understand` `<common_misplacements>`, which reserves specialization for a child rule that concretizes an ancestor rule against a narrower source surface. This one narrows nothing the wider rule does not already cover.

**Why this is not resolved in the changeset that surfaced it**: that changeset is a decomposition, and `spx/21-spec-tree.enabler/54-refactoring.enabler/refactoring.md` forbids changing assertion semantics during tree surgery. Deleting the assertion was attempted there and correctly rejected by the changeset review as an assertion dropped mid-refactor. Removing a declaration is a content change owing its own spec-audit justification, not a side effect of moving files.

**Resolution shape**: delete the assertion from `spx/21-spec-tree.enabler/76-sessions.enabler/15-session-store.enabler/session-store.md` in a changeset whose only subject is that removal, confirming first that `spx/21-spec-tree.enabler/18-context-loading.enabler` remains the declaring node and that no consumer loses the rule from its context.

## 3. The checkout-currency assertion cites a decision that does not state the rule

`spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler/pickup.md` asserts that `/pickup` brings the checkout current for every `git_ref` kind before presenting session detail, citing `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler/20-claim-verification.adr.md`. That decision covers the reconciliation script's mechanics — frontmatter sourcing, the injected runner, the verdict vocabulary, read-only-ness — and states no rule about bringing a checkout current or about `git_ref` kinds.

`spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md` does state it: "`/pickup` fetches and checks out the branch `git_ref` names ... reading in place when `git_ref` is the default branch or a commit SHA."

**Why this is not resolved in the changeset that surfaced it**: that changeset is a decomposition. `spx/21-spec-tree.enabler/54-refactoring.enabler/refactoring.md` forbids changing assertion semantics during tree surgery, and an assertion's governing-decision citation is part of its meaning. The corrected citation was written there and the changeset review rejected it as a semantic change mid-refactor, consistently with the same review rejecting a deleted assertion in the same changeset.

**Resolution shape**: repoint the citation to `spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md` in a changeset whose subject is that correction, confirming the decision still reaches this node from index 13.

## 4. The session-store node's first Scenario overclaims relative to its test

`spx/21-spec-tree.enabler/76-sessions.enabler/15-session-store.enabler/session-store.md` opens with a Scenario whose Given/When encodes the `/handoff` skill's own trigger judgment — that continuation is impossible, and that the skill ran without `--no-session`. Its linked test, `tests/test_sessions.scenario.l1.py`, drives the CLI directly with a generated payload: it constructs no continuation-impossible condition and never varies `--no-session` as a discriminating input. What the test establishes is narrower than what the assertion claims.

The trigger judgment itself is separately asserted in `spx/21-spec-tree.enabler/76-sessions.enabler/25-handoff.enabler/20-closure.enabler`, whose closure precondition owns exactly that decision, so restating it here also duplicates a rule the tree declares elsewhere.

**Why this is not resolved in the changeset that surfaced it**: that changeset is a decomposition. A narrowed Scenario was written there and the changeset review rejected it as an assertion whose subject changed mid-refactor, consistently with the same review rejecting a deleted assertion and a repointed citation in the same changeset. `spx/21-spec-tree.enabler/54-refactoring.enabler/refactoring.md` moves structure, not meaning.

**Resolution shape**: narrow the Scenario to the CLI behavior its test establishes — a payload naming tree state and an active node path yields a document in `.spx/sessions/todo/` carrying that path — in a changeset whose subject is that correction, confirming the closure precondition still carries the trigger judgment.

## 5. The handoff recovery paths state the reload gate unevenly

`src/plugins/spec-tree/skills/handoff/references/claimed-session-resolution.md` line 16 attaches the reload gate ("invoke `/understand`, then `/contextualize` on the governing node, only immediately before the recovery reads or edits coordination notes or other governed product content") to a recovery step that reads only conversation markers and `spx session` output, so the clause names a trigger that step never fires; `workflows/02-reflect.md` line 20 states the same gate without the word "only" the other three sites use; the reference's `<objective>` carries a second paragraph narrating workflow 04's use of the output; and `SKILL.md` `<failure_modes>` has no entry for reloading on every compaction-recovery entry.

**Resolution shape**: drop or forward-point the line-16 clause, align the 02-reflect wording, reduce the objective to its output sentence, and add the eager-reload failure mode — one editorial pass over the handoff skill gated by `instructions:skill-auditor`.

**Evidence.** Surfaced by the `skill-auditor` review of the handoff skill on the post-compaction reload-timing change (findings `unclear_conditional_trigger`, `phrasing_drift`, `objective_bloat`, `no_failure_modes`).

## 5. The `gh` untrusted-text rule is stated twice

`src/plugins/spec-tree/skills/pickup/workflows/change.md` and `src/plugins/spec-tree/skills/handoff/workflows/05-change.md` each carry the same paragraph on passing untrusted text to `gh` — bodies and comments on stdin as `--body-file -`, every other interpolated argument single-quoted with `'"'"'` for apostrophes, never a double-quoted argument, scratch file, or redirect built from such text. Two authored copies drift; the title-quoting defect the local review found had to be repaired in both.

**Resolution shape**: extract the rule into a `{domain}-standards` reference skill both workflows invoke, per the reference-skill pattern in the skill-authoring standards. A new skill is a structural plugin change with its own audit and a minor bump, so it does not belong to the changeset that introduced the Change workflows.

The same rule reaches `src/plugins/spec-tree/skills/open-pr/SKILL.md`, whose `gh pr create --title "…"` double-quotes an interpolated title; the extracted reference covers `--title` as well as `--body-file -`, and `open-pr` invokes it. The pull-request review of PR #535 (head `98b1ab9d114ab60f5da8ca11a6538c0fbd34f936`) surfaced that site as a DEBT finding; its fix changes a skill surface outside that changeset, so it is tracked here rather than carried there.

**Evidence.** The `skill-auditor` verdict on the pickup bundle at `41b304b691460afca90c7b92559123fdc3e6a3a1` names the duplication (`reference_skill_extraction_candidate`).

## 6. The Change-coordination mechanism has no decision record

The overlay contract declared in `spx/21-spec-tree.enabler/76-sessions.enabler/sessions.md`, `25-handoff.enabler/handoff.md`, and `28-pickup.enabler/pickup.md` — claim by assignee plus earliest `Claim:` comment, Maturity gating, the five-line Handoff comment, the authorized close comments, the secret inspection before every store write — is decided in the assertions and the two skill workflows, with no ADR or PDR under this node the way `13-handoff-persistence.adr.md` and `28-pickup.enabler/20-claim-verification.adr.md` decide their narrower mechanisms. The operator directed the GitHub realization to ship as a prototype without a PDR, following methodology 4.0.0 coordination (`versions/next/11-coordination.md` of `outcomeeng/methodology`) and its GitHub realization note directly.

**Resolution shape**: when the prototype graduates, author the decision under this node — a PDR when the Maturity and Lifecycle vocabulary is user-observable product behaviour, otherwise an ADR — and repoint the three overlay assertions at it; `/decompose` places it.

**Evidence.** The local review of `work/session-pointer-truth-derivation` at `488bd2e6c9c43d83d13c50b63029b903e2e03880` recorded the missing decision as a DEBT finding; the operator's prototype direction is the recorded reason it is tracked here rather than fixed in that changeset.
