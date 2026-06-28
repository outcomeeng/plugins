<!-- Prompt template for the post-merge-verification eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies /manage-pr's post-merge behavior after
     MERGE_READINESS and PRODUCTION_READINESS have authorized the merge and
     merge cleanup has completed. -->

Use the installed `/manage-pr` skill from the active spec-tree plugin as the producer for this eval. Classify the synthetic post-merge state below according to that skill and the methodology it loads. Do not answer from a copied rule table in this prompt; the prompt intentionally provides only the case state and the output schema.

The state represents the point immediately after a pull request has merged and the branch cleanup sequence has completed. External state has already been gathered for the case; do not run tools or inspect a real repository.

Case id: substituted by the harness.

The post-merge input (JSON-encoded):

```json
{input_json}
```

Verdict schema — six fields, all mandatory:

- `post_merge_state`: `"RUN_AUTONOMOUS_POST_MERGE"`, `"NO_POST_MERGE_REQUIRED"`, `"OPERATOR_BOUNDARY"`, or `"COMPLETE_AFTER_CHECKOUT_REFRESH"`.
- `source_checkout_action`: `"FAST_FORWARD_CONFIRMED"` or `"NONE"`.
- `install_refresh_action`: `"RUN_SYNC_MARKETPLACE"`, `"NONE"`, or `"SKIP"`.
- `install_refresh_working_directory`: `"source_checkout"` or `"none"`.
- `terminal_token`: `"none"` or `"POST_MERGE_VERIFY"`.
- `reason`: `"overlay-post-merge-command"`, `"overlay-silent"`, or `"operator-owned-post-merge"`.

Return only a parseable JSON document matching the schema.
