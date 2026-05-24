<!-- Prompt template for the local-review-gate eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies the gate's decision logic, given
     a review-result.json input. The case file supplies the JSON; the
     model decides STOP or PROCEED by applying the skill prose at
     plugins/spec-tree/skills/opening-pr/SKILL.md Step 3. The gate's
     upstream behavior (the reviewer itself) has its own evals under
     spx/21-spec-tree.enabler/32-evidence.enabler/21-verification.enabler/
     32-reviewing-changes.enabler/evals/. -->

You are simulating the operator agent that runs `/opening-pr`'s Step 3 (local review gate). The agent has just invoked the `changes-reviewer` agent (or the `/review-changes` slash command) on the working diff, and the resulting `review-result.json` is provided below.

The skill's acceptance criterion (the rule under audit in this eval) is severity-based, not decision-based. The `decision` field is bound to `blocking` presence alone: `request_changes` only when at least one `blocking` finding is present; `approve` and `comment` both fire when no `blocking` finding is present, including when `debt` findings exist. A decision-based check would let `debt`-only results through; the severity-based check does not.

Apply the rule:

- Any finding with `severity == "blocking"` or `severity == "debt"` in `review-result.json` → STOP. The operator must fix the findings before pushing.
- Findings with `severity == "follow_up"` → the operator fixes the ones whose remediation stays within the PR's scope, defers only the widening-scope ones with an ISSUES.md note. The gate authorizes the push for follow-up-only results (the deferral judgment is operator scope, not gate scope).
- `findings` array contains no `blocking` and no `debt` entry → PROCEED (push authorized). The `decision` field's value is informational.

Case id: substituted by the harness.

The `review-result.json` input the gate is evaluating:

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — in this exact shape:

```
{
  "gate_decision": "STOP" | "PROCEED",
  "reason_severity": "blocking" | "debt" | "follow_up" | "none"
}
```

`gate_decision` reports the gate's authorization: `STOP` blocks the push and signals the operator must fix findings; `PROCEED` authorizes the push. `reason_severity` reports which severity drove the decision: `blocking` or `debt` when the gate stops; `follow_up` or `none` when the gate proceeds. The grader checks both fields together — `STOP` paired with `blocking` is correct when the input has a blocking finding; `STOP` paired with `none` is not, because the gate would not stop without a triggering severity. The coupling ensures the model identifies WHICH severity drove the decision rather than just guessing STOP/PROCEED.
