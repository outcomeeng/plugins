# Code Review Instructions

Cover, in this order:

1. Correctness: absolute consistency between what the spec asserts, what tests and evals verify, and what code does
2. Security: confidentiality, integrity, availability
3. Validation of spec, test and code quality: violation of standards (CLAUDE.md and skills)
4. Test evidence: inadequate coverage of all assertions, unmaintainable tests (literals, magic numbers, test-owned constants, duplication)
5. Architecture: violation of ADR and skill governance and fundamental architectural principles

| Class          | Receiver action             | Use when                                                                                                                                                                                           |
| -------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BLOCKING`     | Fix in this PR before merge | Correctness (spec–test–code equivalence and adherence to PDRs and ADRs), security risk, violation of standards (CLAUDE.md and skills), insufficient test evidence or drift risk in tests and evals |
| `NEEDS-ANSWER` | Answer before merge         | A required fact is missing and the answer can clear the concern or upgrade it to `BLOCKING`                                                                                                        |
| `FOLLOW-UP`    | Track outside this PR       | Justified concern, gap or material improvement, but addressing it would widen the PR: architectural deficiencies in need of wider refactoring, technical debt                                      |

Do not use `P0`/`P1`/`P2`/`P3` or `critical`/`high`/`medium`/`low`/`minor`/`nit` as finding headings.

Finding shape:

```text
### BLOCKING [correctness]: path/to/file.py:42
Evidence: <quote the diff or behavior and explain the failure mode>.
Required before merge: <concrete change>.
```

```text
### NEEDS-ANSWER [test-harness]: path/to/spec-file.md:97
Reference: <quote the spec, test or implementation code and justify why the question needs to be answered before merge>.
Question: <concrete question to answer before merge: >.
```

```text
### FOLLOW-UP [test-evidence]: `path/to/foo.compliance.test.ts`
Issue: <what is missing or worthy of improvement>.
Track under: <ISSUES.md file or product-specific issue tracker>.
```

If the diff has no `BLOCKING` or `NEEDS-ANSWER` findings, say so directly in the comment. Do not invent lower-priority findings to prove the review happened.
