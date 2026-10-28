<objective>

The coupling taxonomy of the test-evidence audit: the category and rule identifier for each way a linked test can relate to the code it claims to exercise.

</objective>

<taxonomy>

| Category           | Definition                                                                                        | Verdict                                    |
| ------------------ | ------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| Direct             | Test imports the module under test                                                                | Proceed                                    |
| Indirect           | Test imports a harness wrapping the module                                                        | Proceed — verify harness has real coupling |
| Transitive         | Test imports a consumer of the module                                                             | Proceed — verify test level matches        |
| Laundered indirect | Imports a test-infrastructure module that exists only to expose hardcoded values back to the test | Rule `laundered-coupling`                  |
| False              | Imports module but never calls assertion-relevant functions                                       | Rule `false-coupling`                      |
| Partial            | Calls functions but on wrong inputs or wrong code paths                                           | Rule `partial-coupling`                    |
| None               | Test imports only its test framework                                                              | Rule `no-coupling` (tautology)             |
| Severed            | Imports the module under test and replaces its behavior with a mock, fake, stub, or monkeypatch   | Rule `severed-coupling`                    |
| Prose-coupling     | Reads an authored prose/doc body and asserts its content                                          | Rule `prose-coupling`                      |

</taxonomy>

<prose_coupling>

Coupling means exercising executable **behavior**, never reading a document's content. A test whose "subject" is an authored prose or documentation artifact — a skill body, a spec body, a prompt, any text the product authors and maintains — that the test reads and asserts substrings of is NOT behavioral coupling, even when that artifact is the thing the assertion names. The text passes whatever it literally contains; no code runs. This holds full-chain: a harness that exposes the authored path as a constant, or a reader function that performs the read inside test infrastructure, does not convert a prose assertion into behavioral coupling — follow the read to its source and classify by what is ultimately exercised.

**A test whose evidence is reading an authored prose or documentation body and asserting on its content is a `prose-coupling` finding.** The claim verifies that prose was authored, not that code behaves; its verification type belongs in `[eval]` (a graded judgment over a producer's structured verdict) or `[audit]` (a semantic constraint), and the spec assertion is retagged accordingly. Reading an authored *source-code* file for a structural lint that exercises a rule is not prose-coupling; the discriminator is whether the subject is authored prose/documentation or executable behavior.

</prose_coupling>
