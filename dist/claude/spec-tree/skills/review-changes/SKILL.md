---
name: review-changes
description: ALWAYS invoke this skill when reviewing working changes on a branch against a base ref. NEVER review changes by hand-formatting JSON or by reading persisted review artifacts directly.
allowed-tools:
  - Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py":*)
  - Read
  - Grep
  - Glob
  - Write
---

<objective>
A sealed `spx journal --type review` run whose terminal event records review status and finding counts, with the run token returned to the caller.
</objective>

<inputs>

Review scope is discovered from the current worktree. Reusable gate evidence requires the exact current version to be committed and the worktree to be clean. Explicit advisory feedback may include staged, unstaged, or untracked work, and the resulting review supplies no reusable gate evidence. Export `SPX_VERIFY_BASE_REF` and `SPX_VERIFY_HEAD_REF` to select a non-default range. Branch and target identity variables may also be exported.

</inputs>

<api_surface>

Invoke only the bundled runner:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" start
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" append-scope --state "<statePath>" "<changed-file>"
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" append-finding --state "<statePath>" < "<finding-file>"
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" finish --state "<statePath>" --unread "<unread-file>"
```

Pass `--unread "<unread-file>"` once for each changed file Claude did not read, and omit it when Claude read every changed file.

`start` fetches a git-derived or `origin/` base and refuses a head behind the fetched `origin/<base>` tip before any journal exists — the dedicated stale-base exit code with a `stale-base` JSON diagnostic on stderr and no run state; an exported local ref or commit is compared as given — and otherwise computes the diff bundle, opens the review journal, appends the scope-entered event, and returns JSON containing `statePath`, `runToken`, `diffPath`, `manifestPath`, and `changedFiles`. Report the refusal as a `stale-base` block carrying the diagnostic verbatim and stop.

`append-scope` appends one scope-advanced event for a changed file only after Claude has read that file; a file Claude has not read gets no scope-advanced event.

`append-finding` reads one finding JSON object from its standard input, which the input redirect from `<finding-file>` supplies, wraps it in the journal event envelope, and appends it. The runner does not perform the full review finding schema or citation validation; `spx journal append` is the authoritative event boundary.

`finish` refuses, with a non-zero exit, while a changed file is neither advanced nor marked unread. Otherwise it reads the journal prefix, appends the terminal run-completed event with review status, finding counts, and each unread file, and seals the run `failed` when any file is marked unread, never `approved`. It then removes runner-owned scratch storage and prints the raw run token.

When any runner verb exits non-zero, stop and surface its stderr, except for the single `append-finding` rerun `<finding_payload>` directs; the command boundary in `<constraints>` admits no repair outside the runner.

</api_surface>

<review_materials>

After `start`, read:

```text
${CLAUDE_SKILL_DIR}/references/review-prompt.md
<diffPath>
```

Use `manifestPath` and `changedFiles` for navigation, but treat the diff file as the review input. `Grep` and `Glob` serve two purposes, each read-only and bounded to a relationship the prompt declares: discovery of the unchanged consumers of a changed governing declaration, bounded to exactly the declared relationships the prompt's `<review_scope>` consumers-of-changed-truth item enumerates; and location of the `ISSUES.md` of each governing node of the changed files, bounded to the governing-node relationship the prompt's `<tracked_debt>` section defines. Repository-root review policy files are not part of this skill's review context; the bundled reference prompt is the only prompt authority. Repository-local review rules belong in the repository's spec tree, decisions, root `AGENTS.md` or `CLAUDE.md`, and loaded governing skill files.

</review_materials>

<workflow>

1. Run `start` and parse the returned JSON.
2. Load the prompt reference and diff bundle.
3. Examine every changed file and every emitted diff section, applying the prompt's `<adversarial_probes>` before treating a file as clean. After Claude has read a changed file, call `append-scope` for that file; never call it for a file Claude sampled or skipped.
4. For each changed governing declaration, discover and read its unchanged consumers per the prompt's `<review_scope>` consumers-of-changed-truth item. A contradiction there is a finding cited at the consumer's location; consumers are not `append-scope` units — the journal's scope coverage remains the changed-file set.
5. Before judging any `debt` finding, locate and read the `ISSUES.md` of each governing node of the changed files per the prompt's `<tracked_debt>` section.
6. When a finding is raised, immediately write that one finding JSON object to its own scratch file and pass it to `append-finding` through the input redirect, following `<finding_payload>`. Do not collect findings into a later batch. Set the finding's `unit` and `tracked` fields as the prompt's `<finding_shape>` and `<tracked_debt>` direct.
7. When review is complete, call `finish`, passing `--unread` for each changed file Claude did not read.
8. Report only the raw `runToken` to the caller.

</workflow>

<finding_payload>

A finding is a payload: it carries code spans, quotes, and JSON.

- ALWAYS: write each finding with the file-write tool to a file in the scratch directory the harness names for this session, under a file name unique to this agent and run, such as `finding-<runToken>-<n>.json`. Where the harness names no scratch directory, use the one the hosting environment designates, such as `$RUNNER_TEMP` on a hosted runner.
- ALWAYS: copy the scratch directory the harness names into each finding path character for character — a path rebuilt by hand differs from the written file by one character, and the runner then reads no file.
- ALWAYS: when a file-write result reports a path that the scratch directory does not contain by whole path components, stop before `append-finding` and name the reported path.
- ALWAYS: pass the file to `append-finding` with the input redirect `< <finding-file>`, with the path exactly as the file-write result reports it, written out literally, never held in a shell variable or expanded.
- ALWAYS: when `append-finding` exits non-zero with a diagnostic that names the finding file as absent, run `append-finding` once more with the path copied from the file-write result; on a second failure, stop and report the exit, the stderr, and the run token.
- NEVER: send a finding through a heredoc, a pipe, or an inline argument.
- NEVER: remove a finding file; the harness clears its scratch directory.

</finding_payload>

<constraints>

- NEVER run validation, tests, evals, coverage, lint, typecheck, or any deterministic verification command. Deterministic verification has already passed before this review starts; this skill provides agentic judgment by reading the diff and loaded review context.
- NEVER invoke `spx journal`, `git`, `mktemp`, `rm`, `date`, `printf`, `compute_diff.py`, `journal_emit.py`, or `review_result.py` directly. The runner is the only command boundary.
- NEVER write review-result files, rendered Markdown artifacts, or durable state outside `spx journal`. The runner-owned diff bundle and state file are scratch input for the active invocation only; the only file Claude writes is a finding payload per `<finding_payload>`.
- NEVER load a review prompt other than `${CLAUDE_SKILL_DIR}/references/review-prompt.md` — one prompt keeps every review run comparable.
- NEVER read `REVIEW.md`, `REVIEW.example.md`, or another repository-root review prompt.
- NEVER append praise, acknowledgements, open questions, verdicts, or prose summaries to the review stream — it carries findings only.
- NEVER render, summarize, count, or restate findings for the caller. The sealed journal prefix is the review authority.

</constraints>

<failure_modes>

**Runner failure bypassed the command boundary.** A runner verb exited non-zero, and Claude attempted to repair the journal through direct `spx journal` or scratch-file commands. Stop on the failed verb and surface its stderr; the runner remains the only command boundary.

**A retyped finding path sealed a review with no verdict.** Claude rebuilt the finding file path by hand, `append-finding` read no file, and the run ended without recording the finding. Copy the path from the file-write result, and rerun once only when the diagnostic names the file as absent.

**A clean review became a finding.** Claude appended a no-findings comment or synthetic finding before `finish`. Append no finding object for a clean review; `finish` records zero finding counts in the terminal event and returns the raw run token.

**A partial run was reported as complete.** `finish` failed before sealing, and Claude returned the earlier `runToken`. Report the non-zero exit and stderr; only the token printed by a successful `finish` is a completed review result.

**Sampled files were recorded as read.** Claude sampled a large changeset, appended scope for all 322 changed files, and sealed an approval over files it never opened. Append scope only for a file Claude read, and mark every other changed file with `finish --unread`, which seals the run `failed`.

**A universal claim was read without being executed.** Claude inspected every changed line and accepted "exhaustive" and "mutually exclusive" as prose. The claim failed for constructed boundary members absent from the corpus. Apply the counterexample probe in `<adversarial_probes>` before completing that file's scope.

**Changed governing truth stopped at the diff boundary.** Claude compared changed specifications with their governors while leaving unchanged language renderings and shipped auditors unread. Those consumers contradicted the new rule. Follow declared derivation edges outward per the prompt's `<review_scope>` consumers-of-changed-truth item and report each contradiction at the consumer.

</failure_modes>

<success_criteria>

- [ ] The final output is exactly the raw `runToken` returned by `finish`.
- [ ] The sealed journal prefix contains a terminal run-completed event.
- [ ] The terminal run-completed event records review status and finding counts, and names each unread file.
- [ ] The final output contains no rendered findings, count line, verdict, or summary.
- [ ] A non-zero runner exit is reported with its stderr instead of a partial review result.

</success_criteria>
