# Plan: generic full-chain test auditing

The next slice makes the language-neutral test-evidence auditor reject an
evidence chain whose imported test infrastructure owns unsourced protocol
vocabulary, and identify the exact transitive artifact that breaks source
ownership.

## Observable path

**Actor:** An operator dispatches `test-evidence-auditor` for a spec assertion
whose linked non-Python test imports a test-infrastructure module.

**Invocation:** The caller supplies the governing node, assertion text or
heading, linked test path, declared language partition, and deterministic
verification state through the existing `test-evidence-auditor` request.

**Input:** A curated non-Python evidence chain contains a thin executed test and
an imported test-infrastructure module with hand-authored protocol keys, command
tokens, paths, expected values, or payload members. A paired conforming chain
sources its vocabulary correctly.

**Behavior:** `test-evidence-auditor` enumerates the linked test and every
imported harness, generator, fixture reference, and applicable test-discovery
artifact before judgment. The generic `spec-tree:audit-tests` workflow applies
an ownership screen to each artifact, records the provenance of every case and
protocol value, and refuses approval when an artifact or value remains
uninspected or unclassified.

**Result:** The existing structured test-audit verdict returns `REJECTED` for
the violating chain. Its finding names the imported artifact, import path,
failed evidence property, unsourced value class, and required ownership target.
The conforming chain returns `APPROVED` when all generic evidence properties and
required language composition complete.

**Inspection surface:** The operator reads the structured verdict returned by
`test-evidence-auditor`. Behavioral eval history records whether the real audit
prompt rejects the violating chain and approves the conforming chain.

## Slice boundary

**Demonstrable value:** A dispatched test-evidence auditor rejects a non-Python
evidence chain when imported test infrastructure owns unsourced protocol
vocabulary, and its structured verdict identifies the transitive artifact and
required ownership target.

**Ordered node set:**

1. `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler`

The node delivers the language-neutral wrapper contract, generic audit
methodology, and generic behavioral evidence as one observable path. The slice
does not change `audit-python-tests`, `audit-typescript-tests`,
`audit-rust-tests`, or any language test standards. Its non-Python eval case
proves generic traversal and ownership behavior without using the Python audit
skill as its subject.

## Required behavior

1. The wrapper requires a complete evidence-chain inventory before verdict
   emission.
2. The generic workflow follows imports from the linked test into harnesses,
   generators, fixture providers, and applicable discovery configuration.
3. Every inspected artifact receives an ownership classification and every case
   or protocol value receives a named provenance source.
4. Missing artifacts, incomplete traversal, unavailable required language
   composition, and unclassified values produce a failing row and `REJECTED`.
5. Imported infrastructure receives the same source-ownership scrutiny as the
   executed test while retaining category-specific lifecycle checks.
6. Findings identify the transitive artifact and import chain rather than
   attributing every defect to the thin test file.

## Failure behavior

- **Unread transitive artifact:** Reject with an incomplete-evidence-chain
  finding naming the unresolved import.
- **Unsourced protocol vocabulary:** Reject with a source-ownership finding
  naming the artifact, value class, and required owner.
- **Missing provenance classification:** Reject instead of inferring that a
  harness owns the value.
- **Unavailable required language concern:** Reject with a coverage-gap finding;
  generic approval cannot hide missing composed coverage.
- **Malformed audit request:** Reject with the missing request field before
  evidence judgment.

## Verification

- Add producer-coupled eval cases for one violating and one conforming
  non-Python evidence chain. The grader consumes the structured verdict and
  checks terminal outcome, finding rule, and transitive artifact path.
- Run the focused eval with the repository's default budget and preserve its
  history through the eval workflow.
- Run `just build-skills`, `just check-skills`, `just docs-check`,
  `spx validation markdown`, and `spx spec status --format json`.
- Dispatch `skill-auditor` for the changed skill and reference content,
  `subagent-auditor` for the wrapper, `eval-evidence-auditor` for the new eval,
  and `spec-auditor` for the aligned node assertion.
- Dispatch `changes-reviewer` over the clean committed head, then run
  `just check-full` as the terminal deterministic gate.

## Later slices

- Strengthen `audit-python-tests` with Python-specific harness-body ownership
  rules and a Python adversarial case after this generic contract is stable.
- Apply any language-specific refinements to TypeScript and Rust only when their
  concern skills expose gaps beyond the generic full-chain contract.
- Move artifact-type test-audit persistence to `spx verification run` in the
  already-deferred artifact-auditor migration without changing this slice's
  verdict semantics.
