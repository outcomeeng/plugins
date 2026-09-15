# Plan

## Marketplace diagnostics

The `spx/21-spec-tree.enabler/79-diagnostics.enabler` re-declaration is deferred behind a published
`@outcomeeng/spx` dependency (see that node's `PLAN.md`).

## Align the role vocabulary across the remaining skill surfaces

Governing decision: `spx/15-agent-terminology.pdr.md` (the Refiner, Executor, Author, Fixer, and Verifier roles, capitalized).

The router template, its pinned policies, the `/understand` foundation, `/open-pr`, the merging-standards policy reference, `contribution-standards`, the three audit specs, `spx/15-merging.pdr.md`, `spx/21-spec-tree.enabler/76-merge.enabler/merge.md`, and `spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md` carry the role names. Surfaces still describing who produces or verifies work in the old words:

1. Skills outside the merge-lifecycle pair — `/manage-pr`, `/manage-github-pr`, `/merge`, `/apply`, the audit and review skills — where "the author", "the reviewer", and "the verifier" name the roles; plural and audience uses such as "human reviewers", "CI reviewers", and "reviewer-bot approval" describe people and services, not roles, and stay lowercase.
2. `spx/15-audit-result-delivery.pdr.md`, whose "a reviewer watches on a pull request" names a human reader, stays lowercase.

Why separate: each plugin's skill edit carries the `skill-auditor` gate and a bump.

## Refine the methodology 4.0 migration as a Change

`spx.config.yaml` declares methodology 4.0. The shipped foundation, router, and specs still state the 3.x grammar: five verification types without Probe, `{slug}.md` spec files, enabler and outcome as the only node kinds, no front matter, no malleability, no outcome records or alternatives. Each move amends its governing decision first (`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` for the type set), and the whole is refined with the operator as a Change before any slice executes.

## Installation execution

The structural and evidence-quality work is coordinated in [Change #14](https://github.com/outcomeeng/changes/issues/14). Persistent refresh implementation remains in [Change #48](https://github.com/outcomeeng/changes/issues/48), governed by `spx/32-distribution.enabler/21-installation.enabler/12-installation-state.pdr.md` and `spx/32-distribution.enabler/21-installation.enabler/15-installation-architecture.adr.md`.
