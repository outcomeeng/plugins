<required_reading>

Load `spec-tree:change-standards` through skill composition and read `${CLAUDE_SKILL_DIR}/templates/change.md`. Apply the store configuration resolved by the authoring router.

</required_reading>

<process>

1. Resolve exactly one existing Change. Read its current body, native Product/Maturity/Lifecycle fields, current holder, necessary predecessor and blocker records, and latest Handoff when resuming work. Check relevant repository references through normal context gates. Never reload an entire conversation to recover a fact the Change already supplies.
2. Establish authority to revise. A claim held by another holder prevents takeover by assumption. Terminal Lifecycle prevents ordinary resumption; report the state and the need for a new Change or an authorized lineage operation. Splitting and combining are outside this prototype.
3. Compare the requested revision with the current Output, Frame, relationships, and Activities. Invoke `/interview` for the Change's unresolved questions, reusing explicit prior answers. Ask in plain text and wait. A change to prioritization or why the Output is worth producing returns to discovery before further refinement.
4. Determine whether the current maturity remains truthful. When lowering a Claimed Change's maturity is required, invoke `/handoff` to preserve continuation and release it, then stop this invocation. Continue revision only under renewed authority. Otherwise update every affected section together and preserve unchanged intent and immutable lineage.
5. Apply the template's maturity conditions to the revised body. Remove Input when recording Framed or higher maturity. Keep meaningful pending work in Activities, transient continuation in Handoff, and verification records in SPX. Never append a transcript or a second competing plan to the record.
6. Re-read the remote body and native metadata immediately before publication. If they changed since inspection, reconcile the revision with the current record; ask when the edits conflict in intent. Update the selected issue and native project fields through the router's publication procedure, then read both back. Preserve the canonical reference.
7. Return the stabilized candidate to the router's shared audit gate. Sweep the entire record for every revealed defect class, batch corrections, and re-audit. Record a maturity advancement only after its content, operator authority, and independent audit requirements hold.
8. Return the updated Change reference, truthful state, and next Activity. Invoke `/handoff` when refinement stops or transfers to another holder.

</process>

<success_criteria>

- The same Change identity and immutable lineage are preserved.
- Every section affected by the revision agrees with the current Output and repository truth.
- Maturity and Lifecycle remain distinct and truthful, with Input absent from Framed onward.
- Concurrent edits are reconciled before publication, and the published candidate has independent approval.
- A fresh holder can locate the next Activity and all settled intent without the prior conversation.

</success_criteria>
