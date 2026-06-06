# Audit Verdict Format and Delivery

Audit skills emit verdicts as structured JSON conforming to one canonical schema declared in `plugins/spec-tree/skills/auditing/scripts/verdict.py`. The marketplace's stdlib-only verdict toolchain (`emit_verdict.py`, `read_verdict.py`, `aggregate_verdicts.py`) renders that JSON in three surface forms selected by a `--format` axis: `markdown` (a human-readable table for terminal inspection), `markdown+json` (the table followed by an HTML-comment-delimited JSON block for PR-comment delivery, where humans read the table and tooling parses the JSON), and `json-only` (raw JSON for skill-to-skill and machine-only channels). A skill emits JSON to stdout; the calling workflow forwards `--format` to `emit_verdict.py` and consumes the rendered surface.

## Rationale

JSON over XML because audit verdicts are produced by LLMs, which emit valid JSON with high fidelity while XML suffers self-closing-tag and unescaped-bracket failure modes; the verdict contract's needs (status enums, finding arrays, hierarchical rows) fit JSON's object-and-array model. Carrier-plus-payload over JSON-only because a PR comment is the only durable cross-CI-run surface — humans read those comments, so a markdown table renders for humans while an HTML-comment-delimited JSON block carries the machine-readable verdict, and `--format` lets one producer serve every channel. One canonical schema and one toolchain because every audit skill across languages and domains emits to the same contract and the orchestrator aggregates through one rollup rule, so skills invent no verdict shapes and duplicate no rollup logic. The toolchain is `python3` stdlib because it ships inside the spec-tree plugin and runs in consumer projects that have neither `uv` nor third-party packages.

## Product properties

1. Every audit verdict in the marketplace conforms to exactly one canonical schema declared in `verdict.py` — no skill ships its own verdict shape.
2. Every surface form (`markdown`, `markdown+json`, `json-only`) preserves the schema content losslessly — the same verdict emitted in one form reads back in another via the canonical toolchain.
3. The `markdown+json` carrier wraps the JSON payload between the two HTML-comment delimiters — never between markdown fences, never as the entire response body for a PR-comment channel, never without delimiters.
4. The orchestrator's wrapper verdict derives its overall via the canonical `roll_up` rule applied to its children's overalls.

## Verification

### Audit

- ALWAYS: emit audit verdicts as JSON conforming to the schema in `plugins/spec-tree/skills/auditing/scripts/verdict.py` — deterministic structural validation requires one shared schema ([audit])
- ALWAYS: pipe the JSON through `emit_verdict.py` with the `--format` argument forwarded from the calling workflow — surface rendering is deterministic Python, not free-form LLM output ([audit])
- ALWAYS: use the `markdown+json` form for any channel a human reader may inspect — the carrier preserves human readability without sacrificing machine readability ([audit])
- ALWAYS: use `json-only` for skill-to-skill internal channels — surfaces no human reads do not pay the markdown rendering cost ([audit])
- ALWAYS: state the skill's success criterion as a single exit-0 check against `verdict.parse_json` on its JSON output — no prose interpretation in the success path ([audit])
- ALWAYS: aggregate orchestrator child verdicts through `aggregate_verdicts.py` — the rollup rule lives in one place ([audit])
- NEVER: hand-format markdown verdicts in a skill prompt — every audit skill produces JSON and routes through `emit_verdict.py` ([audit])
- NEVER: ship per-skill verdict validators or per-skill verdict shapes — fragments the contract and breaks aggregation across the marketplace ([audit])
- NEVER: embed verdict interpretation in the skill's LLM prompt — verdicts are validated deterministically, not interpreted ([audit])
- NEVER: wrap the JSON payload in markdown fences inside the `markdown+json` carrier — the HTML-comment delimiters are the canonical boundary ([audit])
- NEVER: mandate that the assistant response is the verdict — that holds only for the `json-only` skill-to-skill channel; PR-comment delivery embeds the verdict as the delimited block, not as the whole response ([audit])
- NEVER: re-implement the rollup rule in an orchestrator — the canonical `roll_up` in `verdict.py` is the only source ([audit])
