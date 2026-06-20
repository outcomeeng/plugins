<!-- Prompt template for the spx-reachability-check eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model. -->

You are the `diagnose` skill running its `spx-reachability` check. Apply that check's verdict table from the skill body to the readings below and emit the check's classification.

The readings stand in for what the check gathers at runtime: `command_v_spx` is the path `command -v spx` resolves to (or `null` when it finds nothing), and `spx_version` is the string `spx --version` reports (or an `error` field when that command fails). Classify exactly as the skill's table prescribes: `spx` on PATH reporting a version is `reachable`; `command -v spx` finding nothing is `unreachable`; a command that errors falls to `unknown` per the workflow's step-4 fallback. The first slice reports the version verbatim and does not judge it against a floor.

Case id: substituted by the harness.

The readings (JSON-encoded input payload follows):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — conforming to this schema:

```
{
  "check": "spx-reachability",
  "verdict": "reachable" | "unreachable" | "unknown",
  "bucket": "healthy" | "broken" | "unknown",
  "path": "<the resolved path from command_v_spx, verbatim, or null when spx is not on PATH>",
  "version": "<the version string from spx_version, verbatim, or null when no version was read>",
  "remediation": "<remediation hint string, or null when the verdict is healthy>"
}
```

Bucket mapping from the skill's verdict table: `reachable` → healthy; `unreachable` → broken; `unknown` → unknown. For a `reachable` verdict, `path` and `version` carry the readings verbatim — exactly as `command_v_spx` and `spx_version` supplied them, never paraphrased or rounded. The `unreachable` and `unknown` verdicts carry a non-null remediation hint.
