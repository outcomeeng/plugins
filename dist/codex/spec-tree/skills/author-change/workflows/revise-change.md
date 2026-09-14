<required_reading>

Load `spec-tree:change-standards` through skill composition and read `${SKILL_DIR}/templates/change.md`. Apply the store configuration resolved by the authoring router.

</required_reading>

<process>

1. Resolve exactly one existing Change. Read its current body, native Product/Maturity/Lifecycle fields, current holder, necessary predecessor and blocker records, and latest Handoff when resuming work. Check relevant repository references through normal context gates. Never reload an entire conversation to recover a fact the Change already supplies.
2. Establish authority to revise. A claim held by another holder prevents takeover by assumption. Terminal Lifecycle prevents ordinary resumption; report the state and the need for a new Change or an authorized lineage operation. Splitting and combining are outside this prototype. Resolve the local working-file path through the router, and import the body and metadata into that file once. Preserve an existing local candidate and reconcile its relationship to the remote version before replacing any content. Retain the inspected remote version for the publication concurrency check outside the Change body.
3. Compare the requested revision with the current Output, Frame, relationships, and Activities. Apply the router's `<triage>` to the delta, preserving resolved choices. Revise directly when the request and governing references settle the change. Invoke `/interview` only for consequential choices that remain unresolved. A revision that requires a new prioritization or pursuit decision pauses for the operator through discovery; a wording correction to Value alone does not require that decision.
4. Determine whether the current maturity remains truthful. When lowering a Claimed Change's maturity is required, invoke `/handoff` to preserve continuation and release it, then stop this invocation. Continue revision only under renewed authority. Otherwise update every affected section together and preserve unchanged intent and immutable lineage.
5. Apply the template's maturity conditions to the local metadata and body. Remove Input when authoring Framed or higher maturity. Keep meaningful pending work in Activities, transient continuation in Handoff, and verification records in SPX. Never append a transcript or a second competing plan to the record.
6. Return the stabilized local file to the router's shared audit gate. Sweep the entire record for every revealed defect class, batch local corrections, and re-audit. Leave the remote content and maturity unchanged until the local candidate has approval.
7. After approval, use the router's publication procedure, including its concurrency and authority checks. Reconcile intervening remote edits locally; ask when they conflict in intent and re-audit a changed candidate. Publish the approved body and metadata, read both back, and preserve the canonical reference.
8. Return the updated Change reference, truthful state, and next Activity. Invoke `/handoff` when refinement stops or transfers to another holder.

</process>

<success_criteria>

- The same Change identity and immutable lineage are preserved.
- Every section affected by the revision agrees with the current Output and repository truth.
- Maturity and Lifecycle remain distinct and truthful, with Input absent from Framed onward.
- Concurrent edits are reconciled before publication, and the published candidate has independent approval.
- A fresh holder can locate the next Activity and all settled intent without the prior conversation.
- Refinement questions address unresolved choices introduced or exposed by the revision; unchanged intent is preserved without another interview.

</success_criteria>
