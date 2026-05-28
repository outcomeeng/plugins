---
template_version: "0.18.2"
template_source: spec-tree
---

# spx/ Directory Guide (Spec Tree)

This guide explains WHEN to invoke spec-tree skills for the **Outcome Engineering Plugin Marketplace** product. It is a **router** — the skills contain the HOW.

---

## Structure Overview

The `spx/` tree is a durable map of the product. Nothing moves because work is "done" — specs are permanent product truth, not a backlog.

Two node types at any depth:

```text
spx/
  outcomeeng.product.md                # Product spec (root)
  NN-{slug}.adr.md                     # Architecture decision
  NN-{slug}.pdr.md                     # Product decision
  NN-{slug}.enabler/                   # Shared infrastructure
    {slug}.md                          # Spec file
    tests/                             # Co-located tests
    PLAN.md                            # Coordination note: deferred plan (optional)
    ISSUES.md                          # Coordination note: known issues (optional)
    NN-{slug}.enabler/                 # Children: enablers only
  NN-{slug}.outcome/                   # Hypothesis + assertions
    {slug}.md                          # Spec file
    tests/                             # Co-located tests
    PLAN.md                            # Coordination note: deferred plan (optional)
    ISSUES.md                          # Coordination note: known issues (optional)
    NN-{slug}.{enabler|outcome}/       # Children: enablers and outcomes
```

---

## Key Principles

1. **Durable map**: Specs stay in place. Nothing moves because work is "done."
2. **Two node types**: Enabler (infrastructure, output is known) and outcome (hypothesis, output is a bet). Enablers can only contain enabler children. Outcomes can contain both.
3. **Co-location**: Tests live with their spec in `tests/`.
4. **Atemporal voice**: Specs state product truth. Never narrate history.
5. **Deterministic context**: The tree path defines what context an agent receives.
6. **Decision records win by hierarchy**: If a spec contradicts an ADR or PDR in its ancestry, the spec is wrong. Rewrite the spec to align with the decision record before any implementation work.
7. **Decision records updated in-place**: When a decision changes, update the ADR/PDR directly. No "superseded" workflow.
8. **Coordination notes**: PLAN.md and ISSUES.md in node directories are committed coordination notes created during development or left by `/handoff`. They are committed to git only to carry coordination across sessions; they never hold spec assertions or decisions. They go stale unless acted upon, so verify a note before it steers work — reconcile it against the specs, decisions, assertions, tests, implementation, and current user intent. `/contextualizing` reads them automatically. Remove a resolved note; for ISSUES.md entries, either delete the fixed entry or convert unresolved product work into a spec node.

---

## Numeric Prefixes

Numeric prefixes drive deterministic context loading within each directory:

1. Lower-index sibling specs are read as constraining context for higher-index targets.
2. Same-index siblings are listed but not read as target constraints.
3. Higher-index siblings are listed but not read as target constraints.
4. Files and directories share one number space. The numeric prefix sorts; the type suffix identifies the artifact.
5. Numbers are sibling-unique only. The same integer can be reused under a different parent.

Read an existing directory like this:

```text
spx/
  15-auth-strategy.adr.md
  21-test-harness.enabler/
  32-auth.outcome/
  32-billing.outcome/
  43-integration.outcome/
```

Work on `spx/43-integration.outcome/` reads `spx/15-auth-strategy.adr.md`, `spx/21-test-harness.enabler/test-harness.md`, `spx/32-auth.outcome/auth.md`, and `spx/32-billing.outcome/billing.md` as prior context. Work on `spx/32-auth.outcome/` does not read `spx/32-billing.outcome/`; same-index siblings are unordered peers.

Use `/decomposing` to create or restructure child nodes. It owns concern boundaries, node types, ordering evidence, and sparse index assignment.

**ALWAYS use full paths when referencing nodes, ADRs, and PDRs** — indices are sibling-unique, not globally unique, and bare decision filenames cannot be resolved:

| Wrong                  | Correct                                    |
| ---------------------- | ------------------------------------------ |
| "32-parser.enabler"    | "spx/21-infra.enabler/32-parser.enabler"   |
| "implement enabler-43" | "spx/21-infra.enabler/43-api.enabler"      |
| "15-build.adr.md"      | "spx/21-spec-tree.enabler/15-build.adr.md" |
| "21-pricing.pdr.md"    | "spx/32-billing.outcome/21-pricing.pdr.md" |

---

## When to Invoke Skills

### Before ANY spec-tree work → `/understanding`

**BLOCKING REQUIREMENT**

Loads the Spec Tree methodology. Emits `<SPEC_TREE_FOUNDATION>` marker. Required once per session.

### Before working on a specific node → `/contextualizing`

**BLOCKING REQUIREMENT**

Walks the tree from product root to target, reads all ancestor specs, lower-index siblings, and ADRs/PDRs.

### When creating specs or nodes → `/authoring`

Create product specs, ADRs/PDRs, enabler nodes, outcome nodes.

### When breaking down a node → `/decomposing`

Decompose when a node has too many assertions (>7) or contains independent concerns.

### When restructuring the tree → `/refactoring`

Move nodes, re-scope assertions, extract shared enablers, consolidate duplicates.

### When checking consistency → `/aligning`

Review, audit, or quality check specs. Find contradictions or gaps.

### Before opening a PR → `/opening-pr` (`REVIEW_READINESS` gate)

**BLOCKING REQUIREMENT**

Every change destined for the default branch passes through the `REVIEW_READINESS` gate at `/opening-pr` before the PR opens. The gate holds when deterministic verification (`just check`) passes **and** the local review has converged. `/opening-pr` invokes the `changes-reviewer` agent on the working diff (isolated context, so the verdict is not biased by what the operator's main agent has been doing; fall back to the `/review-changes` slash command when the agent is not installed — both invoke the same `reviewing-changes` skill chain). The agent acts on each finding by **validity and phase, never severity**: validate against the cited rule, drop the unbacked, apply every valid finding that belongs, and split out of the changeset any whose fix is too large to belong (recorded in the relevant node's `ISSUES.md` or `PLAN.md`). Once `REVIEW_READINESS` holds the PR opens `ready_for_review`; `MERGE_READINESS` and `PRODUCTION_READINESS` then govern the merge. See `spx/21-spec-tree.enabler/76-merging.enabler/merging.md` for the spec assertions and `spx/21-spec-tree.enabler/76-merging.enabler/evals/` for the `[eval]` evidence.

---

## Quick Reference: Skills and Agents

Skills run in the main conversation. Agents preload the skill and run autonomously as subagents, returning structured APPROVED/REJECTED verdicts. Use agents when running multiple audits in parallel; use skills when you want to discuss findings with the user.

| User Says...             | Skill                           | Agent                         |
| ------------------------ | ------------------------------- | ----------------------------- |
| "Implement this outcome" | `/contextualizing`              | —                             |
| "Create an outcome"      | `/authoring`                    | —                             |
| "Add an ADR"             | `/authoring`                    | —                             |
| "This node is too big"   | `/decomposing`                  | —                             |
| "Move this under that"   | `/refactoring`                  | —                             |
| "Check these specs"      | `/aligning`                     | —                             |
| "Write tests for this"   | `/testing`                      | —                             |
| "Start the TDD flow"     | `/applying`                     | `applier`                     |
| "Audit this PDR"         | `/auditing-product-decisions`   | `pdr-auditor`                 |
| "Audit test evidence"    | `/auditing-tests`               | `test-evidence-auditor`       |
| "Audit this code"        | `/auditing-python`              | `python-code-auditor`         |
| "Audit this ADR"         | `/auditing-python-architecture` | `python-architecture-auditor` |
| "Audit these tests"      | `/auditing-python-tests`        | `python-test-auditor`         |

---

## Test Naming Convention

Test level is encoded in the filename.

### Python

| Level | Pattern                           | Example                        |
| ----- | --------------------------------- | ------------------------------ |
| 1     | `test_{subject}.{evidence}.l1.py` | `test_parsing.scenario.l1.py`  |
| 2     | `test_{subject}.{evidence}.l2.py` | `test_cli.scenario.l2.py`      |
| 3     | `test_{subject}.{evidence}.l3.py` | `test_workflow.scenario.l3.py` |

---

## Assertion Evidence Contract

Spec assertions link to their evidence inline:

```markdown
### Scenarios

- Given X, when Y, then Z ([test](tests/test_slug.scenario.l1.py))
```

Use `[test](...)` for automated evidence and `[review]` for semantic constraints that cannot be checked by a finite automated test. Every assertion must carry an evidence tag.

---

## Excluded Nodes

Nodes with specs and tests but no implementation are listed in `spx/EXCLUDE`. The `spx` CLI reads this file and skips excluded nodes when running `spx test passing`. Linting always applies — style is checked regardless of implementation existence.

`spx` never writes to product configuration files. It passes exclusion flags to each tool at invocation time.

Remove entries when implementation begins and tests should start running.

---

## Session Management

Claude Code session handoffs are stored in `.spx/sessions/` (separate from the spec tree):

```text
.spx/sessions/
├── todo/          # Available for /pickup
├── doing/         # Currently claimed
└── archive/       # Completed sessions
```

Use `/handoff` to create, `/pickup` to claim.
