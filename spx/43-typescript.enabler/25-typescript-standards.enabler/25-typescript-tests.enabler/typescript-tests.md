# TypeScript Tests

PROVIDES TypeScript test standards for assertion type, execution level, testability, test data ownership, test-infrastructure auditing, and generator use
SO THAT TypeScript testing and audit skills
CAN produce evidence that is coupled to source behavior, maintainable under source changes, and free of literal laundering

## Assertions

### Compliance

- ALWAYS: the TypeScript filename instantiation of the canonical test-filename model in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md` is `<subject>.<evidence>.<level>[.<runner>].test.ts`, with Vitest as the default runner an omitted runner token names — expression of the model, altering no token semantics ([audit])

- ALWAYS: TypeScript test guidance starts from the spec assertion and its `/test`-selected assertion type before choosing file names, runners, harnesses, generators, or examples — test shape follows the claim being proved ([audit])
- ALWAYS: TypeScript test-standard specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the language-neutral seam rules, while the `21-source-testability.enabler`, `32-test-data-ownership.enabler`, `43-test-infrastructure-auditing.enabler`, and `54-execution-level-guidance.enabler` child nodes own the specific TypeScript source-design, value-ownership, auditing, and execution-level deltas — this parent restates neither the seam rules nor the child deltas ([audit])
