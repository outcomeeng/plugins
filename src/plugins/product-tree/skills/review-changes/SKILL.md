---
name: review-changes
description: ALWAYS invoke this skill when reviewing working changes on a branch against a base ref. NEVER review changes by hand-formatting JSON or by reading persisted review artifacts directly.
allowed-tools:
  - Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py":*)
  - Bash(SPX_VERIFY_*=* python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py":*)
  - Read
  - Grep
  - Glob
  - Write
---

<objective>
The raw run token that `finish` prints for a sealed `spx journal --type review` run.
</objective>

<inputs>

Review scope is discovered from the current worktree. Reusable gate evidence requires the exact current version to be committed and the worktree to be clean. Explicit advisory feedback may include staged, unstaged, or untracked work, and the resulting review supplies no reusable gate evidence. The input may supply the resolved scope as literal `SPX_VERIFY_BASE_REF`, `SPX_VERIFY_HEAD_REF`, `SPX_VERIFY_BRANCH`, `SPX_VERIFY_TARGET_KIND`, and `SPX_VERIFY_PULL_REQUEST_NUMBER` assignments, each written as a prefix on the single `review_run.py start` command line, because a shell export does not persist across Bash calls. `SPX_VERIFY_BASE_REF` and `SPX_VERIFY_HEAD_REF` select a non-default range; the other three record branch and target identity.

</inputs>

<api_surface>

Invoke only the bundled runner:

```bash
[SPX_VERIFY_*=<value> ...] python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" start
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" append-scope --state "<statePath>" "<changed-file>"
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" append-finding --state "<statePath>" < "<finding-file>"
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" finish --state "<statePath>" --unread "<unread-path>"
python3 "${CLAUDE_SKILL_DIR}/scripts/review_run.py" finish --state "<statePath>" --unread-file "<unread-list-file>"
```

The bracketed `SPX_VERIFY_*=<value>` assignments are optional and appear only when the input supplies them, each as a literal prefix on the `start` command line; omit the brackets. Pass `--unread "<unread-path>"` once for each changed file Claude did not read, and omit it when Claude read every changed file. When the unread set is large, write one changed path per line to a payload file with the file-write tool, in the scratch directory `<finding_payload>` names, under a file name unique to this agent and run such as `unread-<runToken>.txt`, and pass that file once as `--unread-file "<unread-list-file>"` with the path exactly as the file-write result reports it; `--unread-file` marks each listed path unread exactly as one `--unread` argument does, and the two forms combine.

`start` fetches a git-derived or `origin/` base and refuses a head behind the fetched `origin/<base>` tip before any journal exists — the dedicated stale-base exit code with a `stale-base` JSON diagnostic on stderr and no run state; a supplied local ref or commit is compared as given — and otherwise computes the diff bundle, opens the review journal, appends the scope-entered event, and returns JSON containing `statePath`, `runToken`, `diffPath`, `manifestPath`, `changedFiles`, `generatedExtents`, `generatedDeclarationChanged`, and `renames`. Report the refusal as a `stale-base` block carrying the diagnostic verbatim and stop.

`changedFiles` lists a renamed file once under its new path. `renames` lists each rename with its `path`, its `former_path`, and `content_unchanged`, true when git detected a rename of identical content. `generatedExtents` is read from `spx/local/generated-sources.toml` as committed at the scope's base ref (`git show <base-ref>:spx/local/generated-sources.toml`), never from the working tree, and is empty when the base lacks the file; it lists, per relation, the changed `files` that the relation's whole-file output pattern matches together with the relation's `sources`, `generator`, and `regenerate` command. A file bounded only by a relation's `begin` and `end` markers is an ordinary changed file. A relation whose declared sources or generator the changeset also changes carries `flagged` true and names them in `changed_sources` and `changed_generator`. When `spx/local/generated-sources.toml` is among the changed paths, `generatedDeclarationChanged` is true and every listed relation carries `flagged` true with `flagged_reason` naming that declaration: the changeset changes the declaration that would exempt its files, so nothing is exempt by declaration, every changed file is ordinary, and the run-completed event records `generatedDeclarationChanged` with that reason and lists no `skippedGenerated` file.

`append-scope` appends one scope-advanced event for a changed file only after Claude has read that file; a file Claude has not read gets no scope-advanced event.

`append-finding` reads one finding JSON object from its standard input, which the input redirect from `<finding-file>` supplies, wraps it in the journal event envelope, and appends it. The runner does not perform the full review finding schema or citation validation; `spx journal append` is the authoritative event boundary.

`finish` refuses, with a non-zero exit, while a changed file is neither advanced nor marked unread, except a declared generated extent and a pure rename, which `finish` accounts for itself and which need no `append-scope` and no unread mark. Otherwise it reads the journal prefix, appends the terminal run-completed event with review status, finding counts, each unread file, each declared generated extent skipped by declaration with its relation's regenerate command, and each rename without content change, and seals the run `failed` when any file is marked unread, never `approved`. A run whose only unexamined files are declared generated extents and pure renames seals by its findings. On a successful `finish` it prints the raw run token. The runner removes its scratch storage on every `finish` exit and on every non-zero exit of `start`, `append-scope`, or `append-finding`, so a failed verb, a coverage refusal included, ends the run and a later verb finds no state.

When any runner verb exits non-zero, stop and surface its stderr, except for the single `append-finding` rerun `<finding_payload>` directs, which follows a shell diagnostic that names an absent finding file and so a runner that never ran and left its state in place; the command boundary in `<constraints>` admits no repair outside the runner.

</api_surface>

<review_materials>

After `start`, read:

```text
${CLAUDE_SKILL_DIR}/references/review-prompt.md
<diffPath>
```

Use `manifestPath` and `changedFiles` for navigation, but treat the diff file as the review input. `Grep` and `Glob` serve two purposes, each read-only and bounded to a relationship the prompt declares: discovery of the unchanged consumers of a changed governing declaration, bounded to exactly the declared relationships the prompt's `<review_scope>` consumers-of-changed-truth item enumerates; and location of the `ISSUES.md` of each governing node of the changed files, bounded to the governing-node relationship the prompt's `<tracked_debt>` section defines. Repository-root review policy files are not part of this skill's review context; the bundled reference prompt is the only prompt authority. Repository-local review rules belong in the repository's Product Tree, decisions, root `{{! file('root_guide', 'codex') !}}` or `{{! file('root_guide', 'claude') !}}`, and loaded governing skill files.

</review_materials>

<workflow>

1. Run `start` and parse the returned JSON.
2. Load the prompt reference and diff bundle.
3. Examine every changed file and every emitted diff section, applying the prompt's `<adversarial_probes>` before treating a file as clean. After Claude has read a changed file, call `append-scope` for that file; never call it for a file Claude sampled or skipped. Judge a declared generated extent through its relation's `sources` and `generator` and never read it as authored work; call neither `append-scope` nor `--unread` for it, and call neither for a pure rename. When a `generatedExtents` entry is `flagged` with `changed_sources` or `changed_generator`, the changeset changes the relation's sources or generator, so Claude may read that relation's extents as evidence of the generator change, and a defect they show resolves to the named `changed_sources` or `changed_generator`. When an entry carries a `flagged_reason`, its files are ordinary changed files: examine each and call `append-scope` after reading it.
4. For each changed governing declaration, discover and read its unchanged consumers per the prompt's `<review_scope>` consumers-of-changed-truth item. A contradiction there is a finding cited at the consumer's location; consumers are not `append-scope` units — the journal's scope coverage remains the changed-file set.
5. Before judging any `debt` finding, locate and read the `ISSUES.md` of each governing node of the changed files per the prompt's `<tracked_debt>` section.
6. When a finding is raised, immediately write that one finding JSON object to its own scratch file and pass it to `append-finding` through the input redirect, following `<finding_payload>`. Do not collect findings into a later batch. Set the finding's `unit` and `tracked` fields as the prompt's `<finding_shape>` and `<tracked_debt>` direct.
7. When review is complete, call `finish`, passing `--unread` for each changed file Claude did not read, or `--unread-file` when that set is large. Exclude declared generated extents and pure renames from the unread set.
8. Output only the raw `runToken` that `finish` printed.

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
- NEVER write review-result files, rendered Markdown artifacts, or durable state outside `spx journal`. The runner-owned diff bundle and state file are scratch input for the active invocation only; the only files Claude writes are a finding payload per `<finding_payload>` and an unread-list payload per `<api_surface>`.
- NEVER load a review prompt other than `${CLAUDE_SKILL_DIR}/references/review-prompt.md` — one prompt keeps every review run comparable.
- NEVER read `REVIEW.md`, `REVIEW.example.md`, or another repository-root review prompt.
- NEVER append praise, acknowledgements, open questions, verdicts, or prose summaries to the review stream — it carries findings only.
- NEVER render, summarize, count, or restate findings in the output. The sealed journal prefix is the review authority.

</constraints>

<failure_modes>

**Runner failure bypassed the command boundary.** A runner verb exited non-zero, and Claude attempted to repair the journal through direct `spx journal` or scratch-file commands. Stop on the failed verb and surface its stderr; the runner remains the only command boundary.

**A retyped finding path sealed a review with no verdict.** Claude rebuilt the finding file path by hand, `append-finding` read no file, and the run ended without recording the finding. Copy the path from the file-write result, and rerun once only when the diagnostic names the file as absent.

**A clean review became a finding.** Claude appended a no-findings comment or synthetic finding before `finish`. Append no finding object for a clean review; `finish` records zero finding counts in the terminal event and returns the raw run token.

**A partial run was reported as complete.** `finish` failed before sealing, and Claude returned the earlier `runToken`. Report the non-zero exit and stderr; only the token printed by a successful `finish` is a completed review result.

**Sampled files were recorded as read.** Claude sampled a large changeset, appended scope for all 322 changed files, and sealed an approval over files it never opened. Append scope only for a file Claude read, and mark every other changed file with `finish --unread`, which seals the run `failed`.

**Generated output was reviewed as authored work.** Claude read every file under a regenerated tree, raised findings in the output, and spent the scope on files the declaration already attributes to a generator. Judge a declared generated extent through its relation's sources, record no scope for it, and cite a finding about generated content at the source; read the extents as evidence only when the relation is `flagged` for changed sources or generator.

**A long unread list broke the command line.** Claude passed hundreds of `--unread` arguments and the command exceeded the shell's limits. Write the paths to a file with the file-write tool and pass it once as `--unread-file`.

**A universal claim was read without being executed.** Claude inspected every changed line and accepted "exhaustive" and "mutually exclusive" as prose. The claim failed for constructed boundary members absent from the corpus. Apply the counterexample probe in `<adversarial_probes>` before completing that file's scope.

**Changed governing truth stopped at the diff boundary.** Claude compared changed specifications with their governors while leaving unchanged language renderings and shipped auditors unread. Those consumers contradicted the new rule. Follow declared derivation edges outward per the prompt's `<review_scope>` consumers-of-changed-truth item and report each contradiction at the consumer.

</failure_modes>

<success_criteria>

- [ ] The sealed journal prefix ends in a terminal run-completed event that records review status, finding counts, each unread file by name, each declared generated extent skipped by declaration with its regenerate command, and each rename without content change.
- [ ] Every changed file that is neither a declared generated extent nor a pure rename is either advanced after being read or named unread, so no unread file is sealed `approved`.
- [ ] The final output contains no rendered findings, count line, verdict, or summary.
- [ ] A non-zero runner exit is reported with its stderr instead of a partial review result.

</success_criteria>
