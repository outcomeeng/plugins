<overview>
Not all tool violations are real issues. Context matters.
</overview>

<when_false_positive>

1. **Context changes the threat model**: S603 (subprocess call) in a CLI tool where inputs come from the user invoking the tool, not untrusted external sources
2. **The code is intentionally doing something the rule warns against**: Using `pickle` for internal caching with no untrusted input
3. **The calling context guarantees safety**: A parameter that looks dead but is required by a Protocol contract

</when_false_positive>

<when_not_false_positive>

- You cannot explain exactly why it's safe in this specific context
- The "justification" is just "we've always done it this way"
- The code runs in a web service, API, or multi-tenant environment
- The surprise in the predict/verify protocol has no good explanation

</when_not_false_positive>

<required_noqa_format>

When suppressing a rule, the noqa comment MUST include justification:

```python
# GOOD - explains why it's safe
result = subprocess.run(cmd)  # noqa: S603 - CLI tool, cmd built from trusted config

# BAD - no justification
result = subprocess.run(cmd)  # noqa: S603
```

</required_noqa_format>

<application_context>

| Application Type        | Trust Boundary        | Security Rules     |
| ----------------------- | --------------------- | ------------------ |
| CLI tool (user-invoked) | User is trusted       | Usually relaxed    |
| Web service             | All input untrusted   | Strict enforcement |
| Internal script         | Depends on deployment | Case-by-case       |
| Library/package         | Consumers untrusted   | Strict enforcement |

</application_context>
