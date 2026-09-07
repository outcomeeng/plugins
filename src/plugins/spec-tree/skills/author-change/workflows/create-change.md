<required_reading>

Load `spec-tree:change-standards` through skill composition and read `${CLAUDE_SKILL_DIR}/templates/change.md`. Apply the store configuration resolved by the authoring router.

</required_reading>

<process>

1. Resolve the intended Output and owning Product from the request. Confirm that discovery has prioritized this Output for refinement; ask only when that intent is absent. Inspect matching open Changes in the configured store to avoid duplicates. If the same Change already exists, use the revision workflow with its exact reference.
2. Invoke `/interview`. Reuse explicit answers already given and inspect the repository facts needed for the remaining questions. Ask questions in plain text, one at a time, with enough explanation to make the decision understandable. Wait for each answer. The operator determines Output and consequential choices; no response supplies no decision.
3. Resolve the local working-file path through the router. Write metadata and body from the template using the shared maturity requirements. Record only established content. If refinement stops at Proposed, keep remaining questions visible. Before authoring Framed, obtain the operator's attestation of the complete Frame and omit Input. Continue to Sliced and Executable only as their requirements become true.
4. Establish publication authority and resolve the configured native metadata mapping without creating an issue or project item. A new local draft has no store claim. All interviews, drafting, and repair continue in the local file.
5. Return the stabilized local file to the router's shared audit gate. A gate failure preserves that file for correction and withholds publication. After approval, use the router's publication procedure to create the Change and its configured project item once, capture the returned canonical reference, and read the result back. Establish any subsequent Refiner claim through the configured ownership mechanism; never assert a claim that the store has not confirmed.
6. After approval and confirmed publication, return the Change reference and its truthful state. Continue refinement when requested and possible. When the holder stops or delegates, route through `/handoff` for transient continuation and release.

</process>

<success_criteria>

- Exactly one new Change represents the intended Output in the correct Product and store.
- Published content and native fields match the inspected candidate and its established maturity.
- Open questions remain explicit; operator attestation is available for Framed or higher maturity.
- The router's independent audit gate approves the complete local candidate before the first publication; a rejected or blocked candidate remains local.

</success_criteria>
