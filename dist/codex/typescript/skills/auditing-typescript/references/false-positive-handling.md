<overview>
Not all tool violations are real issues. Context matters.
</overview>

<when_false_positive>

1. **Context changes the threat model**: Security rule (child_process exec) in a CLI tool where inputs come from the user invoking the tool, not untrusted external sources
2. **The code is intentionally doing something the rule warns against**: Using `eval` for a REPL implementation with sandboxing
3. **The calling context guarantees safety**: A parameter that looks dead but is required by an interface/Protocol contract

</when_false_positive>

<when_not_false_positive>

- You cannot explain exactly why it's safe in this specific context
- The "justification" is just "we've always done it this way"
- The code runs in a web service, API, or multi-tenant environment
- The surprise in the predict/verify protocol has no good explanation

</when_not_false_positive>

<required_comment_format>

When suppressing a rule, the disable comment MUST include justification:

```typescript
// GOOD - explains why it's safe
// eslint-disable-next-line security/detect-child-process -- CLI tool, cmd from trusted config
const result = execSync(cmd);

// BAD - no justification
// eslint-disable-next-line security/detect-child-process
const result = execSync(cmd);
```

</required_comment_format>

<application_context>

| Application Type        | Trust Boundary        | Security Rules     |
| ----------------------- | --------------------- | ------------------ |
| CLI tool (user-invoked) | User is trusted       | Usually relaxed    |
| Web service             | All input untrusted   | Strict enforcement |
| Internal script         | Depends on deployment | Case-by-case       |
| Library/package         | Consumers untrusted   | Strict enforcement |

</application_context>
