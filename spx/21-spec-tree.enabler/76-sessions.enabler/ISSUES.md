# Issues: Sessions

## 1. Claim-verification extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/pickup/scripts/verify_session_claims.py` runs to several hundred lines, an order of magnitude past the fifty-line threshold — reconciliation of a handoff session's recorded claims against current repository state, resolving each claim to exactly one verdict (`Confirmed`, `Discrepancy`, `Unverifiable`) and emitting the verdicts as JSON for `/pickup` to render. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; the verifier has proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product, and the plugins product may depend on the resulting capability only once it is published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts the fix outside any changeset confined to this repository. The session store this script reconciles against is already SPX-owned, so the port moves claim verification beside the state it reads.

**Resolution shape**: port claim reconciliation and the three-verdict resolution into the SPX CLI beside `spx session`, publish it, advance the floor, and reduce the shipped skill to its instruction with no script. Preserve the total verdict mapping across the move — every recorded claim resolves to exactly one verdict, and an unverifiable check stays distinguishable from a discrepancy. The port also carries the node-status lookup, which resolves the target node's record by tree-relative id inside the projection's node tree; a CLI-side implementation reads that record directly rather than re-deriving it from the CLI's own JSON output. Revisit when the capability publishes.

## 2. This node's spec still carries the handoff and pickup-resumption concerns

`sessions.md` holds 36 assertions after the first composition pass, against the roughly seven that `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md` treats as the signal requiring decomposition analysis.

The remaining concerns, their reserved child addresses, the ordering evidence placing them, and the destination of every one of the 36 assertions are recorded in `spx/21-spec-tree.enabler/76-sessions.enabler/PLAN.md`. That note carries the pending steps; this entry records only that the node is mid-composition, so a reader who loads the node knows its spec is not yet at its resting shape.

**Evidence**: the oversize was surfaced by the changeset reviewer on PR 494 (run `2026-07-28_18-06-07-731-0251e1d43e02`) as an `[architecture]` `DEBT` finding. The first composition pass moved 24 assertions into `spx/21-spec-tree.enabler/76-sessions.enabler/15-session-store.enabler` and `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler/30-claim-verification.enabler`.
