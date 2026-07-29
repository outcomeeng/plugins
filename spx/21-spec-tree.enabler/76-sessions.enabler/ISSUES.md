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
