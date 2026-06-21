<!-- Prompt template for the spx-reachability-check eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model. -->

You are the `diagnose` skill running its `spx-reachability` check. Apply that check's verdict table from the skill body to the readings below and emit the check's classification.

The readings stand in for what the check gathers at runtime: `command_v_spx` is the path `command -v spx` resolves to (or `null` when it finds nothing), `spx_version` is the string `spx --version` reports (or an `error` field when that command fails), and `floor` is the version floor the check judges the reported version against. Classify exactly as the skill's table prescribes, comparing `spx_version` against `floor` by dotted-numeric order: `spx` on PATH reporting a version at or above `floor` is `reachable`; `spx` on PATH reporting a version below `floor` is `below-floor`; `command -v spx` finding nothing is `unreachable`; a command that errors, or a version that is not dotted-numeric and so cannot be ordered against `floor`, falls to `unknown` per the workflow's step-4 fallback.

Case id: substituted by the harness.

The readings (JSON-encoded input payload follows):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — conforming to this schema:

```
{
  "check": "spx-reachability",
  "verdict": "reachable" | "below-floor" | "unreachable" | "unknown",
  "bucket": "healthy" | "degraded" | "broken" | "unknown",
  "path": "<the resolved path from command_v_spx, verbatim, or null when spx is not on PATH>",
  "version": "<the version string from spx_version, verbatim, or null when no version was read>",
  "remediation": "<remediation hint string, or null when the verdict is reachable>"
}
```

Bucket mapping from the skill's verdict table: `reachable` → healthy; `below-floor` → degraded; `unreachable` → broken; `unknown` → unknown. For a `reachable` or `below-floor` verdict, `path` and `version` carry the readings verbatim — exactly as `command_v_spx` and `spx_version` supplied them, never paraphrased or rounded. Every verdict except `reachable` carries a non-null remediation hint.
