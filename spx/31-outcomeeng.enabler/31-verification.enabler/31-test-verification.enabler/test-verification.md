# Test Verification

PROVIDES Outcome Engineering governance for deterministic test evidence, test-infrastructure ownership, property-test reproducibility, and full-chain test-evidence audits
SO THAT methodology tests, plugin tests, runtime validation, and language-specific test standards
CAN prove spec assertions through source-coupled evidence without laundering domain truth through test files or helper modules

## Assertions

### Compliance

- ALWAYS: harness, generator, fixture, source-contract, and full-chain audit semantics derive from `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([audit])
- ALWAYS: before an executed test file changes, emit one evidence-design row per assertion that records the quantifier and domain, independent oracle, pass-while-false counterexample, execution level, source-contract needs, harness needs, generator needs, and fixture status; stop on a missing oracle, constant-only generator, absent property replay harness, or fixture without scoped operator approval ([audit])
- ALWAYS: executed test files contain assertion flow only; values, expected outputs, reusable cases, property-test settings, setup policy, and lifecycle policy live in source contracts, spec-governed harnesses, spec-governed generators, operator-approved inert whole-payload fixtures, or curated eval cases when generation is wasteful and intractable ([audit])
- ALWAYS: property-based tests run through spec-governed harnesses that own seed selection, run count, replay input, and failure diagnostics so a failing property run is reproducible from the reported evidence ([audit])
- ALWAYS: every local artifact reference in an evidence-design packet is a product-root-relative Markdown link; harnesses, generators, fixtures, and source contracts link first to their exact governing spec or decision file and also to their implementation when it exists, while an implementation link alone never establishes governance; language-specific test standards derive their file-to-file and reference-role guidance from this node ([audit])
- ALWAYS: test-evidence audits reconstruct the design independently, inspect the executed test file and every imported or referenced test-infrastructure artifact, validate each reference by its declared role, and report every observable defect class in the first verdict ([audit])
- NEVER: a test file declaration, variable binding, fixture parameter, property-generated parameter, or renamed constant changes ownership; the audit still routes the owned value or configuration to the proper source, harness, generator, fixture, or eval case ([audit])
