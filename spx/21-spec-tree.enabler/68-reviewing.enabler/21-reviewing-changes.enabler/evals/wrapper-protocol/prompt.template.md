<!-- Generated from the complete wrapper-agent and review-skill producers. -->

Apply the complete producers below to the supplied diff. Preserve their wrapper-to-skill invocation boundary, runner command surface, immediate finding stream, and caller-output contract. For deterministic grading, return exactly one JSON object with:

- `tool_calls`: the ordered `review_run.py` verb labels the wrapper path uses, with each entry exactly one of `start`, `append-scope`, `append-finding`, or `finish` rather than a shell command;
- `blocking_findings_present`: whether the review would append at least one blocking finding;
- `caller_output`: `raw-run-token-only` when the wrapper returns the skill's raw run token without rendering, summarizing, counting, or restating findings;
- `external_review_artifacts_written`: `false` when the wrapper and skill preserve the producer contract that durable review state exists only in `spx journal` and write no review-result or rendered review artifact elsewhere. Runner-owned scratch input and state for the active invocation do not count as external review artifacts.

{producer_files}
The diff input (JSON-encoded):

```json
{input_json}
```
