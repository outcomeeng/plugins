# Generated-Source Attribution

A product that commits generated artifacts declares them in `spx/local/generated-sources.toml` — one relation per generation relationship, naming the generated extents (whole files by path pattern, regions of authored files by marker pair), the authored sources, the optional generator implementation, and the deterministic regeneration command. Attribution of any changed path derives from that declaration alone: agentic verification skips declared generated extents and records them as skipped, judges them only when generation infrastructure is the verification subject, and resolves findings about generated content to the declaring relation's sources, while deterministic verification always covers the complete changeset.

## Rationale

An unannotated changed-path list makes agentic verifiers judge committed generated output as authored work — duplicating findings across source and output and misjudging generation inputs as defective final artifacts — while per-consumer path heuristics drift; one committed machine-readable declaration gives every verifier, script, and scope projection the same attribution. The rejected alternative, a per-path provenance class vocabulary, collapses into the declaration: a wholly generated file is a generated region covering the whole file, and generation inputs and generator implementations are authored files whose roles exist only within a relation.

## Declaration

The declaration is a committed TOML document at `spx/local/generated-sources.toml`. Each `[[relation]]` record names one generation relationship:

| Field        | Content                                                                                                                                                                                             |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `outputs`    | Generated extents: repository-relative path patterns for wholly generated files, or inline tables `{ file, begin, end }` naming an authored file and the marker pair bounding each generated region |
| `sources`    | Path patterns for the authored inputs the generator consumes                                                                                                                                        |
| `generator`  | Optional path patterns for the generator implementation                                                                                                                                             |
| `regenerate` | The deterministic command that reproduces the outputs from the sources                                                                                                                              |

A region marker matches a line whose content, after leading whitespace, starts with the marker text; the extent spans from the begin line through the end line inclusive, for every such pair in the file. A path's attribution derives from the declaration: wholly generated when covered by an `outputs` path pattern, generated-region-bearing when named by a region entry, authored otherwise. Sources and generator implementations are authored content; their generation roles exist only within their relation, and a relation's source may itself be another relation's output.

## Product properties

1. Attribution derives from the committed declaration alone — no verifier or consumer maintains private generated-path heuristics.
2. An ordinary agentic verification run records every declared generated extent in its scope as skipped rather than silently dropping it, so every raw changed path stays accounted for.
3. A generated extent is judged as evidence exactly when generation infrastructure is the verification subject — the changeset touches its relation's sources or generator, or the declared subject is that relation's source-to-output contract.

## Verification

### Audit

- ALWAYS: a repository that commits generated artifacts declares every generated extent in `spx/local/generated-sources.toml`, each relation naming its outputs, its sources, and its regeneration command ([audit])
- ALWAYS: ordinary agentic verification (review, audit) excludes declared generated extents from judgment and records each skipped extent in the run's scope evidence ([audit])
- ALWAYS: a generated extent is judged as agentic-verification evidence when the changeset touches its relation's sources or generator, or the declared verification subject is that relation's source-to-output contract ([audit])
- ALWAYS: a finding about generated content resolves to the declaring relation's sources — a verifier never requires a hand-edit inside a declared generated extent ([audit])
- ALWAYS: deterministic verification (validate, test, evaluate) runs over the complete changeset including generated extents, and each relation's regeneration command backs the parity evidence established before agentic verification dispatch per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([audit])
- ALWAYS: a generation input or generator implementation is judged as authored content in its generation role — template syntax is judged as template syntax, never as defective final output ([audit])
- NEVER: a verifier or consumer derives generated-source attribution from path similarity, naming convention, or any source other than the committed declaration ([audit])
