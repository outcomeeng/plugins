# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

The `spx/21-spec-tree.enabler/79-diagnostics.enabler` re-declaration is deferred behind a published
`@outcomeeng/spx` dependency (see that node's `PLAN.md`).

The decision governs user-scope state ownership. Pending work remains only in that dependent
slice.

## Align the role vocabulary across the remaining skill surfaces

Governing decision: `spx/15-agent-terminology.pdr.md` (the Refiner, Executor, Author, Fixer, and Verifier roles, capitalized).

The router template, its pinned policies, the `/understand` foundation, `/open-pr`, the merging-standards policy reference, `contribution-standards`, the three audit specs, `spx/15-merging.pdr.md`, `spx/21-spec-tree.enabler/76-merge.enabler/merge.md`, and `spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md` carry the role names. Surfaces still describing who produces or verifies work in the old words:

1. Two router headings the compliance evidence harness pins verbatim — "Spawn each verifier or reviewer with its role task as the initial turn." and "Use the `Agent` tool for every configured verifier or reviewer." — stay until the evidence migration recorded in `spx/21-spec-tree.enabler/43-instruction-block.enabler/ISSUES.md` moves those predicates into the linked tests, since editing `outcomeeng_testing/harnesses/instruction_block_compliance_evidence.py` is that migration's revisit trigger.
2. Skills outside the merge-lifecycle pair — `/manage-pr`, `/manage-github-pr`, `/merge`, `/apply`, the audit and review skills — where "the author", "the reviewer", and "the verifier" name the roles; plural and audience uses such as "human reviewers", "CI reviewers", and "reviewer-bot approval" describe people and services, not roles, and stay lowercase.
3. `spx/15-audit-result-delivery.pdr.md`, whose "a reviewer watches on a pull request" names a human reader, stays lowercase.

Why separate: each plugin's skill edit carries the `skill-auditor` gate and a bump, and the harness-pinned headings wait on the evidence migration.

## Refine the methodology 4.0 migration as a Change

`spx.config.yaml` declares methodology 4.0.0. The shipped foundation, router, and specs still state the 3.x grammar: five verification types without Probe, `{slug}.md` spec files, enabler and outcome as the only node kinds, no front matter, no malleability, no outcome records or alternatives. Each move amends its governing decision first (`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` for the type set), and the whole is refined with the operator as a Change before any slice executes.

## Relocate installation governance and split the repository-installation node

`spx/12-marketplace-state.adr.md` sits at the product root while its opening paragraph, invariants, and testing rules govern installation mechanics only; its agent-definition co-location and ownership content is the cross-cutting part. `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler` conflates the maintainers' persistent command — `just install-marketplace`, run with the designated main checkout in the release phase — with isolated verification — `just verify-marketplace-installation`, installing every catalog plugin for every agent into disposable homes — in one spec of more than twenty assertions. The product-level `spx/ISSUES.md` entry on agent-specific behavior inside product-level decisions names the same decision.

Steps; `/decompose` and `/refactor` own placement and index assignment:

1. Move the installation content of `spx/12-marketplace-state.adr.md` into a new decision under `spx/32-distribution.enabler/21-installation.enabler/`; place the co-location and ownership content through `/decompose` — candidate owner `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler` — preserving every sentence; retire the root file.
2. Split the repository-installation node into a persistent-installation child (refresh exactly the installed set, empty-inventory bootstrap, pending publication, agent-home placement and reconciliation, the settings-unchanged invariant) and an isolated-verification child (disposable homes, checkout as marketplace, full catalog and generated subsets, terminal absence, idempotent repeat, the role-discovery probe); distribute the six evidence files and the node's `ISSUES.md` entries.
3. Lift `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/21-installation-architecture.adr.md` to the installation node.
4. Citation sweep: `spx/outcomeeng.product.md`, this file, `spx/ISSUES.md`, `spx/local/merging.md`, the `justfile` recipe test path, the recipe-asserting scenario test, the diagnostics node references, and the prose in `CLAUDE.md`, `AGENTS.md`, and `README.md`.

Ordering: after the settings-unchanged changeset recorded in `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/PLAN.md`.
