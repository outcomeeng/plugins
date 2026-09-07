# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

The `spx/21-spec-tree.enabler/79-diagnostics.enabler` re-declaration is deferred behind a published
`@outcomeeng/spx` dependency (see that node's `PLAN.md`).

The decision governs user-scope state ownership. Pending work remains only in that dependent
slice.

## Align the role vocabulary across skills, the router, and the remaining specs

Governing decision: `spx/15-agent-terminology.pdr.md` (the Refiner, Executor, Author, Fixer, and Verifier roles, capitalized).

The decision names the roles and `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` and `spx/43-prose.enabler/prose.md` carry them. Surfaces still describing who produces or verifies work in the old words, in dependency order:

1. Router template and its pins: `src/plugins/spec-tree/skills/update-instruction-block/templates/instruction-block.md` (two "authoring agent session" sites), the `*_POLICY_REQUIREMENTS` tuples and `verifier`-bearing contradiction patterns in `outcomeeng/distribution/instruction_block.py`, and `spx/21-spec-tree.enabler/43-instruction-block.enabler/tests/test_instruction_block.compliance.l1.py`; regenerate with `just build-instructions`.
2. Shipped skills: `src/plugins/spec-tree/skills/understand/SKILL.md` (the commit-before-read sentence), `src/plugins/spec-tree/skills/open-pr/SKILL.md`, `src/plugins/spec-tree/skills/merging-standards/references/merge-policy.md`, `src/plugins/contribute/skills/contribution-standards/SKILL.md`, and every skill naming "the author context", "the authoring conversation", or a lowercase verifier role; each plugin takes the `skill-auditor` gate and a bump.
3. Specs and decisions: the "author context" clause in `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-specs.enabler/audit-specs.md`, `.../32-audit-tests.enabler/audit-tests.md`, and `.../32-changeset-coherence.enabler/changeset-coherence.md`; the lowercase "reviewer" and "author" in `spx/15-merging.pdr.md` and `spx/15-audit-result-delivery.pdr.md`.

Why separate: items 1 and 2 are plugin-distribution changes carrying the skill-auditor gate, a bump, and a router pin migration, and item 3 spans nodes whose contexts the terminology changeset does not load.

## Refine the methodology 4.0 migration as a Change

`spx.config.yaml` declares methodology 4.0.0. The shipped foundation, router, and specs still state the 3.x grammar: five verification types without Probe, `{slug}.md` spec files, enabler and outcome as the only node kinds, no front matter, no malleability, no outcome records or alternatives. Each move amends its governing decision first (`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` for the type set), and the whole is refined with the operator as a Change before any slice executes.
