# Issues: Sessions

## 1. Claim-verification extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/pickup/scripts/verify_session_claims.py` runs to several hundred lines, an order of magnitude past the fifty-line threshold — reconciliation of a handoff session's recorded claims against current repository state, resolving each claim to exactly one verdict (`Confirmed`, `Discrepancy`, `Unverifiable`) and emitting the verdicts as JSON for `/pickup` to render. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; the verifier has proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product, and the plugins product may depend on the resulting capability only once it is published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts the fix outside any changeset confined to this repository. The session store this script reconciles against is already SPX-owned, so the port moves claim verification beside the state it reads.

**Resolution shape**: port claim reconciliation and the three-verdict resolution into the SPX CLI beside `spx session`, publish it, advance the floor, and reduce the shipped skill to its instruction with no script. Preserve the total verdict mapping across the move — every recorded claim resolves to exactly one verdict, and an unverifiable check stays distinguishable from a discrepancy. The port also carries the node-status lookup, which resolves the target node's record by tree-relative id inside the projection's node tree; a CLI-side implementation reads that record directly rather than re-deriving it from the CLI's own JSON output. Revisit when the capability publishes.

## 2. The node carries sixty assertions against a seven-assertion decomposition signal

`sessions.md` holds 47 Compliance assertions, 11 Scenarios, and 2 Mappings. `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md` treats more than roughly seven assertions as a signal requiring decomposition analysis, so a node at sixty is far past the point where that analysis is owed.

The Compliance section spans several independently governable concerns that each have their own validation boundary: handoff persistence and the session-file lifecycle, claimed-session and continuation-thread resolution, pickup claim verification, and closeout reporting. Each could anchor its own child enabler.

**Why this is not folded into the changeset that surfaced it**: the resolution is `/decompose` analysis followed by `/refactor` tree surgery across the node, its two existing children, its co-located tests, and every full-path citation that names it — node-scale structural work whose ordering evidence and index assignment `/decompose` owns. The changeset that surfaced this adds one assertion governing closeout content; the oversize predates it and is independent of that concern, so folding the restructure in would replace a bounded content change with a subtree migration.

**Resolution shape**: run `/decompose spx/21-spec-tree.enabler/76-sessions.enabler` to produce the ordering-evidence matrix and child boundaries, then apply the split through `/refactor`, preserving assertion semantics and moving each assertion to the child whose concern owns it. Gate with the spec auditor per child.

**Evidence**: surfaced by the changeset reviewer on PR 494 (run `2026-07-28_18-06-07-731-0251e1d43e02`) as a `[architecture]` `DEBT` finding against `sessions.md:76`.
