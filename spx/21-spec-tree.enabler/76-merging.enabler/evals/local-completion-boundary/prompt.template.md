<!-- Generated from the ordered complete merge producers. -->

Apply the complete merge producers below to the supplied lifecycle state. Derive every classification and action sequence exclusively from those producers. Return exactly one JSON object with these mandatory fields:

- `lifecycle_disposition`: `ADVANCE` when `ordered_actions` is nonempty, or `STOP` when `ordered_actions` is empty
- `next_action`: `INVOKE_MANAGE_GITHUB_PR`, `DRIVE_DIRECT_PUSH`, `RUN_DEPLOY`, `RUN_RELEASE`, `ENTER_CLOSE`, `PRESENT_PRE_MUTATION_CONFIRMATION`, `STOP_AT_LIFECYCLE_GATE`, `STOP_LOCAL_SCOPE`, or `NO_MERGE_NEEDED`
- `operator_input_required`: boolean
- `blocking_gate`: the gate label, or `none`
- `ordered_actions`: an object whose numeric string keys (`1`, `2`, ...) preserve the required action order and whose values use the `next_action` vocabulary; use an empty object when no action remains

{producer_files}
The lifecycle state (JSON-encoded):

```json
{input_json}
```
