<required_reading>

Load `spec-tree:change-standards` through skill composition and read `${CLAUDE_SKILL_DIR}/templates/change.md`. Apply the store configuration resolved by the authoring router.

</required_reading>

<process>

1. Resolve the intended Output and owning Product from the request. Confirm that discovery has prioritized this Output for refinement; ask only when that intent is absent. Inspect matching open Changes in the configured store to avoid duplicates. If the same Change already exists, use the revision workflow with its exact reference.
2. Invoke `/interview`. Reuse explicit answers already given and inspect the repository facts needed for the remaining questions. Ask questions in plain text, one at a time, with enough explanation to make the decision understandable. Wait for each answer. The operator determines Output and consequential choices; no response supplies no decision.
3. Draft the body from the template using the maturity requirements in the shared standards. Record only established content. If refinement stops at Proposed, keep remaining questions visible. Before recording Framed, obtain the operator's attestation of the complete Frame and omit Input. Continue to Sliced and Executable only as their requirements become true.
4. Establish authority for the new Change and its native metadata. Create one issue at Proposed maturity in the configured store, capture the returned canonical reference, and add its project item and resolved field values. Establish the Refiner's claim through the configured ownership mechanism before advancing refinement; never assert a claim that the store has not confirmed. Read back the issue and metadata after creation. A partial publication resumes against that reference; never retry creation blindly.
5. Return the stabilized candidate to the router's shared audit gate. Keep the requested maturity advancement pending until the candidate has the required operator attestation and independent approval. A gate failure preserves the candidate for correction and withholds advancement.
6. After approval and confirmed publication, return the Change reference and its truthful state. Continue refinement when requested and possible. When the holder stops or delegates, route through `/handoff` for transient continuation and release.

</process>

<success_criteria>

- Exactly one new Change represents the intended Output in the correct Product and store.
- Published content and native fields match the inspected candidate and its established maturity.
- Open questions remain explicit; operator attestation is available for Framed or higher maturity.
- The router's independent audit gate approves the current candidate before advancement is reported complete.

</success_criteria>
