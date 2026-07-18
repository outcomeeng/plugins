# Plan: extract TypeScript verification routing

The preserved aggregate contains TypeScript implementation and remediation guidance that must consume shared review, audit, and test-verification contracts without redeclaring parallel policy.

## Merge cycle

Reconstruct the TypeScript patch from current `origin/main` after the governing test-verification, review, and audit cycles merge. Keep only implementation and remediation workflow changes that route TypeScript work through those established contracts, together with this node's governing spec alignment and generated plugin output.

Split any TypeScript test-ownership change into the test-verification cycle when it can merge independently of code remediation behavior.

## Revisit condition

Replace this plan with the extracted branch and PR identity after the current base exposes the residual TypeScript diff and focused verification proves one implementation-routing contract.
