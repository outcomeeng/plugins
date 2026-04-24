# Audit Verdict Format and Delivery

## Purpose

Governs the output format of audit skills and how audit verdicts are validated.

## Context

**Business impact:** Audit skills produce verdicts that function as the success criterion for the artifact under audit. Prose verdicts embed LLM judgment in the success criterion — a verdict written in natural language is re-read and re-interpreted by the producing skill, which defeats deterministic auditing. The audit passes or fails based on language the validator must interpret rather than structure the validator can parse.

**Technical constraints:** The marketplace ships multiple audit skills across languages and domains. Each audit needs a validator. Fragmenting into per-skill validators duplicates tooling and allows the verdict contract to drift per skill.

## Decision

Audit skills emit verdicts as structured XML documents conforming to a shared schema. Verdict validation is delegated to the `spx` CLI via a dedicated subcommand. A skill's success criterion is a single exit-0 result from that subcommand — no prose is interpreted in the success path.

## Rationale

Two forces need simultaneous resolution:

- Audit verdicts must be deterministic. A machine must determine pass or fail without interpreting prose.
- The marketplace must not fragment into per-audit-skill validation tooling.

XML with a shared schema resolves both. Any XML validator library parses it; a single `spx` subcommand validates every verdict regardless of which skill produced it.

XML is chosen over JSON because audit verdicts are structurally rich: hierarchical (nested gates with assertions with findings), attribute-bearing (status attribute on gate elements), and schema-validatable with mature tooling (XSD 1.1, lxml, xmllint). JSON Schema is a serviceable alternative but flattens attributes into properties and has weaker tooling for mixed-content documents.

Delegation to the `spx` CLI is chosen over shipping per-plugin validators because `spx` already hosts the marketplace's validation pipeline. Adding one more sibling subcommand to the existing validation family is a uniform extension; shipping a Python script in one plugin, a Node script in another, and a Bash script in a third fragments the contract and multiplies maintenance.

## Trade-offs accepted

| Trade-off                                                 | Mitigation / reasoning                                                                                                      |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| XML verbosity compared with JSON or TOML                  | Schema tooling and attribute semantics matter more than compactness for a machine-checked contract                          |
| Audit skills acquire an `spx` CLI dependency              | `spx` is the marketplace's canonical validation host; the dependency unifies tooling rather than proliferating alternatives |
| Verdicts are less human-scannable than a markdown summary | The verdict is primarily for the validator; a skill may produce a separate human-readable summary without coupling the two  |

## Product invariants

- Every audit skill's success criterion is a machine-checkable XML validation result — no secondary pass/fail condition interprets prose.
- The verdict document contains only structural content — any human-readable narrative is produced separately and does not participate in the success check.

## Compliance

### Recognized by

Audit skills document their success criterion as an exit-0 result from the `spx` verdict-validation subcommand. The verdict document is well-formed XML and conforms to the shared schema. Prose summaries, if produced, live in separate documents from the validated verdict.

### MUST

- Emit audit verdicts as XML conforming to the shared schema — deterministic structural validation requires a uniform schema ([review])
- Delegate verdict validation to the `spx` CLI — marketplace-wide tooling uniformity ([review])
- State the skill's success criterion as a single exit-0 check against the shared validator — no prose interpretation in the success path ([review])

### NEVER

- Ship per-skill verdict validators — fragments the contract and duplicates tooling ([review])
- Embed verdict interpretation in the skill's LLM prompt — verdicts are validated deterministically, not interpreted ([review])
- Mix prose content with structural content in the verdict document — prose belongs in a separate summary document ([review])
