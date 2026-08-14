---
name: test-evidence-standards
user-invocable: false
description: >-
  Test-evidence seam, case-provenance, oracle-independence, execution-level, and per-assertion-type artifact-permission standards enforced across test authoring and auditing. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The shared test-evidence standards that keep predicates in linked tests, cases independent from the implementation they verify, and every test file's evidence inside the artifact permissions of its assertion type at its execution level.
</objective>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/test-evidence.md` at the repository root. Read that file after this reference if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth, and it never weakens a seam, provenance, oracle, level, or permission rule this reference states.
</repo_local_overlay>

<execution_levels>

Execution level measures execution pain and environment dependence. It is an axis independent of assertion type and of tooling.

- `l1` — deterministic local evidence: pure logic, cheap temporary filesystem work, standard repository-required tools and subprocesses, and dependency-injected controlled implementations under a recorded exception case.
- `l2` — real local infrastructure: local services, containers, browsers against local services, product-specific binaries, and other heavier local dependencies.
- `l3` — remote, shared, credentialed, or network-dependent systems, selected only when equivalent evidence cannot be produced with local real infrastructure.

Three rules govern level selection:

1. Evidence uses the lowest level that proves the assertion.
2. A runner, framework, resource name, or implementation layer never determines the level; dependency class does.
3. A case's level floor is the heaviest dependency class among the behavior under test, the oracle, and the enforcement mechanism.

**Executable discriminator.** One ordered discriminator classifies the exact executable the evidence exercises — behavior, oracle, or enforcement mechanism alike — and its two steps are disjoint:

1. **An artifact of the product under test:** `l1` when the suite exercises the form the checkout carries — the binary the declared toolchain builds within the ordinary deterministic test cycle, that build's own cache-restored output among its forms, or a product artifact executed directly from the checkout, executable source scripts among them; `l2` for every other acquired form of the product's artifact — installed, bootstrapped, preinstalled, downloaded, copied, mounted, restored from a cache outside the ordinary build, or otherwise obtained. The two arms are a complement pair over acquisition provenance, so environment supply never reclassifies the product's own artifact as repository-standard.
2. **Every other executable:** `l1` when the declared development environment supplies it or the declared toolchain produces it in-cycle; `l2` when obtaining it requires installation, bootstrap, download, or a service lifecycle outside that cycle.

In both steps the level floor stays `l3` where the evidence run itself must reach a remote, shared, credentialed, or network-dependent system to obtain or exercise the executable; acquisition completed before the ordinary test cycle — a bootstrap download among its forms — keeps the acquired-form classification above.

**Harness obligations follow the level, identically for every assertion type:** at `l1`, framework resource handles and standard-subprocess harnesses suffice; at `l2`, a harness owns the lifecycle — start, health, teardown — of each heavy local dependency; at `l3`, credential, isolation, and cleanup harnesses are required.

**Unavailable required evidence never passes:** a missing mandatory credential, endpoint, binary, or local service fails loudly, or skips only where the suite declares that evidence optional.

**Controlled-implementation relief.** A controlled implementation enters evidence only under the test methodology's exception set — the seven named cases from failure simulation through contract probes, declared by the generic test workflow that both authoring and auditing load — and the evidence names the matching case. The combinatorial-cost exception is that set's member for broad evidence a real dependency makes prohibitively expensive.

**Cell composition.** Every assertion type × execution level cell is decided by composition: the type's artifact rules in `<type_level_permissions>` hold at every level unchanged, and the level contributes only the harness obligations, the level floor, the availability rule, and the controlled-implementation relief above, identically for every type. A per-type per-level delta exists only where the type changes the answer. A permission undecidable from this composition is an amendment to the product's governing evidence decision, never an author's or auditor's inference.

**Filename declaration.** The canonical filename model `<subject>.<evidence>.<level>[.<runner>]` declares each executed test file's cell: exactly one assertion type and exactly one execution level per file, with a runner token only for a non-default runner. The product's language test standard declares the language's filename instantiation and the default runner an omitted runner token names — or the deterministic rule, including any repository override, by which that default is derived; the instantiation is expression and changes no token semantics.

</execution_levels>

<artifact_ownership>

Each artifact category has its own valid transfer out of the test file: a harness acquires execution policy, a generator acquires domain construction, a fixture acquires an inert whole payload, production acquires a real product contract, and the linked test retains the cases and the verdict its assertion type requires. Value movement is judged on the finished artifact by the checks this reference owns — semantic binding ownership, predicate inversion, oracle independence, production mutation — never by diffing an extraction.

**Two probes decide whether a value is cross-assertion (harness-owned) or the assertion's own (stays at the call site).** A value belongs to the harness only when it survives both:

- *Negation* — state the assertion's opposite. Does the value change? A thirty-second timeout is thirty seconds whether the operation must succeed or must fail.
- *Transplant* — put the test in an unrelated product. Does the value change? Temporary-directory lifecycle is identical in a parser and in a payment gateway.

Neither probe stands alone. An input survives negation — same input, flipped expectation — so negation alone launders every case. A generic expected string such as `"timeout exceeded"` survives transplant, so transplant alone launders expectations.

Cross-assertion, by example: temporary-directory creation and removal, working directory, environment reset, clock control, seed, run count, shrink budget, timeout, deadline, subprocess launch and teardown, port allocation, output capture, state reset between cases, fixture-root resolution, teardown ordering.

The assertion's own, by example: the input, the expected output, the domain's boundaries, the oracle, the identity of the error.

The only test shape holding nothing from the cross-assertion list is a function called with values, returning a value, compared in place. Touch the filesystem, a process, the clock, the network, or randomness and the test has acquired a value the spec does not contain and the assertion cannot own — so a harness exists, and the test receives only its handles and observations. A cross-assertion value never enters the test as a call-site literal; a call-site value is valid only when the two probes classify it as the assertion's own.

**The first test in a node pays for the harness every later test uses.** The first test is the one with the least reason to build a harness and the most influence on what follows: reusable setup policy it hand-rolls inline becomes the template later tests copy. Build the harness at the first test that needs one.

</artifact_ownership>

<predicate_seam>

The linked executed test function or callback owns every behavioral predicate and every assertion API call. A harness may establish context, manage resources, execute behavior, and pass observations or handles to the test. A harness, generator, fixture, controlled implementation, or recording collaborator NEVER:

- calls `assert`, `expect`, a matcher, or an assertion helper
- accepts the expected outcome as an input
- returns pass/fail, valid/invalid, success/failure, or another verdict
- exposes verdict-shaped methods such as `*_succeeds`, `is_valid`, `was_called_with`, or `assert_called`
- catches a product failure merely to convert it into a boolean test result

Controlled implementations and recording collaborators implement the real dependency boundary and expose observations. They preserve behavior-relevant state instead of replacing the asserted behavior. The linked test decides what each observation means.

</predicate_seam>

<semantic_binding_ownership>

Judge a binding by what it chooses, never by syntax alone.

Allowed bindings receive or rename values chosen by an owning source:

- an imported source contract, enum member, schema, registry, or constructor result
- a generated value supplied by a generator
- a resource handle, callback input, or observation supplied by a harness
- a fixture path supplied by an inert-fixture path provider
- the actual result returned by the behavior under test

An allowed binding introduces no domain member, case, expected result, setup policy, runner configuration, or verdict rule.

Rejected bindings choose data or policy inside the assertion file:

- hand-picked inputs, boundary bags, parametrize rows, payload members, or fixture contents
- expected outputs or expected interaction verdicts
- property seeds, run counts, retries, timeouts, or replay policy
- generator domains or source vocabulary copied into the test
- reusable setup, lifecycle, cleanup, or dependency policy
- helper functions whose return value decides whether the assertion passes

The rejected rows above are examples, not the boundary: for a concern no row names — port allocation, clock control, state reset between cases, teardown ordering — apply the two probes in `<artifact_ownership>` to decide whether it is cross-assertion policy the harness owns or the assertion's own value that stays at the call site.

Fixture parameters, generated parameters, destructuring, aliases, local variables, and constants can be valid or invalid. Their semantic ownership decides.

A framework-provided temporary-directory handle, a local that receives a harness observation, and a projection written directly inside the linked assertion are valid because they choose no data or policy. NEVER reject a binding because it is local syntax or require moving an observation alias into infrastructure; that move can obscure the predicate seam without changing ownership.

</semantic_binding_ownership>

<case_provenance_and_oracles>

Every case names a source independent of the implementation author’s invention. Every expected result comes from an oracle independent of the production path under test. Reading the implementation and selecting a case because it passes creates a shared-model tautology.

Ask for every input and expectation:

1. Which spec sentence, source-owned domain, generator, external oracle, governing rule, or real whole-payload artifact selected this case?
2. Could the implementation author have chosen it because the current code handles it?
3. Does the expected result reuse the same table, algorithm, parser, branch logic, acceptance predicate, or collaborator verdict method as production?
4. Would an independent implementation receive the same case and oracle?
5. Does the case source match the assertion’s quantifier?

Construction-derived expectations are valid only when the construction law is independent from the code under test. A generator may carry that law when production does not reuse it. Independence from the production path is necessary and not sufficient: the law itself traces to a source outside the author's invention — the governing spec's declared relationship, a source-owned contract, or a separately owned oracle — because a law authored from the same model as the production algorithm is a second implementation, not an oracle.

</case_provenance_and_oracles>

<type_level_permissions>

The artifact set each assertion type permits and requires, per level where the type changes the answer. Each section composes with `<execution_levels>` — the level adds harness obligations, floor, and availability identically for every type — and defers case-source and oracle authority to `<assertion_type_litmus>`.

**Scenario.** The case is the exact interaction the governing spec declares, or a real whole-payload artifact whose complete shape is the case, read by path and never imported. The case literal is correct at the test site; incidental values only the test needs come from generators over variable domains or from harness handles. At `l1` the test calls the production API directly or drives a repository-standard binary — one the declared environment supplies or the declared toolchain builds within the ordinary test cycle, the product's own in-cycle checkout build among them — through a standard-subprocess harness; at `l2` the same interaction runs against a product-specific binary acquired outside that cycle — installed, bootstrapped, or otherwise obtained per the executable discriminator — and the level moves because the dependency class moved, not because a subprocess is involved; at `l3` a credentialed end-to-end interaction runs through credential, isolation, and cleanup harnesses and remains one existential case. A cheap temporary-file scenario never promotes to `l2` for touching the filesystem. A universal claim is never scenario evidence, however large the example bag.

**Mapping.** The domain is the complete finite source-owned enumeration — imported from its owning registry, enum, schema, or typed factory — or a generated finite domain. Expected mappings derive from an independent construction law that may live inline in the linked test, in a spec-governed generator, or in an independent oracle module; independence is measured against the production path, not by location, and the law traces to a source outside the author's invention per `<case_provenance_and_oracles>`. Hand-written per-row expected values choose data and are rejected; a derivation from a provenance-bearing independent law is not a choice. Completeness holds at every level: cost pressure routes to the combinatorial-cost exception or to a lower level, never to sampling. A mapping exercised through a product-binary harness classifies `l2` when the binary is an installed or bootstrapped artifact per the executable discriminator; the same mapping against the in-cycle checkout build classifies `l1`. One example is never a mapping — a single case is a quantifier mismatch.

**Conformance.** The oracle is separately owned from the implementation under test: an external standard, schema, validator tool, reference implementation, or separately owned internal contract. Expectations come from the oracle; neither test nor infrastructure re-implements the oracle's logic, and the case set covers the contract surface the assertion claims. The discriminator in `<execution_levels>` classifies the oracle tool: a repository-standard validator or compiler is `l1` (a compile-fail harness passing a violating source fixture by path is the canonical shape), a product-specific installed or bootstrapped validator is `l2`, and a remote reference implementation reached through credentialed harnesses is `l3`, selected by necessity. A spec-declared value and the source complying with it admit no conformance evidence: every candidate oracle for that agreement is a second declaration of the same value, so the agreement is audit evidence, not test evidence.

**Property.** The case set comes from a generator over the declared open domain with meaningful variation, composition, and shrinking; the invariant stays lexically in the linked test; a spec-governed harness owns seed selection, run count, replay input, and failure diagnostics, and a failing run is reproducible from its reported evidence. Property evidence is permitted at every level — the absence of a level restriction is decided, not overlooked; the lowest-level rule and the combinatorial-cost exception govern property cost at heavier levels. A constant boundary branch inside a larger generator is valid when it expands boundary coverage and every source-owned value is imported from its owner; a generator that is a constant-only wrapper of a source-owned singleton is not a generator. A generator never filters candidates through the production acceptance predicate, and property-framework syntax around one example is scenario evidence impersonating property.

**Compliance.** The evidence exercises real violating input: a whole-payload fixture passed by path — a source artifact that violates the rule — never a fixture exporting violating tokens. At least one real violating case is present, and disabling or weakening the enforcement makes the linked test fail; conforming cases alongside the violating ones prove no false positive. Detection is the test's subject; pipeline registration is separate operational evidence, so a green validation-pipeline run proves nothing about detection. Enforcement shipped in a product-specific binary — an installed or bootstrapped artifact per the executable discriminator — classifies `l2`; the same enforcement exercised through the in-cycle checkout build classifies `l1`. A complete finite source-owned invalid set is a mapping, not compliance — the correspondence's quantifier decides.

</type_level_permissions>

<common_litmus_questions>

Apply every question while authoring and auditing:

1. Holding arrangement and execution fixed, if the assertion changes to its opposite, can only the linked test predicate change? A harness change means the harness encodes the assertion.
2. Can a reader understand the complete pass/fail predicate from the linked test alone?
3. Does infrastructure return observations and handles rather than verdicts?
4. Does failure report actual and expected observations at the linked assertion site rather than only `assert helper()` or an equivalent wrapper?
5. Can the same harness support two tests making opposite claims about the same observation?
6. Does infrastructure raise only setup, dependency, lifecycle, or execution errors rather than assertion failures?
7. Does mutating the assertion-relevant production behavior make the test fail?
8. What semantic choice does each test-file binding make? If it only receives or projects an owned observation or handle, rejecting it is syntax-based rather than ownership-based.

</common_litmus_questions>

<assertion_type_litmus>

| Assertion type | Required source and oracle                                                                                             | Reject when                                                                                            |
| -------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Scenario       | The exact Given/When/Then interaction from the spec, or a real whole-payload artifact whose complete shape is the case | The case is one member of an author-invented “typical” or “edge” bag                                   |
| Mapping        | The complete finite source-owned domain; expected mappings derive independently from the production mapping            | Rows are hand-extended, incomplete, or copied from the implementation table                            |
| Property       | A generator over the declared open domain; the invariant remains in the linked test                                    | The generator reuses the production acceptance predicate, collapses to examples, or owns the predicate |
| Conformance    | An external standard, schema, validator, reference implementation, or separately owned contract                        | The implementation validates itself or the oracle is another copy of its logic                         |
| Compliance     | The governing ALWAYS/NEVER rule plus real violating cases                                                              | Evidence uses only conforming cases or still passes when enforcement is disabled                       |

For every type, ask whether the selected cases cover the quantifier the assertion states. A universal claim never becomes scenario evidence through a larger example bag.

</assertion_type_litmus>

<mutation_litmus>

Use three mental or executable mutations:

1. Invert the linked predicate. Only the linked test changes; infrastructure remains reusable.
2. Mutate or disable the assertion-relevant production behavior. The evidence fails.
3. Replace the independent expected result with its opposite. Only the linked test predicate or independently owned oracle changes.

A seam that fails mutation 1 launders the assertion into infrastructure. Evidence that survives mutation 2 lacks falsifiability or coverage. An oracle that fails mutation 3 is coupled to production or hidden behind a verdict helper.

</mutation_litmus>

<language_deltas>

Language test standards are expression only. A language test standard cites its product's governing evidence decision by full path, and realizes every source and artifact category this reference permits in its language's terms — assertion API, binding forms, generator libraries, test-infrastructure home, runner specifics, and the filename instantiation of the canonical model — and it neither narrows nor widens the category set or any seam, provenance, oracle, level, or permission rule stated here. A category a language cannot realize is surfaced as an amendment to the product's governing evidence decision, which records the exception centrally, never as a silent per-language subtraction.

</language_deltas>

<success_criteria>

- Every behavioral predicate and assertion API call is lexically visible in the linked executed test function or callback.
- Test-file bindings introduce no independently chosen data, expectations, setup policy, runner configuration, or verdict rules, with unlisted concerns decided by the two probes in `<artifact_ownership>`.
- Every case and expected result has assertion-type-appropriate provenance independent of the implementation path under test.
- Every executed test file declares exactly one assertion type and one execution level through the canonical filename model, and its evidence satisfies that cell's permissions in `<type_level_permissions>` composed with `<execution_levels>`.
- Execution level derives from dependency class alone, floored by the heaviest dependency among behavior, oracle, and enforcement mechanism.
- Controlled implementations and recording collaborators preserve the real boundary and expose observations only.
- Predicate inversion changes only the linked test, and production mutation makes the evidence fail.

</success_criteria>
