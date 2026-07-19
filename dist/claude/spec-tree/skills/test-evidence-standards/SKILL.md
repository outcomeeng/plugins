---
name: test-evidence-standards
user-invocable: false
description: >-
  Test-evidence seam, case-provenance, and oracle-independence standards enforced across test authoring and auditing. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The shared test-evidence standards that keep predicates in linked tests and cases independent from the implementation they verify.
</objective>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/test-evidence.md` at the repository root. Read that file after this reference if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth, and it never weakens a seam, provenance, or oracle rule this reference states.
</repo_local_overlay>

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

Construction-derived expectations are valid only when the construction law is independent from the code under test. A generator may carry that law when production does not reuse it.

</case_provenance_and_oracles>

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

<success_criteria>

- Every behavioral predicate and assertion API call is lexically visible in the linked executed test function or callback.
- Test-file bindings introduce no independently chosen data, expectations, setup policy, runner configuration, or verdict rules.
- Every case and expected result has assertion-type-appropriate provenance independent of the implementation path under test.
- Controlled implementations and recording collaborators preserve the real boundary and expose observations only.
- Predicate inversion changes only the linked test, and production mutation makes the evidence fail.

</success_criteria>
