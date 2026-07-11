Dispatch the `adr-auditor` agent to audit the supplied ADR through its required `audit-adr` skill. Treat the caller's scope classification as language-neutral. Return only the structured JSON verdict produced by the audit.

The ADR input (JSON-encoded):

```json
{input_json}
```
