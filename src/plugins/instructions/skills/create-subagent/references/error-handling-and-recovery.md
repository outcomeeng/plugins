<failure_boundary>

Classify the observed failure before proposing a correction:

| Boundary      | Evidence to retain                                           |
| ------------- | ------------------------------------------------------------ |
| Configuration | Exact native definition and loader diagnostic                |
| Discovery     | Expected configured role and the harness's observed registry |
| Launch        | One native call's arguments and actual return                |
| Execution     | Returned progress, tool failure, or stopped task             |
| Result        | Actual final response and the required result contract       |

</failure_boundary>

<diagnosis>

1. Preserve the actual result and exact target.
2. Compare the configured artifact with its governing profile and native schema.
3. Check installation ownership and whether the running session loaded the installed revision.
4. Identify the first failing boundary and the evidence supporting that conclusion.
5. Report the failed action, consequence, and required correction to the invoking conversation.

Apply the one-call failure policy in `/subagent-standards`. Diagnosis does not authorize
another launch, a substitute role, a model override, or an alternative launch mechanism.

</diagnosis>

<valid_rejection>

A usable rejected audit is evidence about its subject. Follow the owning skill's
finding disposition and repair workflow: preserve the rejected subject and verdict,
produce the corrected subject under that workflow, and obtain fresh verification when
it requires it. Keep this separate from a launch failure or an unusable result.

</valid_rejection>

<operator_decision>

When evidence leaves a product decision unresolved, return the missing decision,
the exact blocked action, and observations that distinguish the available choices.
The invoking conversation resolves the decision. A missing answer supplies no approval.

</operator_decision>
