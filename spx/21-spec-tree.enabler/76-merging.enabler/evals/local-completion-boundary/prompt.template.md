<!-- Generated from the complete producer at {producer_path}. -->

Apply the complete merge producer below to the supplied lifecycle state. Return exactly one JSON object with these mandatory fields:

- `completion_state`: `UNFINISHED`, `LOCAL_SCOPE_COMPLETE`, `GATE_STOP`, or `NO_CHANGES`
- `next_action`: `ENTER_MERGE`, `PRESENT_PRE_MUTATION_CONFIRMATION`, `STOP_AT_LIFECYCLE_GATE`, `STOP_LOCAL_SCOPE`, or `NO_MERGE_NEEDED`
- `confirmation_required`: boolean
- `operator_input_required`: boolean
- `blocking_gate`: the gate label, or `none`
- `reason`: `branch-ahead`, `terse-followup`, `overlay-confirmation`, `local-only`, `lifecycle-gate`, or `no-ahead-commits`

{producer_file}
The lifecycle state (JSON-encoded):

```json
{input_json}
```
