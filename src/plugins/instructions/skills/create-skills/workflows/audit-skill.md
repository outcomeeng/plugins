<required_reading>

Read `/skill-standards` and `/agent-prompt-standards` before evaluating or improving skill content. Read `spx/local/skills.md` when the target repository provides it.

</required_reading>

<process>

<step name="resolve_target">

Use the target path supplied by the caller. When no path is supplied, ask for the exact `SKILL.md` or skill-directory path; never assume a runtime-specific home directory.

Read the target `SKILL.md` and every bundled file under its `references/`, `workflows/`, `templates/`, and `scripts/` directories.

</step>

<step name="dispatch_audit">

Check whether the runtime exposes the `skill-auditor` role. When it does, dispatch `skill-auditor` with the target paths, governing nodes when known, and current deterministic verification evidence. When it does not, invoke `/audit-skills` over the same complete target bundle and use that verdict; absence of the optional typed role does not block authoring.

For an audit-only request, return the auditor's structured verdict without offering or generating fixes. For an explicit improvement request, use the verdict as the repair input and continue to the next step.

</step>

<step name="apply_requested_improvements">

Apply every must-fix item and any explicitly requested recommendation through `/create-skills`. Preserve unaffected content and keep standards in `/skill-standards` rather than copying them into the target skill.

After repairs, run the bundled validator, identify the product's skill build and deterministic-check commands for the caller's repository workflow, create a clean checkpoint after those checks report success, and dispatch a fresh `skill-auditor` over the new head. Repeat until the verdict is APPROVED or a concrete blocker remains.

</step>

</process>

<audit_anti_patterns>

| Anti-pattern          | Rejected behavior                                                                    |
| --------------------- | ------------------------------------------------------------------------------------ |
| Ad hoc audit          | Evaluating the skill without the exposed `skill-auditor` or `/audit-skills` fallback |
| Runtime-specific path | Assuming a home-directory skill location instead of using the target path            |
| Scored report         | Replacing the structured verdict with a numeric score                                |
| Automatic fix offer   | Soliciting fixes after an audit-only request                                         |
| Restated standards    | Copying `/skill-standards` rules into this workflow                                  |

</audit_anti_patterns>

<success_criteria>

- An audit-only request returns the exposed skill-auditor verdict or `/audit-skills` fallback verdict over the complete target bundle.
- An explicit improvement request produces skill content that passes deterministic checks and a fresh skill audit.
- Target resolution remains runtime-neutral, and `/skill-standards` remains the single rule source.

</success_criteria>
