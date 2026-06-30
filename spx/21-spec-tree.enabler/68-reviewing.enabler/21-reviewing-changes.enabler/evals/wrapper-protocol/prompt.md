<!-- Prompt template for the wrapper-protocol eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe limitation: the eval harness captures only the final assistant
     message, not the tool-call trace. This eval therefore asks the model
     to act as the changes-reviewer wrapper agent and self-report its
     planned tool-call sequence in a structured "tool_calls" array.
     Self-report is weaker than observed behavior; the grader checks
     presence of the runner command calls. -->

You are simulating the `changes-reviewer` wrapper agent defined at `plugins/spec-tree/agents/changes-reviewer.md`. The agent's protocol invokes the `spec-tree:review-changes` skill, and that skill uses exactly one command surface:

1. Run `review_run.py start`.
2. Read `REVIEW.md` when present, `${CLAUDE_SKILL_DIR}/references/review-prompt.md`, and the returned diff path.
3. As each changed file is examined, run `review_run.py append-scope`.
4. The instant a finding is raised, emit that one finding JSON object and run `review_run.py append-finding`.
5. When review is complete, run `review_run.py finish`.
6. Return only the raw run token from `finish`; do not render, summarize, count, or restate findings for the caller.

**The rules under audit in this eval:**

- The wrapper reaches the review implementation only through the `review-changes` skill and the skill's `review_run.py` command surface.
- Findings are emitted immediately as single finding JSON objects and passed to `review_run.py append-finding`; no finding batch is created.
- Durable review state is recorded only through the journal calls owned by the runner.
- Caller-facing output is the raw run token only.

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

Each `tool_calls` entry is a short string naming the runner command, for example `"review_run.py start"`, `"review_run.py append-scope"`, `"review_run.py append-finding"`, or `"review_run.py finish"`. Include shell invocations only; do not include skill invocations or the model's own reasoning. The `blocking_findings_present` field reports whether the simulated review would emit at least one `blocking` finding. The grader checks structural presence in `tool_calls` and the finding direction; the order of `tool_calls` is informational but not graded.
