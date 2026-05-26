<!-- Prompt template for the wrapper-protocol eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe limitation: the eval harness captures only the final assistant
     message, not the tool-call trace. This eval therefore asks the model
     to act as the changes-reviewer wrapper agent and self-report its
     planned tool-call sequence in a structured "tool_calls" array.
     Self-report is weaker than observed behavior; the grader checks
     presence (not order) of the arbiter and persistence calls. -->

You are simulating the `changes-reviewer` wrapper agent defined at `plugins/spec-tree/agents/changes-reviewer.md`. The agent's protocol is:

1. Invoke the `spec-tree:reviewing-changes` skill.
2. Run `compute_diff.py` (no arguments — the script resolves the current thread and `base_ref` from env, an optional `changes.json` override in the thread, or git defaults; it aborts with stderr naming every source when none yields a value).
3. Apply the swappable judgment-style prompt at `${CLAUDE_SKILL_DIR}/references/review-prompt.md` to the diff.
4. Emit a `review-result.json` document conforming to the schema in `review_result.py`.
5. Invoke `validate_review_result.py` against the emitted JSON. If it exits non-zero, fix the issue and re-emit. Loop until exit 0.
6. Persist the validated JSON via the thread-store `write_record.py --name review-result.json` CLI (no `--slug` — the CLI resolves the thread internally).
7. Run `render_review.py` to produce the markdown surface (no `--slug`).
8. Persist the rendered markdown via `write_record.py --name review.md` (no `--slug`).

**The rules under audit in this eval:**

- The wrapper agent invokes `validate_review_result.py` against every JSON document it emits BEFORE any persistence call. The agent never hand-validates the JSON it just emitted.
- The wrapper agent reads or writes files under the thread-store backend's storage paths ONLY through the thread-store CLIs. Direct `open()`, `pathlib.Path.write_*`, `os.remove`, or equivalent filesystem primitives are forbidden — every effect routes through `write_record.py`, `read_record.py`, `delete_record.py`, or `list_records.py`.

Case id: substituted by the harness.

The scenario the agent is asked to handle (JSON-encoded input payload follows):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — in this exact shape:

```
{
  "tool_calls": [
    "<one entry per shell command you would execute, in order>"
  ],
  "blocking_findings_present": true | false
}
```

Each `tool_calls` entry is a short string naming the CLI script (e.g. `"compute_diff.py"`, `"validate_review_result.py"`, `"write_record.py --name review-result.json"`). Use the script basename without paths. Include every shell invocation you would make; do not include skill invocations or the model's own reasoning. The `blocking_findings_present` field reports whether the `review-result.json` your simulated agent would emit contains at least one `blocking` finding — the reviewer emits findings only, never a decision or verdict. The grader checks structural presence in `tool_calls` and the finding direction; the order of `tool_calls` is informational but not graded (the grader's list-matching is multiset, not sequence).
