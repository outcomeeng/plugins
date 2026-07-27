<required_reading>

Read `/skill-standards` and `/agent-prompt-standards` before evaluating or improving skill content. Read `spx/local/skills.md` when the target repository provides it.

</required_reading>

<process>

<step name="resolve_target">

Use the target path supplied by the operator. When no path is supplied, ask for the exact `SKILL.md` or skill-directory path; never assume a runtime-specific home directory.

Resolve the target to its `SKILL.md` plus every file recursively present under `references/`, `workflows/`, `templates/`, `assets/`, and `scripts/`, including uncited and orphaned bundled files.

</step>

<step name="dispatch_audit">

Dispatch the typed `skill-auditor` role with the repository path, every target skill-content path, governing node paths when known, and deterministic verification already run. If the role is unavailable or returns no complete structured JSON verdict, return `BLOCKED`; never substitute an in-context `/audit-skill` invocation. Preserve a completed structured verdict unchanged.

The audit is read-only: never edit files, assign a numeric score, ask the auditor to produce fixes, or append an unsolicited fix offer. For an audit-only request, return the verdict and stop. For an explicit improvement request, preserve the verdict as repair input and continue.

</step>

<step name="complete_name_review">

For every explicit improvement request, complete the router's `<material_change_name_review>` before applying any change. Audit-only requests remain read-only and skip the mutation gate.

</step>

<step name="apply_requested_improvements">

For an explicit improvement request, map every accepted finding to its governing rule, identify every same-class instance in the complete bundle, resolve the exact authored paths, and settle every operator-owned decision that changes behavior. Before changing behavior, load `${CLAUDE_SKILL_DIR}/references/test-patterns.md`. Load `${CLAUDE_SKILL_DIR}/references/reusability-patterns.md` when the repair changes variable inputs, clarification, abstraction level, or tool choice. Load `${CLAUDE_SKILL_DIR}/references/technical-patterns.md` when the repair touches files, data, external services, state mutation, or executable automation.

Apply every must-fix item and every explicitly requested improvement through the authoring rules loaded by `/create-skill`. Preserve unaffected content and keep standards in `/skill-standards` rather than copying them into the target skill.

</step>

<step name="validate_and_reaudit">

For an explicit improvement request, confirm every accepted finding and same-class instance is repaired, the complete bundle passes the applicable `/skill-standards` and `/agent-prompt-standards` checks, every bundled citation resolves, and focused checks for the changed behavior pass. Run the target repository's canonical skill build and deterministic checks. Create a clean checkpoint after those checks pass and repeat the same audit route over the new head. Continue until the verdict is `APPROVED` or a concrete blocker remains.

</step>

</process>

<audit_anti_patterns>

| Anti-pattern          | Rejected behavior                                                                                          |
| --------------------- | ---------------------------------------------------------------------------------------------------------- |
| Ad hoc audit          | Evaluating the skill without the typed `skill-auditor` or invoking `/audit-skill` in the authoring context |
| Runtime-specific path | Assuming a home-directory skill location instead of using the supplied or repository path                  |
| Scored report         | Replacing the structured verdict with a numeric score                                                      |
| Automatic fix offer   | Soliciting mutations after an audit-only request                                                           |
| Lexical batch rename  | Renaming unlike skill types because their names share a token, suffix, or grammatical form                 |
| Restated standards    | Copying `/skill-standards` rules into this workflow                                                        |

</audit_anti_patterns>

<success_criteria>

- An audit-only request returns the unchanged structured verdict over the complete target bundle and performs no mutation.
- An explicit improvement request produces content that passes deterministic checks and a fresh `APPROVED` verdict from the typed `skill-auditor`.
- Every proposed rename has a complete classification row grounded in the declared naming form, vocabulary source, and relevant history.
- Target resolution remains runtime-neutral, and `/skill-standards` remains the single rule source.

</success_criteria>
