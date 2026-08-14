# Evidence Cells

Every `[test]` assertion's evidence occupies one cell of a cross-product: its assertion type — scenario, mapping, conformance, property, or compliance — times its execution level — `l1`, `l2`, or `l3`. This decision governs what each cell permits and requires: the neutral execution-level semantics, the artifact set available to each assertion type at each level, the filename declaration of the cell, and the acceptance corpus whose cases bind those boundaries. Language test-standard nodes express these semantics in language terms; they never alter them.

## Execution Levels

Execution level measures execution pain and environment dependence. It is an axis independent of assertion type and of tooling.

- `l1` — deterministic local evidence: pure logic, cheap temporary filesystem work, standard repository-required tools and subprocesses, and dependency-injected controlled implementations under a recorded Stage 5 exception case.
- `l2` — real local infrastructure: local services, containers, browsers against local services, product-specific binaries, and other heavier local dependencies.
- `l3` — remote, shared, credentialed, or network-dependent systems, selected only when equivalent evidence cannot be produced with local real infrastructure.

A controlled implementation enters evidence only under the `/test` methodology's Stage 5 exception set — the seven named cases from failure simulation through contract probes — and the exception is recorded by naming the matching case in the evidence. The Stage 5 combinatorial-cost exception is that set's member for broad evidence a real dependency makes prohibitively expensive.

Three rules govern level selection:

- Evidence uses the lowest level that proves the assertion.
- A runner, framework, or implementation layer never determines the level; dependency class does.
- A case's level floor is the heaviest dependency class among the behavior under test, the oracle, and the enforcement mechanism.

One ordered discriminator classifies the exact executable the evidence exercises, and its two steps are disjoint. First, an artifact of the product under test: `l1` when the suite exercises the form the checkout carries — the binary the declared toolchain builds within the ordinary deterministic test cycle, that build's own cache-restored output among its forms, or a product artifact executed directly from the checkout, executable source scripts among them; `l2` for every other acquired form of the product's artifact — installed, bootstrapped, preinstalled, downloaded, copied, mounted, restored from a cache outside the ordinary build, or otherwise obtained — so the two arms are a complement pair over acquisition provenance, and environment supply never reclassifies the product's own artifact as repository-standard. Second, every other executable: `l1` when the declared development environment supplies it or the declared toolchain produces it in-cycle, `l2` when obtaining it requires installation, bootstrap, download, or a service lifecycle outside that cycle. In both steps the level floor stays `l3` where obtaining or exercising the executable requires a remote, shared, credentialed, or network-dependent system. The same discriminator classifies oracles and enforcement mechanisms.

Harness obligations follow the level's dependency class, identically for every assertion type: at `l1`, framework resource handles and standard-subprocess harnesses suffice; at `l2`, a harness owns the lifecycle — start, health, teardown — of each heavy local dependency; at `l3`, credential, isolation, and cleanup harnesses are required.

Unavailable required evidence never passes: a missing mandatory credential, endpoint, binary, or local service fails loudly, or skips only where the suite declares that evidence optional.

Every cell of the cross-product is decided by composition. An assertion type's section states its artifact rules — case source, oracle, domain, and type-specific artifacts — and those rules hold at every execution level unchanged; the execution level contributes only the harness obligations, the level floor, the availability rule, and the Stage 5 relief above, identically for every type. A per-type section states a per-level delta only where the type changes the answer, as the scenario section's level-paired cases do. A permission undecidable from this composition is an amendment to this decision, never an author's or auditor's inference.

## Test-File Declaration

The canonical filename model `<subject>.<evidence>.<level>[.<runner>]` declares each executed test file's cell: exactly one assertion type and exactly one execution level per file, with a runner token only for a non-default runner. Each language test-standards node declares exactly one filename instantiation of this model as part of its language delta, citing this decision by full path, and declares the default runner an omitted `<runner>` token names — or the deterministic rule, including any repository override, by which that default is derived. The instantiation is expression: it renders the model into the language's file-naming convention and changes no token semantics.

## Scenario

A scenario proves one existential interaction. Its case is the exact interaction the governing spec declares, or a real whole-payload artifact whose complete shape is the case. The case literal is correct at the test site; incidental values only the test needs come from generators over variable domains or from harness handles, per the generated-values and binding assertions in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`.

Valid:

1. `l1` — the spec declares an interaction; the test transcribes it, calls the production API directly, and asserts the declared outcome with the case literal at the call site.
2. `l1` — the case is a complete artifact; an inert fixture is read by path and never imported.
3. `l1` — the interaction writes into a framework-provided temporary directory using a generated incidental filename; neither binding introduces data or policy.
4. `l1` — a command-line interaction runs through a standard-subprocess harness against a repository-standard binary — one the declared environment supplies or the declared toolchain builds within the ordinary test cycle, including the repository's own CLI built in-cycle; the harness exposes exit code and captured output, and the test owns every predicate.
5. `l2` — the same interaction runs against a product-specific binary — one whose installation or bootstrap lies outside that cycle, including the same repository CLI when the claim requires the installed artifact even where the declared environment ships it preinstalled; the level moves because the dependency class moved, not because a subprocess is involved.
6. `l3` — a credentialed end-to-end interaction runs through credential, isolation, and cleanup harnesses and remains one existential case.

Rejected:

7. Several author-invented "representative" inputs parameterized as one scenario — an example bag has no spec-declared case (case-provenance assertions in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`).
8. A universally quantified assertion evidenced by one example — a universal is never a scenario.
9. The scenario's case tuple relocated to a production constant so the test can cite a production address — source laundering (the production-address `NEVER` assertion in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`; the litmus-first assertion in `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md`).
10. A harness method that accepts the expected outcome or returns a verdict — the predicate crossed the seam (the seam assertions in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`).
11. Reusable setup policy hand-rolled inside the test file — test-owned configuration (the binding assertion in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`).
12. The test imports the orchestrator, then replaces its dispatch with a monkeypatch while asserting dispatch behavior — the harness-replacement `NEVER` assertion in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`.
13. A cheap temporary-file scenario promoted to `l2` because it touches the filesystem — the level rules above reject tool- and resource-name promotion.

## Mapping

A mapping proves a correspondence over a complete finite domain. The domain is the complete finite source-owned enumeration — imported from its owning registry, enum, schema, or typed factory — or a generated finite domain. Expected mappings derive independently of the production mapping. Completeness holds at every level: cost pressure routes to the Stage 5 combinatorial-cost exception or to a lower level, never to sampling.

The independent expectation law may live inline in the linked test, in a spec-governed generator, or in an independent oracle module; independence is measured against the production path, not by location. Independence from the production path is necessary and not sufficient: every construction law traces to a source outside the author's invention — the governing spec's declared relationship, a source-owned contract, or a separately owned oracle — because a law authored from the same model as the production algorithm is a second implementation, not an oracle. Hand-written per-row expected values choose data and are rejected; a derivation from a provenance-bearing independent construction law is not a choice.

Valid:

14. `l1` — the domain is imported from a production enum; expectations derive from an independent construction law; the test parameterizes over every member.
15. `l1` — a generated finite domain composes two source-owned option sets; expectations derive per input independently of production.
16. `l2` — every command in a source-owned command registry maps to its dispatch action through a product-binary harness.
17. `l1` — boundary validation over a closed, finite, source-owned invalid set, every member exercised.
18. A broad domain against an expensive real dependency runs through a configurable controlled implementation preserving the boundary, under a recorded Stage 5 combinatorial-cost exception.

Rejected:

19. Rows hand-extended past the source-owned enumeration — the domain is no longer source-owned (source-owned-values assertions in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`).
20. The expected column copied from the implementation's lookup table — a tautology (the evidence-chain rules in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`).
21. The production module's internal table transcribed into the test instead of imported — source ownership copied to the test.
22. One example presented as the mapping — quantifier mismatch.
23. Parameterization rows chosen in the test file rather than imported or generated — test-owned data.
24. The domain sampled at `l3` for cost — completeness is invariant; the exception path above is the only relief.
25. A parallel expectation algorithm written from the author's model of the production mapping — differing from the production path but tracing to no spec-declared relationship, source-owned contract, or separately owned oracle — a second implementation as oracle (the author-invention independence assertions in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`).

## Conformance

A conformance case proves behavior matches a contract whose oracle is separately owned from the implementation under test: an external standard, schema, validator tool, reference implementation, or separately owned internal contract. Expectations come from the oracle; neither test nor infrastructure re-implements the oracle's logic. The case set covers the contract surface the assertion claims.

A spec-declared value and the source complying with it admit no conformance evidence: every candidate oracle for that agreement is a second declaration of the same value and is therefore not separately owned. That agreement is audit evidence.

Valid:

26. `l1` — generated output validated against a separately owned schema by a repository-standard validator — one the declared environment supplies or the declared toolchain builds in-cycle.
27. `l1` — a compile-fail harness passes a violating source fixture by path to the standard compiler; the compiler is the oracle.
28. `l2` — an emitted artifact is validated by a product-specific binary's validator — an installed or bootstrapped artifact per the executable discriminator.
29. `l1` — captured whole-payload protocol fixtures, read by path, validated against the separately owned protocol schema.
30. `l3` — the contract is verified against a remote reference implementation through credentialed harnesses, selected by necessity.

Rejected:

31. The module's own validation routine as the oracle for its own output — self-validation (the evidence-chain oracle rules in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`).
32. A hand-rolled checker in a harness duplicating production parsing logic — the oracle is a copy of the implementation.
33. The expected canonical output produced by the production serializer under test — oracle coupled to the production path (the oracle-independence assertions in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`).
34. A spec-declared token asserted equal between a test constant and the source — a second declaration, not an oracle; the agreement is audit evidence per this section.
35. A conformance claim with no tool, schema, or reference oracle — no conformance evidence exists.

## Property

A property proves an invariant over an open domain. The case set comes from a generator over the declared domain with meaningful variation, composition, and shrinking; the invariant stays lexically in the linked test; a spec-governed harness owns seed selection, run count, replay input, and failure diagnostics, and a failing run is reproducible from its reported evidence.

Property evidence is permitted at every level. The absence of a level restriction is decided, not overlooked: the lowest-level rule and the Stage 5 combinatorial-cost exception govern property cost at heavier levels.

Valid:

36. `l1` — a round-trip invariant over a shrinking generator; the harness owns seed and replay; the invariant sits in the test.
37. `l1` — a constant boundary branch inside a larger generator expands boundary coverage while every source-owned value is imported from its owner.
38. `l1` — expectations derive from a construction law the generator carries, tracing to a spec-declared relationship or source-owned contract, which production does not reuse.
39. `l2` — an invariant over a real local service; the harness owns service lifecycle plus seed and replay.

Rejected:

40. Property-framework syntax around one example — scenario evidence impersonating property (the framework-syntax `NEVER` rule in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`).
41. A generator that is a constant-only wrapper of a source-owned singleton — the constant-only `NEVER` assertion in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`.
42. A generator filtering candidates through the production acceptance predicate — the generator owns the verdict's shape (the acceptance-function rule in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`).
43. Seed or run count set in the test file — test-owned run configuration (the property-harness assertion in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`).
44. Failure output lacking seed and replay path — the failing run is not reproducible from its evidence.
45. The expected output computed by calling the function under test on the generated input — oracle equals the production path.

## Compliance

A compliance case proves a deterministic ALWAYS/NEVER boundary by exercising real violating input. The rule names the violation; the evidence includes at least one real violating case, and disabling or weakening the enforcement makes the linked test fail. A violating input for an enforcement rule is a whole-payload fixture passed by path — a source artifact that violates the rule — never a fixture exporting violating tokens. Detection is the test's subject; pipeline registration is separate operational evidence.

Valid:

46. `l1` — an enforcement rule runs against a violating source fixture by path; the test asserts detection with the rule identifier imported from the rule's registry.
47. `l1` — a NEVER-rule exercised with a real violating input; disabling the enforcement fails the test.
48. `l1` — violating and conforming fixtures together, the conforming cases proving no false positive alongside the required violating cases.
49. `l2` — enforcement shipped in a product-specific binary — an installed or bootstrapped artifact per the executable discriminator — exercised against a violating fixture.

Rejected:

50. Conforming-only evidence — nothing proves the boundary rejects anything (the violating-case rules in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`).
51. A test that still passes with the enforcement disabled — no falsifiability.
52. A fixture file exporting violating token strings — the isolated-strings fixture `NEVER` assertion in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`.
53. Violating cases invented as an author's edge bag rather than derived from the rule's stated boundary — case provenance fails.
54. A complete finite source-owned invalid set written as compliance — that correspondence is a mapping.
55. Detection claimed from a green validation-pipeline run — registration conflated with detection.

## Language Narrowing

Language deltas are expression only. A language test-standards node realizes every source and artifact category this decision permits in its language's terms; it neither narrows nor widens the category set. A category a language cannot realize is surfaced as an amendment to this decision, which records the exception centrally.

## Rationale

Per-type and per-level permission decided once, language-neutrally, is what keeps three language plugins from re-deriving divergent answers — the same drift the superset node exists to remove — and the corpus cases make each boundary concrete enough to compare candidate renderings of the standard against one fixed subject. The rejected alternative, per-language permission tables, re-opens divergence-by-subtraction with no gate that compares siblings.

## Product properties

1. Every executed test file declares exactly one assertion type and one execution level through the canonical filename model, and its evidence satisfies that cell's artifact permissions.
2. Every corpus case in this decision decides acceptance identically in every language rendering; a language delta changes expression, never a verdict.
3. Execution level derives from dependency class alone — the lowest level that proves the assertion, floored by the heaviest dependency among behavior, oracle, and enforcement mechanism.

## Verification

### Audit

- ALWAYS: each executed test file declares exactly one assertion type and one execution level through the canonical filename model `<subject>.<evidence>.<level>[.<runner>]` ([audit])
- ALWAYS: each language test-standards node declares exactly one filename instantiation of the canonical model as part of its language delta, citing this decision by full path, and declares or deterministically derives the default runner an omitted runner token names ([audit])
- ALWAYS: evidence level derives from the heaviest dependency class among the behavior under test, the oracle, and the enforcement mechanism, and evidence uses the lowest level that proves the assertion ([audit])
- NEVER: a runner, framework, resource name, or implementation layer determines an execution level ([audit])
- ALWAYS: evidence for a cell satisfies the artifact permissions this decision states for its assertion type at its execution level ([audit])
- ALWAYS: each corpus case in this decision decides acceptance identically in every language rendering ([audit])
- NEVER: a language test-standards node narrows or widens the source and artifact categories this decision permits — a category a language cannot realize is an amendment to this decision ([audit])
- NEVER: mapping completeness is relaxed by sampling at any level — cost routes to the Stage 5 combinatorial-cost exception or to a lower level ([audit])
- NEVER: unavailable required evidence produces a passing test — a missing mandatory dependency fails loudly or skips only where the suite declares that evidence optional ([audit])
