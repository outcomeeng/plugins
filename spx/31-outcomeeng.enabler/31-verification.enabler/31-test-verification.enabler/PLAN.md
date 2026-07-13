# Plan: test evidence design gates

## Program outcome

Test authoring chooses the evidence architecture before writing an assertion
file. Every path records whether the assertion needs a source contract, an
independent oracle, a harness, a variable generator, or an inert whole-payload
fixture. Open or composable input spaces default to generated or property-based
evidence with reproducible replay. A fixture requires an operator decision
because choosing a deterministic payload deliberately gives up state-space
coverage.

The gate applies before file mutation. A fixture request states:

- why the complete payload shape is material to the asserted behavior;
- why a variable generator or property test is infeasible or wasteful;
- which state-space coverage the fixture gives up;
- which harness owns setup, cleanup, seed policy, replay, and diagnostics;
- the recommended generator or property-evidence alternative;
- a structured operator choice between that recommendation, approving the
  fixture exception, and pausing to inspect the evidence design.

Approval is scoped to the named assertion and payload role. It does not approve
fixture modules, constant bags, copied protocol values, expected-output files,
or a fixture used as a finite substitute for an open domain.

## Slice 1: Python authoring and audit gate

### Demonstrable value

An operator invoking `/test` or `/apply` for a Python node sees the proposed
evidence architecture before any test file is written. The workflow proceeds
autonomously when source contracts, harnesses, and generators provide the
strongest tractable evidence. A proposed inert fixture pauses for an explicit
operator decision with the coverage trade-off visible. The dispatched test
evidence audit rejects evidence whose infrastructure selection, oracle, domain
variation, replay path, or fixture suitability cannot be established from the
evidence chain. `/apply` passes the evidence-design packet and fixture decision
into its audit handoff; the auditor reconstructs the evidence judgment
independently and never treats the authoring packet as proof that the evidence
is strong.

### Existing node set

- `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler`
  owns the methodology rule and fixture-approval boundary.
- `spx/21-spec-tree.enabler/35-evidence.enabler` owns the foundational `/test`
  evidence-design gate.
- `spx/21-spec-tree.enabler/65-apply.enabler` ensures `/apply` reaches the same
  gate before its language-specific test-writing step.
- `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler` owns the
  adversarial audit checks and complete first-pass finding sweep.
- `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler`
  owns the Python expression in `/python-test-standards`, `/test-python`, and
  `/audit-python-tests`.

### Observable path

- **Actor:** an implementation agent with an operator supervising test design.
- **Invocation:** `/test <python-node>` directly, or `/apply <python-node>`.
- **Input:** the contextualized assertion, source contracts, implementation
  surface, and any proposed test-infrastructure artifacts.
- **Behavior:** emit one evidence-design row per assertion before edits. Each row
  names the quantifier and domain, independent oracle, a concrete
  pass-while-assertion-fails counterexample, execution level, source-contract
  needs, harness needs, generator needs, and fixture status. Stop on a missing
  oracle, constant-only generator, absent replay harness, or unapproved fixture.
- **Externalized result:** the evidence-design packet and any structured fixture
  decision remain visible in the active workflow before test files are created.
- **Inspection:** the operator reads the packet and approval rationale; the
  test-evidence auditor returns all applicable evidence-design findings in its
  first verdict rather than revealing avoidable classes across retries.
- **First useful failures:** `missing-independent-oracle`,
  `missing-replay-harness`, `insufficient-domain-variation`,
  `fixture-not-whole-payload`, and, at the authoring gate,
  `fixture-approval-missing`.

### Verification constraints

- Exercise direct `/test` and `/apply` entry paths; the latter cannot bypass the
  foundational determination by delegating directly to Python test writing.
- Cover at least an open-domain property, a finite source-owned mapping, a real
  whole-payload fixture candidate, a constant-only generator, and a circular
  oracle whose expected value comes from the implementation under test.
- Require the audit to inspect the full evidence chain and report every
  observable defect class in one pass over the supplied subject.
- Run focused spec tests or evals selected by the aligned assertions, then
  `just build-skills`, `just check-skills`, `just docs-check`,
  `spx validation markdown`, and `spx spec status --format json`.
- Gate changed skill content through the instructions-owned skill auditor. Gate
  test evidence through `test-evidence-auditor`, implementation through
  `implementation-auditor`, and the cross-node changeset through
  `changes-reviewer` before the repository's terminal deterministic bundle and
  `/merge`.

## Later slices

### Slice 2: TypeScript parity

Carry the Slice 1 evidence-design contract into the TypeScript test-writing,
test-standard, and test-audit surfaces. Preserve the packet fields and fixture
approval semantics so the generic audit can compare languages without
language-shaped exceptions. Use `fast-check` generators and the TypeScript
test-infrastructure home declared by the governing decision.

### Slice 3: Rust parity

Carry the same contract into the Rust test-writing, test-standard, and
test-audit surfaces. Preserve replay data and variable-domain semantics through
`proptest`, with fixtures remaining inert files in the Rust testing crate.

### Slice 4: Cross-language regression corpus

Add a maintained adversarial corpus covering circular oracles, incomplete
finite mappings, provider-scope bleed, positive-only schema checks,
parse-before-side-effect ordering, constant generators, fixture laundering, and
architecture concerns misrouted as test concerns. The corpus verifies that the
authoring packet predicts the audit's evidence properties and that the first
audit verdict reports every defect visible in the original subject.

### Slice 5: Workflow convergence policy

Use the regression corpus to tighten `/apply`'s transition into the gating test
audit: repeat the audit contract immediately before dispatch, require the
evidence-design packet as handoff context, and treat repeated findings in one
design area as a signal to revise the evidence architecture before consuming
another retry. Keep the auditor isolated and authoritative; the authoring
workflow prepares a complete subject rather than pre-judging the verdict.

## Current-interface constraints

- The evidence-design packet stays language-neutral; language skills add only
  implementation syntax and normative infrastructure paths.
- Fixture approval uses the runtime's structured-question surface and remains
  an operator decision. A skill never silently downgrades a generator or
  property claim to deterministic examples.
- Approval does not turn a fixture into a stronger assertion type. The audit
  still judges coupling, falsifiability, alignment, coverage, source ownership,
  domain variation, oracle independence, cleanup safety, and replayability.
- Test files remain typed assertion files. Harnesses, generators, and inert
  fixtures remain spec-governed infrastructure outside `spx/` and outside every
  `tests/` directory.
- Later language slices preserve the same packet fields and failure vocabulary
  so generic `/test`, `/apply`, and `/audit-tests` orchestration stays portable.
