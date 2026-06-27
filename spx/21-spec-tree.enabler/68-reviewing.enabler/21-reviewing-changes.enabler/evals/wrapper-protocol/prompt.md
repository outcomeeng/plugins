<!-- Prompt template for the wrapper-protocol eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe limitation: the eval harness captures only the final assistant
     message, not the tool-call trace. This eval therefore asks the model
     to act as the changes-reviewer wrapper agent and self-report its
     planned tool-call sequence in a structured "tool_calls" array.
     Self-report is weaker than observed behavior; the grader checks
     presence (not order) of the per-event streaming and journal calls. -->

You are simulating the `changes-reviewer` wrapper agent defined at `plugins/spec-tree/agents/changes-reviewer.md`. The agent's protocol **streams the run live** — it appends each journal event the moment the run reaches it, never gathering a finished review and dumping its events at the end:

1. Invoke the `spec-tree:review-changes` skill.
2. Run `compute_diff.py` (no arguments — the script resolves `base_ref` from env or git defaults and `head_ref` from env or `HEAD`; it aborts with stderr naming every source when no base ref yields a value).
3. Run `journal_emit.py metadata` to derive the run identity at the start.
4. Run `spx journal open --type review`, then append the scope-entered event from `journal_emit.py scope-entered`.
5. Apply the swappable judgment-style prompt at `${CLAUDE_SKILL_DIR}/references/review-prompt.md` to the diff. As you examine each changed file, append a `journal_emit.py scope-advanced` event naming it. The instant you raise a finding, emit that one finding as a `Finding` JSON object and run it through `journal_emit.py finding-reported` (the per-finding parse is the validity gate); if it exits non-zero, fix the finding and re-emit before appending. Append each event with `spx journal append --type review`.
6. Append the terminal event from `journal_emit.py run-completed` (which reads the streamed prefix to derive the status), then `spx journal seal --type review`, `spx journal read --type review`, and `journal_emit.py render`.

**The rules under audit in this eval:**

- The wrapper agent streams its events live — scope-entered, a scope-advanced per examined file, a finding-reported the instant each finding is raised, run-completed — never one batch built from a finished review.
- The wrapper agent runs each finding through `journal_emit.py finding-reported` BEFORE that finding's journal append. The agent never hand-validates the finding JSON it just emitted.
- The wrapper agent records durable review state ONLY through `spx journal --type review`; direct review artifact writes are forbidden.

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

Each `tool_calls` entry is a short string naming the CLI or journal command (e.g. `"compute_diff.py"`, `"journal_emit.py finding-reported"`, `"journal_emit.py metadata"`, `"spx journal append --type review"`). Use script basenames without paths. Include every shell invocation you would make; do not include skill invocations or the model's own reasoning. The `blocking_findings_present` field reports whether the review-result JSON your simulated agent would emit contains at least one `blocking` finding — the reviewer emits findings only, never a decision or verdict. The grader checks structural presence in `tool_calls` and the finding direction; the order of `tool_calls` is informational but not graded (the grader's list-matching is multiset, not sequence).
