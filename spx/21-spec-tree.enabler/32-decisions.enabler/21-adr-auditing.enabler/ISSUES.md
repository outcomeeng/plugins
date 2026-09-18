# Issues

## Eval run history is stale for all three suites

The newest full-suite passing rows for `evals/structure`, `evals/voice`, and
`evals/tag-validity` are from 2026-07-11 (git SHAs
`afe86c93648cae7896781155345627f0c5be62b9` and
`16c29f04a151d941ed4a0be9855892f3234055fa`); the 2026-07-20 rows are single-case
runs on commits that are not ancestors of the current head. The producer
`src/plugins/spec-tree/skills/audit-adr/SKILL.md` changed in twenty commits since,
the eval harness changed, and `prompt.md` was rematerialized, so no committed run
proves the current producer, prompt, and case set. `PLAN.md` in this node defers
the refresh behind the verification-run migration.

**Settlement condition**: one passing `just eval-node` run over the three suites
on a head that carries the current producer, with its rows committed to each
`history.jsonl`.

**Evidence**: `spec-tree:eval-evidence-auditor` findings `f-007`, `f-008`,
`f-009` on head `a65659114b99767b90b4d920550fff5dc0824794` during Change #76, whose prototype boundary runs no eval.

## Two tag-validity assertions rest on one case each under a 0.85 threshold

The assertions for a bare mechanism tag on a compliance-type rule and for a
universal claim tagged `scenario` each map to exactly one case
(`compliance-type-bare-mechanism-tag-rejected`,
`universal-scenario-tag-rejected`) in a seven-case suite whose threshold is
0.85; 6/7 = 0.857 passes the suite, so either assertion can be unfulfilled while
the suite passes. `history.jsonl` records sixteen rows with 6 of 7 passing and
`passed: true`.

**Settlement condition**: each of the two assertions is backed by more than one
case, or the suite threshold requires its case.

**Evidence**: `spec-tree:eval-evidence-auditor` finding `f-004` on head `a65659114b99767b90b4d920550fff5dc0824794`
during Change #76.

## `audit-adr` Failure 2 names the `/test` router that Step 5 forbids invoking

`src/plugins/spec-tree/skills/audit-adr/SKILL.md:184` (Failure 2) says Step 5
verifies the assertion type "per the `/test` router" and rejects "any type the
router would not produce", while Step 5 at line 103 applies the
`spec-tree:test-evidence-standards` assertion-type litmus and forbids invoking
`/test`. The compliance assertion in this node's spec carries the same "per the
`/test` router" wording, so the skill and the spec name the router as the rule's
source while the step names the litmus as its realization.

**Impact**: a reading under which Claude consults or reasons from the mutating
`/test` workflow the constraint on line 103 prohibits.

**Settlement condition**: Failure 2 and Step 5 name one authority for the shape
check, consistent with the assertion in `adr-auditing.md` — the router's selection
rule realized through the `test-evidence-standards` litmus, never an invocation of
`/test`.

**Evidence**: `instructions:skill-auditor` finding rule
`internal_reference_inconsistency`, severity `WARNING`, on head
`524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76.

## `audit-adr` states the language-composition boundary twice

The boundary — this skill owns structure, voice, and tags; the language skill owns
dependency injection, no-mocking, and execution-level accuracy — is stated in full
in `<constraints>` at `src/plugins/spec-tree/skills/audit-adr/SKILL.md:36` and
restated in Step 5b at line 123.

**Impact**: the repeat lengthens the eagerly loaded body and adds no instruction,
failing `/skill-standards` `<conciseness>`'s sentence test.

**Settlement condition**: the boundary appears once, in `<constraints>`, and Step 5b
opens with the classification instruction at line 125.

**Evidence**: `instructions:skill-auditor` finding rule
`duplicated_boundary_statement`, severity `WARNING`, on head
`524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76.
