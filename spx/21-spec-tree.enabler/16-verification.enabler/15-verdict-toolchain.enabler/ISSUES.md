# Issues: Verification run payload validation

The audit verification contract harness duplicates SPX-owned protocol vocabulary and must move to captured whole-payload fixtures after the new auditor agents ship and receive runtime smoke testing.

## Hard-coded SPX contract vocabulary

`outcomeeng_testing/harnesses/audit_verification_run_contract.py` manually constructs audit inputs, scope evidence, finding evidence, command arguments, and projection assertions. It repeats field names and values owned by the SPX verification contract, including `unitId`, `coverageRequirement`, `producerProvenance`, `runToken`, and `terminalStatus`.

This conflicts with the Python test standards:

- Production and protocol vocabulary comes from its owning source.
- Container keys are vocabulary and are not hand-written test cases.
- Moving copied values into harness constants does not establish ownership.
- A production module created only to supply tests is not an acceptable source contract.

The harness currently combines three value classes:

1. SPX-owned CLI, payload, enum, and projection vocabulary copied from the published verification-run behavior.
2. Plugin-owned agent, skill, plugin, manifest, and retired-artifact names governed by this repository.
3. Test-authored values such as `file.txt`, example findings, commit messages, and idempotency keys.

The live SPX probe also couples deterministic repository evidence to an installed external executable. Its assertions repeat SPX response fields and make the test responsible for an external contract that this repository does not own.

## Deferred fixture-backed replacement

Capture one canonical audit verification run from the supported published SPX release as inert whole-payload JSON fixtures. Preserve the exact input and output for start, scope add, finding add, finish, and render, together with provenance that records the SPX version, capture source, exact commands, fixture format version, and volatile values.

The replacement follows these boundaries:

- Fixtures own complete external payloads and outputs; Python reads them as whole files.
- Repository conformance tests retain only positive repository-owned assertions: SPX version floor, CI pin compatibility, wrapper identity, and language concern-skill trios.
- Deterministic tests do not claim that captured output proves the currently installed SPX executable accepts the payload.
- Agentic audit or producer-coupled eval evidence owns payload construction and projection interpretation behavior.
- Fixture refresh occurs only for a newly supported SPX release or changed audit contract and replaces the complete capture with updated provenance.
- Individual fixture fields are never edited to satisfy a repository test.

Suggested fixture surface:

```text
outcomeeng_testing/fixtures/audit_verification_run/
|-- provenance.json
|-- start-input.json
|-- start-output.json
|-- scope-input.json
|-- scope-output.json
|-- finding-input.json
|-- finding-output.json
|-- finish-output.json
`-- render-output.json
```

## Evidence correction

The assertion that a fixture-backed Python test proves live SPX acceptance must be removed or reclassified when this issue is implemented. Fixture integrity can prove that captured records are present and valid whole JSON payloads. Current executable acceptance requires a live contract check, while auditor payload reasoning and projection handling require audit or eval evidence.

## Revisit condition

Address this issue after the `implementation-auditor` wrapper and language concern skills have shipped and completed representative runtime smoke audits. Before adding further deterministic verification-run assertions or extending `outcomeeng_testing/harnesses/audit_verification_run_contract.py`, implement the fixture-backed boundary, correct the governing evidence claims, and run the Python test-evidence audit over the replacement.
