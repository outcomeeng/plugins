---
name: review-changes
description: Protocol for reviewing branch changes against a base ref and recording the result as a sealed review-journal run.
allowed-tools:
  - Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py":*)
  - Read
---

<objective>
A sealed `spx journal --type review` run whose terminal event records review status and finding counts, with the run token returned to the caller.
</objective>

<inputs>

The skill self-discovers the review scope from the current worktree. Callers that need a non-default range export `SPX_VERIFY_BASE_REF` and `SPX_VERIFY_HEAD_REF` before invoking the skill. Wrapper agents may also export branch and target identity variables.

</inputs>

<api_surface>

- MUST: invoke only the bundled runner through one of these commands:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" start
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" append-scope --state "<statePath>" "<changed-file>"
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" append-finding --state "<statePath>"
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" finish --state "<statePath>"
```

`start` computes the diff bundle, opens the review journal, appends the scope-entered event, and returns JSON containing `statePath`, `runToken`, `diffPath`, `manifestPath`, and `changedFiles`.

`append-scope` appends one scope-advanced event for a changed file after Claude has examined that file.

`append-finding` reads one finding JSON object from stdin, wraps it in the journal event envelope, and appends it. The runner does not perform the full review finding schema or citation validation; `spx journal append` is the authoritative event boundary for this stop-gap implementation.

`finish` reads the journal prefix, appends the terminal run-completed event with review status and finding counts, seals the run, removes runner-owned scratch storage, and prints the raw run token.

When any runner verb exits non-zero, stop and surface its stderr. Do not repair journal state by calling `spx journal`, `git`, `mktemp`, `rm`, `date`, or helper scripts directly.

</api_surface>

<review_materials>

After `start`, read:

```text
${CLAUDE_SKILL_DIR}/references/review-prompt.md
<diffPath>
```

Use `manifestPath` and `changedFiles` for navigation, but treat the diff file as the review input. Repository-root review policy files are not part of this skill's review context; the bundled reference prompt is the only prompt authority. Repository-local review rules belong in the repository's spec tree, decisions, root `AGENTS.md` or `CLAUDE.md`, and loaded governing skill files.

</review_materials>

<workflow>

1. Run `start` and parse the returned JSON.
2. Load the prompt reference and diff bundle.
3. Examine every changed file and every emitted diff section. After each changed file has been examined, call `append-scope` for that file.
4. When a finding is raised, immediately pass that one finding JSON object to `append-finding` on stdin. Do not collect findings into a later batch.
5. When review is complete, call `finish`.
6. Report only the raw `runToken` to the caller.

</workflow>

<constraints>

- Never run validation, tests, evals, coverage, lint, typecheck, or any deterministic verification command. Deterministic verification has already passed before this review starts; this skill provides agentic judgment by reading the diff and loaded review context.
- Never invoke `spx journal`, `git`, `mktemp`, `rm`, `date`, `printf`, `compute_diff.py`, `journal_emit.py`, or `review_result.py` directly. The runner is the only command boundary.
- Never write review-result files, rendered Markdown artifacts, or durable state outside `spx journal`. The runner-owned diff bundle and state file are scratch input for the active invocation only.
- The prompt lives only at `${CLAUDE_SKILL_DIR}/references/review-prompt.md`; rotating the prompt must not require changing code.
- Never read `REVIEW.md`, `REVIEW.example.md`, or another repository-root review prompt.
- Findings only. No praise, acknowledgements, open questions, verdicts, or prose summaries belong in the review stream.
- Do not render, summarize, count, or restate findings for the caller. The sealed journal prefix is the review authority.

</constraints>

<failure_modes>

<runner_verb_failure>
What: `start`, `append-scope`, `append-finding`, or `finish` exits non-zero.
Why: The runner could not preserve the review state or journal contract.
Avoid: Stop immediately and return the verb's stderr; never bypass the runner with direct journal or scratch-file commands.
</runner_verb_failure>

<incomplete_scope>
What: A changed file reaches `finish` without a corresponding `append-scope` event.
Why: The sealed run cannot prove that the complete changeset was examined.
Avoid: Traverse every entry in `changedFiles`, use `manifestPath` for navigation, and append scope immediately after examining each file.
</incomplete_scope>

<invalid_finding_event>
What: `append-finding` rejects a finding or the journal rejects its event shape.
Why: The input was batched, malformed, or inconsistent with the journal schema.
Avoid: Send exactly one finding JSON object through stdin per invocation, stop on rejection, and never hand-format a replacement journal event.
</invalid_finding_event>

</failure_modes>

<success_criteria>

- [ ] The final output is exactly the raw `runToken` returned by `finish`.
- [ ] The sealed journal prefix contains a terminal run-completed event.
- [ ] The terminal run-completed event records review status and finding counts.
- [ ] The final output contains no rendered findings, count line, verdict, or summary.
- [ ] A non-zero runner exit is reported with its stderr instead of a partial review result.

</success_criteria>
