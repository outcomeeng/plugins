# Source Testability

PROVIDES the source-design stance for TypeScript test writing
SO THAT TypeScript test authors and auditors
CAN require architecture changes before accepting weak, literal-bound, or mock-bound evidence

## Assertions

### Compliance

- ALWAYS: TypeScript source-testability specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the source-design seam rules and declare only the TypeScript delta: the observable contracts source modules expose are TypeScript interfaces, typed dependency parameters, discriminated-union and enum constructors, exported registries, and typed factories; controlled implementations and recording collaborators conform to the same typed interface boundary as production ([audit])
