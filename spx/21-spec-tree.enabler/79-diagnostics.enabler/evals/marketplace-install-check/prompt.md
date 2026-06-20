<!-- Prompt template for the marketplace-install-check eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model. -->

You are the `diagnose` skill running its `marketplace-install` check. Apply that check's verdict table from the skill body to the readings below and emit the check's classification.

The readings stand in for what the check gathers at runtime, one entry per plugin surface. Each surface has `present` (whether its plugin CLI exists), `registered` (whether the methodology marketplace is registered on it), and `plugins` — the marketplace's offered plugins, each already joined to its install state: `installed` and `enabled` are booleans, and `installed_version` and `offered_version` are the version the surface has installed and the version the registered marketplace offers. A surface that is not `present` carries no install state. When a surface carries an `error` field, the underlying command failed.

Classify across the present surfaces exactly as the skill's table prescribes, taking the worst verdict over them (unregistered worse than drifted worse than installed):

- **installed** — every present surface has the marketplace registered and every offered plugin `installed`, `enabled`, and `installed_version` equal to `offered_version`.
- **drifted** — the marketplace is registered on the present surfaces, but at least one offered plugin is not installed, is installed but disabled, or has an `installed_version` below its `offered_version`.
- **unregistered** — a present surface does not have the marketplace registered, so its offered plugins cannot resolve.
- **not-applicable** — no surface is `present`, so there is no install surface to inspect.
- **unknown** — a command errors, per the workflow's step-4 fallback.

Case id: substituted by the harness.

The readings (JSON-encoded input payload follows):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — conforming to this schema:

```
{
  "check": "marketplace-install",
  "verdict": "installed" | "drifted" | "unregistered" | "not-applicable" | "unknown",
  "bucket": "healthy" | "degraded" | "broken" | "not-applicable" | "unknown",
  "remediation": "<remediation hint string, or null when the verdict is installed or not-applicable>"
}
```

Bucket mapping from the skill's verdict table: `installed` → healthy; `drifted` → degraded; `unregistered` → broken; `not-applicable` → not-applicable; `unknown` → unknown. Every verdict except `installed` and `not-applicable` carries a non-null remediation hint.
