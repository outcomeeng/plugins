# Issues: TypeScript code

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The TypeScript implementation and remediation routing is unextracted from the preserved aggregate

The preserved aggregate `spx/21-spec-tree.enabler/65-apply.enabler/ISSUES.md` records holds TypeScript implementation and remediation guidance that must consume the shared review, audit and test-verification contracts without redeclaring parallel policy. The TypeScript patch reconstructs from current `origin/main` after the governing test-verification, review and audit cycles merge, and it keeps only the implementation and remediation workflow changes that route TypeScript work through those contracts, with this node's spec alignment and the generated plugin output. A TypeScript test-ownership change that can merge independently of code remediation behavior belongs to the test-verification cycle.

**Settlement condition.** The residual TypeScript diff is visible against the current base, focused verification proves one implementation-routing contract, and the extracted branch lands as its own pull request.
