# Evidence Skill Refactoring Plan

The evidence lifecycle is delivered through three dependent pull requests. The complete node structure is declared with the first pull request so every implementation slice loads its final ownership and ordering context.

## Structure

```text
spx/21-spec-tree.enabler/35-evidence.enabler
├── 39-test-skill.enabler
├── 39-eval-skill.enabler
│   └── 21-skill-eval.enabler
└── 69-verify-skill.enabler
```

`spx/21-spec-tree.enabler/35-evidence.enabler/39-test-skill.enabler` and `spx/21-spec-tree.enabler/35-evidence.enabler/39-eval-skill.enabler` are independent evidence providers at the same index. `spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler` consumes both providers and therefore follows them. `spx/21-spec-tree.enabler/35-evidence.enabler/39-eval-skill.enabler/21-skill-eval.enabler` is the first concrete producer specialization inside the eval aggregate; later producer types use the reserved child horizon only when their own contracts become known.

## Ordering evidence

| Predecessor                                                          | Ordering basis        | Constraining contribution         | Successor                                                              | Required by                                  | Consequence if absent                                           | Disposition        |
| -------------------------------------------------------------------- | --------------------- | --------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------- | --------------------------------------------------------------- | ------------------ |
| `spx/21-spec-tree.enabler/35-evidence.enabler/39-test-skill.enabler` | Provider/consumer     | Deterministic test evidence route | `spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler` | Verification routing for `[test]` assertions | Verification can classify test evidence but cannot construct it | Ordered dependency |
| `spx/21-spec-tree.enabler/35-evidence.enabler/39-eval-skill.enabler` | Provider/consumer     | Structured eval evidence route    | `spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler` | Verification routing for `[eval]` assertions | Verification can classify eval evidence but cannot construct it | Ordered dependency |
| `spx/21-spec-tree.enabler/35-evidence.enabler/39-test-skill.enabler` | Independent providers | Test evidence                     | `spx/21-spec-tree.enabler/35-evidence.enabler/39-eval-skill.enabler`   | None                                         | Neither provider loses coherence or verifiability               | Same-index peers   |

## PR 1 — verification routing and current-type migration

- Add `/verify` under `spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler`.
- Route every authored `/test` invocation site through `/verify`; `/verify` delegates selected test work to `/test`.
- Narrow `/test` enough to accept only routed `[test]` work and remove its claim to verification-type ownership. The full test-ceremony extraction remains PR 2.
- Recognize only the current verification types: test, evaluate, and audit. The shipped workflow carries no compatibility vocabulary.
- Migrate repository assertions by removing unsupported tags before current-type classification; the one-time repository refactor owns that migration and does not add compatibility behavior to `/verify`.
- Regenerate skill trees and managed instruction blocks after authored source changes.

## PR 2 — generic test routing

- Keep `/test` as the generic test specialist invoked only by `/verify`.
- Move assertion typing, execution-level selection, source-contract checks, evidence properties, exception classification, naming, context checks, and reporting ceremony out of language workers.
- Route from `/test` to `/test-{language}` only after generic decisions are complete.
- Give test authoring and test auditing one independently loadable standards source; language skills carry only language-specific expression and commands.

## PR 3 — generic eval routing and skill evaluation

- Add `/eval` under `spx/21-spec-tree.enabler/35-evidence.enabler/39-eval-skill.enabler`.
- Add `/eval-skill` under `spx/21-spec-tree.enabler/35-evidence.enabler/39-eval-skill.enabler/21-skill-eval.enabler` as the first producer specialization.
- Consume a product-declared semantic command contract for prompt materialization, one-case paid execution, freshness inspection, and deterministic aggregation.
- Run paid cases serially and fail fast. Producer, prompt, case, grader, model, or effective-setting changes invalidate only mismatched case results.
- Keep producer repair in the producer-owning workflow; eval authoring owns the oracle and evidence artifacts.
- Give eval authoring and eval auditing one independently loadable evidence standard.

## Assertion redistribution

- Verification-type selection moves from this parent to `spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler`.
- Test assertion typing, level selection, evidence integrity, and language delegation move to `spx/21-spec-tree.enabler/35-evidence.enabler/39-test-skill.enabler`.
- Eval routing and producer specialization move to `spx/21-spec-tree.enabler/35-evidence.enabler/39-eval-skill.enabler` and its first child.
- Cross-type standards identity and acyclic routing remain on this parent.

Every assertion in the declared node structure carries its current verification tag in PR 1; later implementation PRs add runtime assertions only with their selected evidence.
