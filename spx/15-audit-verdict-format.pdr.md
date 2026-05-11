# Audit Verdict Format and Delivery

## Purpose

Governs the output format of audit verdicts, the canonical schema they conform to, and how each surface form delivers them to readers (humans, CI systems, calling skills).

## Context

**Business impact:** Audit skills produce verdicts that function as the success criterion for the artifact under audit. Prose verdicts embed LLM judgment in the success criterion — a verdict written in natural language is re-read and re-interpreted by the producing skill, which defeats deterministic auditing. The audit passes or fails based on language the validator must interpret rather than structure the validator can parse.

**Technical constraints:** The marketplace ships multiple audit skills across languages and domains, plus a generic `/auditing` orchestrator that aggregates dispatched verdicts. Each audit needs a validator. Fragmenting into per-skill validators duplicates tooling and allows the verdict contract to drift per skill. Verdicts also travel through multiple surfaces: PR comments (humans + bots), pipe-connected skill chains (machines only), local terminal output (humans), and shared state files (machines + humans). One surface form does not fit every channel.

## Decision

Audit skills emit verdicts as structured JSON documents conforming to one canonical schema declared in `plugins/spec-tree/skills/auditing/scripts/verdict.py`. Skills never hand-format markdown; the marketplace's stdlib-only verdict toolchain (`emit_verdict.py`, `read_verdict.py`, `aggregate_verdicts.py`) renders the JSON in three surface forms selected by a `--format` axis:

- **`markdown`** — human-readable table only. Local terminal inspection.
- **`markdown+json`** — markdown table followed by an HTML-comment-delimited JSON block (`<!-- AUDIT_VERDICT_JSON_BEGIN --> ... <!-- AUDIT_VERDICT_JSON_END -->`). PR-comment delivery: humans read the table, tooling parses the JSON.
- **`json-only`** — raw JSON. Skill-to-skill internal calls and machine-only delivery channels.

The producing skill emits JSON to stdout; the calling workflow forwards a `--format` argument to `emit_verdict.py` and consumes the rendered surface. A skill's success criterion is exit-0 from the toolchain validator on its JSON output. The toolchain ships inside the `spec-tree` plugin's `skills/auditing/scripts/` directory and runs against `python3` only, per the Plugin Portability Constraints in `AGENTS.md`.

## Rationale

**JSON over XML.** Audit verdicts are produced by LLMs. Modern model training emphasizes JSON for tool use, structured generation, and function calling; models emit valid JSON with high fidelity, while XML suffers from inconsistent self-closing-tag style, missing close tags, attribute-vs-element confusion, and unescaped angle brackets in text content. The verdict contract's structural needs (status enums, lists of findings, hierarchical row/finding/child structure) are well-served by JSON objects and arrays; mixed-content documents are not in scope. Empirical validation: a JSON verdict in the slice eval produced ~70% smaller grader code and ~40% lower latency than its XML predecessor.

**Carrier + payload over JSON-only.** A PR-comment delivery channel is the only durable cross-CI-run surface for an audit verdict — every run posts to the same comment thread, and a downstream run reads its predecessor's verdict from there. Humans read those comments; pure JSON in a comment is hostile to human review. The carrier+payload model preserves both: a markdown table renders for humans, an HTML-comment-delimited JSON block carries the machine-readable verdict. Tools extract the JSON by delimiter match; humans see the table. The `--format` axis lets the same producer serve every channel without branching the verdict generator.

**One canonical schema, one toolchain.** Every audit skill in the marketplace — orchestrator, dispatched language audits, develop-plugin audits, generic spec-tree audits — emits JSON conforming to `verdict.py`'s schema and pipes through `emit_verdict.py`. The orchestrator aggregates dispatched verdicts via `aggregate_verdicts.py`; the rollup rule (`REJECTED` if any child fails, `UNKNOWN` if any child is unknown without failures, `APPROVED` otherwise) lives in one place. Skills do not invent verdict shapes, do not hand-format markdown, do not duplicate rollup logic.

**`python3` stdlib over a third-party validator.** The toolchain ships inside the spec-tree plugin and runs in consumer projects that have neither `uv` nor any third-party package. Stdlib (`json`, `argparse`, `dataclasses`, `enum`, `pathlib`, `tempfile`) is sufficient for schema validation, surface rendering, parsing, and aggregation. The `outcomeeng_*` repo packages are marketplace build/test infrastructure — not portable to consumer projects.

## Trade-offs accepted

| Trade-off                                                                            | Mitigation / reasoning                                                                                                                                                 |
| ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| JSON Schema constraints are less expressive than XSD 1.1 for mixed-content documents | The verdict contract has no mixed-content needs; status enums, finding arrays, and rule identifiers fit JSON's object-and-array model with no expressiveness gap       |
| Three surface forms instead of one                                                   | The format axis is a single CLI flag forwarded by the calling workflow; producers emit one shape (JSON) regardless of surface; rendering is deterministic Python       |
| Carrier delimiter requires consumers to extract the JSON block                       | The marketplace ships `read_verdict.py` to do the extraction; consumers that need the JSON call the script rather than implementing delimiter matching themselves      |
| Stdlib-only constrains schema-validation richness                                    | The Python module is the canonical schema (dataclasses + parser); JSON Schema is not authored. Stdlib-driven validation covers every constraint the toolchain enforces |

## Product invariants

- Every audit verdict in the marketplace conforms to exactly one canonical schema declared in `verdict.py`. No skill ships its own verdict shape.
- Every surface form (`markdown`, `markdown+json`, `json-only`) preserves the schema content losslessly — the same verdict can be emitted in one form and read back in another via the canonical toolchain.
- The `markdown+json` carrier wraps the JSON payload between the two HTML-comment delimiters declared by the toolchain — never between markdown fences (`` ```json ``), never as the entire response body for a PR-comment channel, never without delimiters.
- The orchestrator's wrapper verdict derives its overall via the canonical `roll_up` rule applied to its children's overalls — orchestrators do not re-implement the rollup.

## Compliance

### Recognized by

An audit skill emits a single JSON document conforming to the schema in `verdict.py` and pipes it through `emit_verdict.py` with a `--format` argument forwarded from the calling workflow. The toolchain validator (`verdict.parse_json`) returns exit-0 on a conforming verdict and non-zero on any schema violation. Markdown surfaces produced via the toolchain include the canonical concerns table; `markdown+json` surfaces include the JSON payload between the canonical delimiter comments.

### MUST

- Emit audit verdicts as JSON conforming to the schema in `plugins/spec-tree/skills/auditing/scripts/verdict.py` — deterministic structural validation requires one shared schema ([review])
- Pipe the JSON through `emit_verdict.py` with the `--format` argument forwarded from the calling workflow — surface rendering is deterministic Python, not free-form LLM output ([review])
- Use the `markdown+json` form for any channel a human reader may inspect (PR comments, terminal output captured for review) — the carrier preserves human readability without sacrificing machine readability ([review])
- Use `json-only` for skill-to-skill internal channels — surfaces that no human reads do not pay the markdown rendering cost ([review])
- State the skill's success criterion as a single exit-0 check against `verdict.parse_json` on its JSON output — no prose interpretation in the success path ([review])
- Aggregate orchestrator child verdicts through `aggregate_verdicts.py` — the rollup rule lives in one place ([review])

### NEVER

- Hand-format markdown verdicts in a skill prompt — every audit skill produces JSON and routes through `emit_verdict.py` ([review])
- Ship per-skill verdict validators or per-skill verdict shapes — fragments the contract and breaks aggregation across the marketplace ([review])
- Embed verdict interpretation in the skill's LLM prompt — verdicts are validated deterministically, not interpreted ([review])
- Wrap the JSON payload in markdown fences (`` ```json ``) inside the `markdown+json` carrier — the HTML-comment delimiters are the canonical boundary; fences confuse both LLM emitters and downstream parsers ([review])
- Mandate that the assistant response IS the verdict — that constraint is true only for the `json-only` skill-to-skill channel; PR-comment delivery uses the `markdown+json` carrier and includes the verdict as the embedded block, not as the entire response ([review])
- Re-implement the rollup rule in an orchestrator — the canonical `roll_up` in `verdict.py` is the only source ([review])
