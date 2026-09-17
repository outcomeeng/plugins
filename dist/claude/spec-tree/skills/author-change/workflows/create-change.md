<required_reading>

Load `spec-tree:change-standards` through skill composition and read `${CLAUDE_SKILL_DIR}/templates/change.md`. Apply the store configuration resolved by the authoring router.

</required_reading>

<process>

1. Apply the router's `<triage>` to the request and relevant repository facts. Resolve the owning Product and intended Output; help formulate an Output when only a problem is supplied. An explicit request to produce a clear Output establishes the operator's choice to pursue it; do not require a separate prioritization interview. Inspect matching open Changes in the configured store to avoid duplicates. If the same Change already exists, use the revision workflow with its exact reference.
2. Follow the selected refinement route. Draft directly when consequential choices are resolved. Invoke `/interview` only for unresolved operator-owned choices, with the plain-text question and answer rules from `<triage>`. Pause for an operator choice when prioritization or whether to pursue the proposed Output remains unresolved.
3. Compose metadata and body from the template using the shared maturity requirements, with `refined_from: []` for the root. Preserve a selected working file or create one through the router's `<local_draft>` procedure. Record only established content. If refinement stops at Proposed, keep remaining questions visible and omit the Intent attestation line. Before authoring Framed, present the complete Frame to the operator; only after approval, write `Intent attestation: attested by the operator on <date>.` and omit Input. Continue to Sliced and Executable only as their requirements become true.
4. Establish publication authority and resolve the configured native metadata mapping without creating an issue or project item. A new local draft has no store claim. All interviews, drafting, and repair continue in the local file.
5. Return the stabilized local file to the router's shared audit gate. A gate failure preserves that file for correction and withholds publication. After approval, use the router's publication procedure to create the Change and its configured project item once, capture the returned canonical reference, and read the result back. Establish any subsequent Refiner claim through the configured ownership mechanism; never assert a claim that the store has not confirmed.
6. After approval and confirmed publication, return the Change reference and its truthful state. Continue refinement when requested and possible. When the holder stops or delegates, route through `/handoff` for transient continuation and release.

</process>

<success_criteria>

- Exactly one new Change represents the intended Output in the correct Product and store.
- Published content and native fields match the inspected candidate and its established maturity.
- Open questions remain explicit; operator attestation is available for Framed or higher maturity.
- A clear, fully resolved request requires no refinement interview; remaining questions correspond to actual unresolved choices.
- The router's independent audit gate approves the complete local candidate before the first publication; a rejected or blocked candidate remains local.

</success_criteria>
