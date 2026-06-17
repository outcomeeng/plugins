---
description: Run review-changes against the current branch's diff; print verdict and artifact paths.
argument-hint: ""
allowed-tools: Bash, Read, Skill
---

<objective>
Run the review-changes skill against the current branch's diff and surface the findings to the main agent. The reviewer emits findings only — it never decides. The main agent (or operator) handles every finding by validity and phase — the discipline the `merging-standards` skill defines — never by its severity label: validate each finding against its cited rule and drop the unbacked; fix every valid finding in the diff, or — before the PR opens — split out of the changeset any whose fix is too large to belong and record it in the owning node's `ISSUES.md` / `PLAN.md`.

The slash command is the smallest local equivalent of the CI review workflow — same two-severity verdict shape (`### BLOCKING` / `### DEBT`), no PR open required, no CI roundtrip.
</objective>

<process>

## Step 1: Run the skill

Invoke the `spec-tree:review-changes` skill via the Skill tool. The skill teaches the script chain: derive the current thread, compute the diff against the resolved `base_ref`, apply the swappable review prompt, validate the emitted JSON through the arbiter CLI, render the markdown via the per-section templates under `references/render/`, and persist both `review-result.json` and `review.md` to the thread store.

```text
Skill tool → { "skill": "spec-tree:review-changes" }
```

On chain failure (no `base_ref` derivable, detached HEAD, git unavailable, arbiter rejection), the skill reports the error verbatim — surface it to the user and stop.

## Step 2: Read the artifacts

The skill's chain ended by writing `review-result.json` and `review.md` to the thread store under the derived slug. Read them back via the thread-store CLIs (the skill prose names the exact paths and confirms `--slug` is optional — derived from the current branch).

Use the same `read_record.py --name <name>` invocation the skill teaches; no `--slug` flag.

## Step 3: Print the verdict to the main agent

Print, in this order:

1. The absolute filesystem paths to `review-result.json` and `review.md` (under `.spx/reviews/<slug>/` on the local backend).
2. A one-line finding count by render class: `BLOCKING: <n>, DEBT: <n>` (mapping is identity: render class equals uppercase severity, so `blocking → BLOCKING`, `debt → DEBT`).
3. If the review carries any finding — of any severity — the full `review.md` content. The main agent reads it and handles every finding by validity and phase — per the `merging-standards` skill — never by severity: a `debt` finding is surfaced even when no `blocking` is present, for the author to fix in the PR or track out of scope by disposition.
4. Else (no findings at all): nothing more. The artifacts are on disk.

</process>

<success_criteria>

- The skill's chain ran end-to-end and persisted both `review-result.json` and `review.md`.
- The slash command printed the two paths, the finding-count line, and (when applicable) the full `review.md`.
- No `--slug` argument was passed to any thread-store CLI — Claude never names the thread address.
- When the review carries any finding, the main agent sees the full verdict text without having to read it from disk, so it can handle every finding by validity and phase.

</success_criteria>
