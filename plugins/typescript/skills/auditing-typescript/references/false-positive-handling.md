# False Positive Handling

Not all tool violations are real issues. Context matters.

## When a Violation is a False Positive

A violation is a **false positive** when:

1. **Context changes the threat model**:
   - Security rule in a CLI tool where inputs come from the user invoking the tool
   - XSS rule in server-side code that never renders to browser

2. **The code is intentionally doing something the rule warns against**:
   - Using `eval` for a REPL implementation with sandboxing
   - Using `any` for external library compatibility layer

3. **The rule doesn't apply to this framework or pattern**:
   - React-specific rules in non-React code
   - Node.js rules in browser code

## When a Violation is NOT a False Positive

A violation is **real** when:

- User/external input can reach the flagged code path
- The code runs in a web service, API, or multi-tenant environment
- The "justification" is just "we've always done it this way"
- You cannot explain exactly why it's safe in this specific context

## Required Disable Comment Format

When suppressing a rule, the comment MUST include justification:

```typescript
// GOOD - explains why it's safe
// eslint-disable-next-line security/detect-child-process -- CLI tool, cmd from trusted config
const result = execSync(cmd);

// BAD - no justification
// eslint-disable-next-line security/detect-child-process
const result = execSync(cmd);
```

## Application Context Guide

| Application Type        | Trust Boundary        | exec/spawn             | Hardcoded Paths   |
| ----------------------- | --------------------- | ---------------------- | ----------------- |
| CLI tool (user-invoked) | User is trusted       | Usually false positive | Often intentional |
| Web service             | All input untrusted   | Real issue             | Real issue        |
| Internal script         | Depends on deployment | Analyze case-by-case   | Usually OK        |
| Library/package         | Consumers untrusted   | Real issue             | Avoid             |
