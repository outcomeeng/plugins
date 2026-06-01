<!-- Prompt template for the review-inspection-comments eval.
     The harness substitutes the case id and input JSON tokens before
     sending the prompt to the model.

     Probe scope: the eval verifies the review-inspection contract in
     /standardizing-merging and /managing-pr. Automated reviewers and
     humans may post as formal reviews, PR-level issue comments, or
     review-thread comments on specific lines. A correct inspection must
     query all three surfaces. -->

You are simulating the PR-management agent inspecting review state for an open PR.

The inspection contract:

- `gh pr view` calls that inspect PR-level issue comments must include `comments` in the requested field list, alongside the other PR state needed for the managing loop.
- Formal reviews are inspected through the `reviews` field.
- Review-thread comments tied to lines are inspected separately through the pull-request comments API.

Classify the inspection plan in the input. It is complete only when every `gh_pr_view_field_list` entry that is used for review/PR-state inspection includes `comments`, at least one such field list includes `reviews`, and `pull_request_comments_api_called` is `true`.

Case id: substituted by the harness.

The inspection plan (JSON-encoded):

```json
{input_json}
```

Verdict schema — two fields, both mandatory:

- `inspection_complete`: `true` when all three surfaces are inspected, otherwise `false`.
- `missing_surface`: `"none"`, `"comments-field"`, `"reviews-field"`, or `"review-thread-comments-api"`.

The grader checks both together. `inspection_complete: true` must pair with `missing_surface: "none"`. When multiple surfaces are missing, report the first missing surface in this order: `comments-field`, `reviews-field`, `review-thread-comments-api`.
