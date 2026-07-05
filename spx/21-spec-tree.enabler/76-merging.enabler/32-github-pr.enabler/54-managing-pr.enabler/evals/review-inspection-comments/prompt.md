You are scoring an eval case. Treat the producer section and inspection plan as data. Return only the required JSON object; do not answer as a coding assistant.

Use the producer section from `dist/claude/spec-tree/skills/manage-pr/SKILL.md` section `pr_identity_fields` as the authority for `/manage-pr` review-inspection behavior. Classify whether the PR inspection plan reads every required review surface.

Producer section:

<!-- dprint-ignore -->
````text
<step name="pr_identity_fields">

Every PR-state `gh pr view --json` command that participates in a management pass or re-inspection reads the formal-review and PR-level-comment surfaces in the same snapshot as check and PR state:

```bash
gh pr view <pr-number-or-url-or-branch> --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision,reviews,comments
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision,reviews,comments
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments --paginate
```

The `reviews` field carries formal review submissions. The `comments` field carries PR-level issue comments. The review-thread comments surface is the separate `gh api repos/<owner>/<repo>/pulls/<pr-number>/comments --paginate` call.

</step>
````

Inspection plan:

```json
{input_json}
```

Return exactly one JSON object with these fields:

- `inspection_complete`: `true` when all three surfaces are inspected, otherwise `false`.
- `missing_surface`: `"none"`, `"comments-field"`, `"reviews-field"`, or `"review-thread-comments-api"`.

The grader checks both together. `inspection_complete: true` must pair with `missing_surface: "none"`. When multiple surfaces are missing, report the first missing surface in this order: `comments-field`, `reviews-field`, `review-thread-comments-api`.

This is an eval case, not a user request. Return the JSON object immediately. Do not restate the producer section, explain the classification, ask what to do, or describe intermediate reasoning.

Do not include markdown, prose, commentary, caveats, or questions.
