---
description: Run reviewing-changes against the current branch's diff; print verdict and artifact paths.
---

<objective>
Run the reviewing-changes skill against the current branch's diff and surface the findings to the main agent. The reviewer emits findings only — it never decides. The main agent (or operator) decides what to do next: fix the `blocking` and `debt` findings before pushing; with none of those present, proceed to `/open-pr` or commit.

The slash command is the smallest local equivalent of the GH `spec-tree-review` workflow — same three-severity verdict shape (`### BLOCKING` / `### DEBT` / `### FOLLOW-UP`), no PR open required, no CI roundtrip.
</objective>

<process>

## Step 1: Run the skill

Invoke the `spec-tree:reviewing-changes` skill via the Skill tool. The skill teaches the script chain: derive the current thread, compute the diff against the resolved `base_ref`, apply the swappable review prompt, validate the emitted JSON through the arbiter CLI, render the markdown via the per-section templates under `references/render/`, and persist both `review-result.json` and `review.md` to the thread store.

```text
Skill tool → { "skill": "spec-tree:reviewing-changes" }
```

On chain failure (no `base_ref` derivable, detached HEAD, git unavailable, arbiter rejection), the skill reports the error verbatim — surface it to the user and stop.

## Step 2: Read the artifacts

The skill's chain ended by writing `review-result.json` and `review.md` to the thread store under the derived slug. Read them back via the thread-store CLIs (the skill prose names the exact paths and confirms `--slug` is optional — derived from the current branch).

Use the same `read_record.py --name <name>` invocation the skill teaches; no `--slug` flag.

## Step 3: Print the verdict to the main agent

Print, in this order:

1. The absolute filesystem paths to `review-result.json` and `review.md` (under `.spx/reviews/<slug>/` on the local backend).
2. A one-line finding count by render class: `BLOCKING: <n>, DEBT: <n>, FOLLOW-UP: <n>` (mapping is identity: render class equals uppercase severity, so `blocking → BLOCKING`, `debt → DEBT`, `follow_up → FOLLOW-UP`).
3. If any `blocking` or `debt` finding is present: the full `review.md` content. The main agent reads it and decides which findings to fix first.
4. Else: nothing more. The artifacts are on disk; the main agent can read them if it wants the full text.

</process>

<success_criteria>

- The skill's chain ran end-to-end and persisted both `review-result.json` and `review.md`.
- The slash command printed the two paths, the finding-count line, and (when applicable) the full `review.md`.
- No `--slug` argument was passed to any thread-store CLI — the agent never names the thread address.
- When a `blocking` or `debt` finding is present, the main agent sees the full verdict text without having to read it from disk.

</success_criteria>
