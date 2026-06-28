<!-- Prompt template for the post-merge-verification eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies /manage-pr's post-merge behavior after
     MERGE_READINESS and PRODUCTION_READINESS have authorized the merge and
     merge cleanup has completed. -->

You are simulating Claude running `/manage-pr` immediately after a pull request has merged and the branch cleanup sequence has completed.

Project overlays can declare post-merge commands. These commands are routine lifecycle work:

- run every autonomous post-merge command the overlay declares before reporting the managing pass complete;
- do not turn a runnable post-merge command into `POST_MERGE_VERIFY`;
- reserve `POST_MERGE_VERIFY` for a remaining post-merge action that is operator-owned, credential-blocked, or externally blocked after all autonomous commands have run;
- when the overlay declares a marketplace-source refresh, a refreshed source checkout is only prerequisite state. Run the install-refresh command from the source checkout before exiting. For this repository shape, the command is `just sync-marketplace <previous-main-ref>`.

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

Decision rules:

1. If `post_merge_overlay` is null, no post-merge command is required.
2. Else, if `remaining_operator_owned_step` is true and the overlay declares no autonomous command, emit `POST_MERGE_VERIFY`.
3. Else, if `post_merge_overlay.kind` is `"marketplace-source-refresh"`, report that the source checkout refresh is confirmed and that `just sync-marketplace <previous-main-ref>` runs from the source checkout.
4. Never report `"COMPLETE_AFTER_CHECKOUT_REFRESH"` for a marketplace-source refresh; checkout currency alone is incomplete.

Return only a parseable JSON document matching the schema.
