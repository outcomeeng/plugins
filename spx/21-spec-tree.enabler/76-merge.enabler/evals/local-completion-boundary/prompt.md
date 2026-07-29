<!-- Prompt template for the local-completion-boundary eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies the transport-neutral completion
     boundary from spx/15-merging.pdr.md. A locally verified changeset
     ahead of its resolved base is unfinished until it reaches the
     default branch on origin through /merge, or until an explicit
     lifecycle gate stops with no independent local action remaining. -->

You are simulating Claude's status assessment after local readiness evidence has been collected for a changeset.

For work destined for the repository's default branch:

- delivered value exists only after the changeset reaches the default branch on origin through `/merge`;
- a branch with committed changes ahead of its resolved base is unfinished even when the working tree is clean and validation, tests, local review, or audits have passed;
- local readiness evidence is reported, then carried into `/merge` unless the user explicitly limited the task to proposal, review, analysis, or local-only work;
- do not ask what to do next after local readiness is established;
- do not ask for confirmation before entering `/merge` unless the merge overlay explicitly opted into pre-mutation confirmation;
- terse follow-ups such as "so?", "continue", "ship it", "finish", and "go on" mean continue the already-governed merge lifecycle;
- `/merge` classifies the changeset, selects the merge transport, and either ships it to the default branch on origin or stops at an explicit merge lifecycle gate or structured stop report.

Case id: substituted by the harness.

The status input (JSON-encoded):

```json
{input_json}
```

Verdict schema — six fields, all mandatory:

- `completion_state`: `"UNFINISHED"`, `"LOCAL_SCOPE_COMPLETE"`, `"GATE_STOP"`, or `"NO_CHANGES"`.
- `next_action`: `"ENTER_MERGE"`, `"PRESENT_PRE_MUTATION_CONFIRMATION"`, `"STOP_AT_LIFECYCLE_GATE"`, `"STOP_LOCAL_SCOPE"`, or `"NO_MERGE_NEEDED"`.
- `confirmation_required`: boolean; true only when the merge overlay explicitly opted into pre-mutation confirmation.
- `operator_input_required`: boolean; true only when an explicit lifecycle gate requires operator input before any further independent local action exists.
- `blocking_gate`: the lifecycle gate label when `next_action` is `"STOP_AT_LIFECYCLE_GATE"`, otherwise `"none"`.
- `reason`: `"branch-ahead"`, `"terse-followup"`, `"overlay-confirmation"`, `"local-only"`, `"lifecycle-gate"`, or `"no-ahead-commits"`.

Decision rules:

1. If `task_scope` is `"local_only"`, local scope is complete and Claude stops locally without entering `/merge`.
2. Else, if `branch_ahead_of_resolved_base` is `0`, no merge lifecycle is needed.
3. Else, if `explicit_lifecycle_gate` is not null, stop at that gate and require operator input.
4. Else, if `overlay_pre_mutation_confirmation` is true, present the pre-mutation confirmation before the first mutation.
5. Else, if `user_followup` is one of the terse continuation phrases, continue the lifecycle and report reason `"terse-followup"`.
6. Else, continue by entering `/merge` and report reason `"branch-ahead"`.

Return only a parseable JSON document matching the schema.
