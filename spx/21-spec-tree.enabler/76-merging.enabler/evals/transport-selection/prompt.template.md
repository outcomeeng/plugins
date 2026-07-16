<!-- Generated from the ordered complete merge producers. -->

Apply the complete merge producers below to the supplied changeset classification and overlay state. Return exactly one JSON object with these mandatory fields:

- `selected_transport`: `GITHUB_PR` or `DIRECT_PUSH`
- `selection_reason`: `overlay-selector`, `coordination-note-only`, or `default`
- `delegation_target`: `manage-github-pr` or `direct-push-lifecycle`
- `pre_mutation_action`: `PRESENT_CONFIRMATION` or `PROCEED_AUTONOMOUSLY`

{producer_files}
The changeset and overlay state (JSON-encoded):

```json
{input_json}
```
