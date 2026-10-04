# Issues: TypeScript code

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The TypeScript implementation and remediation routing is unextracted from the preserved aggregate

The preserved aggregate `spx/21-spec-tree.enabler/65-apply.enabler/ISSUES.md` records holds TypeScript implementation and remediation guidance that must consume the shared review, audit and test-verification contracts without redeclaring parallel policy. That guidance is not extracted, so it stays entangled with the aggregate's test-ownership changes, which belong to the test-verification node.

**Settlement condition.** The TypeScript implementation and remediation workflows route TypeScript work through the shared review, audit and test-verification contracts and redeclare no parallel policy, one verification story proves that routing contract, and it lands as its own pull request.
