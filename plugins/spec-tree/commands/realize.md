---
description: Realize all potential nodes — drain spx/POTENTIAL by running the TDD flow for each
argument-hint: [subtree-path]
---

<objective>
Autonomously realize every potential node listed in `spx/POTENTIAL`. For each node, run the full spec-tree TDD flow (contextualize → architect → test → code with review gates), commit, then move to the next node without stopping.

If a subtree path is given as `$ARGUMENTS`, only realize potential nodes under that subtree. Otherwise, realize all.
</objective>

<context>
**Potential Nodes:**
!`cat spx/POTENTIAL 2>/dev/null || echo "(no spx/POTENTIAL file found)"`

**Git Status:**
!`git status --short`

**Recent Commits:**
!`git log --oneline -5`

**Project Language Indicators:**
!`ls pyproject.toml package.json tsconfig.json 2>/dev/null`
</context>

<process>

## Step 1: Parse the work queue

Read `spx/POTENTIAL`. Each non-comment, non-blank line is a node path relative to `spx/`. If `$ARGUMENTS` is provided, filter to only paths that start with (or are nested under) that subtree.

If no potential nodes remain after filtering, report "Nothing to realize" and stop.

## Step 2: Order by dependency

Sort nodes by their numeric index prefix (lower index first). Lower-indexed nodes constrain higher-indexed ones, so they must be realized first.

## Step 3: Realize each node

For each node path, in order:

**3a. Remove from POTENTIAL**

Edit `spx/POTENTIAL` to remove this node's line. Then run the project's sync command (defined in the project's `spx/CLAUDE.md`) to update tool configuration so the node's tests now run.

**3b. Load context**

```text
Skill tool → { "skill": "spec-tree:contextualizing", "args": "spx/{node-path}" }
```

**3c. Run the TDD flow**

```text
Skill tool → { "skill": "spec-tree:coding" }
```

This runs the full 8-phase flow: methodology → context → architect → review → test → review → implement → review.

**3d. Commit the realized node**

```text
Skill tool → { "skill": "spec-tree:committing-changes" }
```

**3e. Move to next node**

Do NOT stop or ask the user. Proceed immediately to the next potential node.

## Step 4: On failure

If a node's TDD flow fails (review gate rejects after max retries, tests won't pass, or implementation blocked):

- STOP the loop — do not skip to the next node
- Report which node failed and at which phase
- Leave remaining nodes in `spx/POTENTIAL`

## Step 5: Report

When all nodes are realized (or on failure), report final status.

</process>

<success_criteria>

- All targeted potential nodes realized (tests passing, implementation complete)
- Each node committed individually
- `spx/POTENTIAL` drained of all realized entries
- No nodes skipped — dependency order respected

</success_criteria>
