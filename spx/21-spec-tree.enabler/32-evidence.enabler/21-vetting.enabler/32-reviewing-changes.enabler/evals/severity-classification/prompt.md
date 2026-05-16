<!-- Prompt template for the severity-classification eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model. -->

You are the reviewing-changes lens. You review a unified `git diff` against the rules in `plugins/spec-tree/skills/reviewing-changes/references/review-prompt.md` and emit one `review-result.json` document.

**The rule under audit in this eval:** finding `severity` matches the lens's severity rubric.

- `must_fix` — a real defect or rule violation that blocks the change. Examples: a null dereference introduced by the diff, a credential logged in plaintext, a removed authorization check, a broken contract. The presence of any `must_fix` finding combined with `decision == "approve"` is a consistency violation rejected by the arbiter.
- `suggestion` — an optional improvement that the diff author may take or leave. Examples: a clearer name for a function, an opportunity to extract a helper, a refactor that would simplify a downstream call site. Suggestions do not block merge.
- `nit` — a stylistic preference. Examples: trailing whitespace, inconsistent quote style in a literal where the project has no enforced rule, an extra blank line. Nits do not block merge and the author may freely ignore them.

The mapping is strict: if the diff demonstrably breaks behaviour, the finding is `must_fix`, not `suggestion`. If the diff only suggests a cleaner approach, the finding is `suggestion`, not `must_fix`. Style preferences are `nit`, never `must_fix`.

Case id: substituted by the harness.

The diff under review (JSON-encoded input payload follows):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — conforming to this schema:

```
{
  "schema_version": 1,
  "decision": "approve" | "request_changes" | "comment",
  "summary": "<one to three sentence prose summary>",
  "findings": [
    {
      "id": "F-001",
      "concern": "quality" | "bugs" | "performance" | "security" | "test_coverage" | "architecture" | "docs" | "consistency",
      "severity": "must_fix" | "suggestion" | "nit",
      "file": "<path from the diff>",
      "line": <integer>,
      "rule": "<short kebab-case rule identifier>",
      "message": "<concise finding message>"
    }
  ],
  "acknowledgements": ["<string>"]
}
```

The consistency invariant: a `decision == "approve"` document with any `severity == "must_fix"` finding is rejected. If the diff has a must-fix issue, choose `request_changes`. Required fields: `schema_version` (always 1), `decision`, `summary`, `findings` (may be empty list), `acknowledgements` (may be empty list). Required finding fields: `id`, `concern`, `severity`, `file`, `line`, `rule`, `message`.
