<!-- Generated from the complete producer at {producer_path}. -->

Apply the complete merge producer below to the supplied lifecycle state. Return exactly one JSON object with these mandatory fields:

- `completion_state`: `UNFINISHED`, `LOCAL_SCOPE_COMPLETE`, `GATE_STOP`, or `NO_CHANGES`
- `next_action`: `ENTER_MERGE`, `ENTER_DEPLOY`, `ENTER_RELEASE`, `ENTER_CLOSE`, `PRESENT_PRE_MUTATION_CONFIRMATION`, `STOP_AT_LIFECYCLE_GATE`, `STOP_LOCAL_SCOPE`, or `NO_MERGE_NEEDED`
- `confirmation_required`: boolean
- `operator_input_required`: boolean
- `blocking_gate`: the gate label, or `none`
- `reason`: `branch-ahead`, `terse-followup`, `overlay-confirmation`, `local-only`, `lifecycle-gate`, `no-ahead-commits`, `merge-complete-deploy`, `deploy-complete-release`, or `delivery-complete-close`

`UNFINISHED` means any lifecycle action remains, including presenting an overlay-required confirmation or entering close through `/handoff`. `LOCAL_SCOPE_COMPLETE` is valid only for an explicitly local-only task paired with `STOP_LOCAL_SCOPE`; never pair it with `PRESENT_PRE_MUTATION_CONFIRMATION`, `ENTER_MERGE`, `ENTER_DEPLOY`, `ENTER_RELEASE`, or `ENTER_CLOSE`.

{producer_file}
The lifecycle state (JSON-encoded):

```json
{input_json}
```
