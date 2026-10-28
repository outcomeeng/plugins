<objective>

The language composition of the test-evidence audit: how linked tests map to installed language plugins, how each language audit's result is validated and merged into the run, and how composed architectural duplication rolls up.

</objective>

<language_skills>

| Language   | Standards skill                        | Audit skill                        |
| ---------- | -------------------------------------- | ---------------------------------- |
| Python     | `python:python-test-standards`         | `python:audit-python-test`         |
| TypeScript | `typescript:typescript-test-standards` | `typescript:audit-typescript-test` |
| Go         | `go:go-test-standards`                 | `go:audit-go-test`                 |
| Rust       | `rust:rust-test-standards`             | `rust:audit-rust-test`             |

</language_skills>

<language_partitions>

Derive language partitions from the linked-test filenames and the installed language plugins. Take the installed language skills from the skill listing already in context; no directory scan is needed.

Read the loaded standards skill's filename instantiation of `<subject>.<evidence>.<level>[.<runner>]` — the concrete pattern the standard states, such as `test_<subject>.<evidence>.<level>[.<runner>].py`. The text after the last closing bracket is the declared suffix: a compound suffix such as `.test.ts` as readily as a bare `.py` or `_test.go`. Map every linked test whose filename ends in an installed plugin's declared suffix to that language. A suffix no installed plugin declares, or an ambiguous partition, is an `unsupported-language` finding with remediation target `language-partition` instead of a guess; never map an extension from a list this skill carries.

</language_partitions>

<language_results>

Validate each language audit's output against that skill's declared verdict contract: output shape, required fields, applicable rows, and agreement between findings, row statuses, and overall status. Malformed or incomplete output is a `language-composition` finding on the language unit of that partition, which stays `incomplete`; continue the remaining languages.

Take each valid result's findings into this run: a composed finding keeps the rule identifier from the rule catalog of the invoked `audit-<lang>-test` skill and is keyed `<unitId>:<that identifier>` on the language unit of the linked test file it concerns. Composed findings sharing a key join into one finding whose `location` lists each of their locations. A composed rejection remains a rejection in the run. When a required `audit-<lang>-test` skill is absent or unavailable, record a `language-composition` finding naming the missing skill, remediation target `skill-installation`, on the language unit of each affected test file, which stays `incomplete`; never approve incomplete coverage.

A language audit returns a third shape when its own scope step finds that every subject it was given is a retired path with no current `[test]` assertion and no current evidence-chain owner: `{"status": "NOT_APPLICABLE", "subjects": [...], "explanation": "..."}`, carrying no rows and no findings. Treat it as neither a pass nor a failure of that language's concerns. Record each reported subject as one `not-applicable` child, compose the remaining languages normally, and decide the terminal status from the units that do exist. When every language in scope returns `NOT_APPLICABLE` and no language-neutral finding was raised, record only the `not-applicable` children, because no evidence was judged.

</language_results>

<architectural_rollup>

Architectural duplication is a composed-language concern. It applies when at least one language-specific verdict returns a `gate-2-architectural` row. Record each of its findings on the language unit of the test file it names, preserving each finding's language-specific rule and extraction target in its message, and joining findings that share a key.

- Treat a malformed or unevaluated applicable architectural row as `language-composition` evidence on that language unit; never infer architectural approval.
- Record nothing for a language whose verdict omits the row, as non-applicable or because that language's Gate 1 rejected the evidence, so its Gate 2 never ran.

</architectural_rollup>
