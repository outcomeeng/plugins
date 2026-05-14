# Evidence Execution Lanes

## Purpose

Governs how the marketplace separates evidence by execution surface. Spec assertions span deterministic Python code, LLM-driven skill behavior, and audit judgment; each needs its own runner, cadence, and CI integration. One runner cannot honestly cover all surfaces without either degrading signal quality on the strict lane or inflating cost on the cheap lane.

## Context

**Business impact:** Mismatched runners produce silent quality failures. Pytest forced over LLM-driven behavior either accepts non-determinism into the per-PR gate (where flakes destroy signal) or pushes the LLM lane behind an opt-in environment flag (where the gate stops enforcing the assertion). A general-purpose eval runner forced over deterministic Python code adds dollars and minutes for no evidence gain.

**Technical constraints:**

- The marketplace publishes skills that emit structured verdicts (auditing skills) and skills that emit free-form text. Assertions about the structured-verdict behavior are amenable to graded LLM evaluation; assertions about free-form behavior are not.
- Pytest is well-suited to deterministic logic and parser-backed structural evidence per `spx/15-test-language.adr.md`. It is not well-suited to multi-trial LLM grading with pass@k thresholds.
- The `[eval]` evidence mechanism, declared in `spx/15-spec-coverage.adr.md` and detailed in `plugins/spec-tree/skills/understanding/references/assertion-types.md`, requires its own execution surface. The `outcomeeng_evals` package, governed by `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`, provides that surface.
- The `[review]` mechanism has no automated execution surface — it is human or agent judgment captured during an audit pass.

## Decision

The marketplace separates evidence by execution lane. Three lanes are declared:

1. **`[test]` lane** — pytest, governed by `spx/15-test-language.adr.md`. Deterministic Python: pure logic, parser-backed structural checks, command-builder verification, file-output assertions, link-integrity checks.
2. **`[eval]` lane** — the `outcomeeng_evals` CLI, governed by `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`. Graded LLM behavior over curated cases, with structured-verdict graders matching per-eval expected fields.
3. **`[review]` lane** — audit skills, no automated runner. Human or agent judgment captured during a review pass.

Every spec assertion's evidence mechanism maps to exactly one lane. Each lane has its own runner, cadence, and CI integration. Lanes do not absorb each other; a new lane is added by amending this ADR alongside the ADR that governs the new lane.

## Rationale

**Separated lanes over a single-tool policy.** Pytest, an eval CLI, and human review have orthogonal cost profiles (milliseconds, dollars, attention) and orthogonal cadence profiles (per-PR, scheduled, on-audit). Forcing them through one runner either inflates the cost of the cheap lanes or drops the expensive lanes out of the gate. Naming the lanes explicitly preserves the distinct cost-cadence pairs.

**Each lane carries its own ADR governing implementation.** `spx/15-test-language.adr.md` governs `[test]`; `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md` governs `[eval]`. This ADR carries only the lane declarations themselves and the routing rule, not the per-lane implementation choices.

**Evidence mechanism is the routing key, not assertion type.** A Compliance assertion can route to `[test]`, `[eval]`, or `[review]` depending on what falsifies the rule. The mechanism is independent of the assertion type per `plugins/spec-tree/skills/understanding/references/assertion-types.md`. Routing by mechanism keeps the lane decision local to each assertion rather than coupled to a global type-to-lane map.

**Lane addition is a deliberate amendment, not an implicit extension.** A new lane — Hurl HTTP evidence, live remote-state evidence, structural artifact comparison — is added by amending this ADR with the new lane and the ADR that governs it. The lane catalog is finite, explicit, and reviewable.

Alternatives rejected: a single mega-runner covering all evidence types (conflates cost profiles and degrades the strict lane); per-assertion-type lane mapping (Compliance assertions cross all lanes, so the mapping has to live at the mechanism level); leaving lanes implicit and discoverable through code (new lanes appear without governance, silently expanding the gate's failure modes).

## Trade-offs accepted

| Trade-off                                                           | Mitigation / reasoning                                                                                                                                |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Each lane needs its own runner configuration and CI step            | Three small focused runners cost less to maintain than one runner that fights its dominant use case; per-lane configuration stays local to its ADR    |
| Adding a new evidence-execution lane requires an ADR amendment      | The amendment is the audit point — silent lane proliferation would defeat the separation principle                                                    |
| An assertion cannot mix evidence mechanisms within a single tag     | The mechanism is the routing key; mixed-mechanism evidence becomes two assertions, not one                                                            |
| Link-integrity validation is a per-lane concern, not a single check | The marketplace script under `outcomeeng/scripts/` walks both `[test]` and `[eval]` link forms in one pass; lane-specific resolution rules apply once |

## Compliance

### Recognized by

Every spec assertion in the marketplace tree carries exactly one of `[test](path)`, `[eval](path)`, or `[review]`. Each `[test]` link resolves to a pytest collectable under some `spx/**/tests/` directory. Each `[eval]` link resolves to an `eval.toml` under some `spx/**/evals/{rule}/` directory. Each `[review]` tag carries no path. No assertion's evidence mechanism is ambiguous or mixed.

### MUST

- Every assertion's evidence mechanism maps to exactly one declared lane: `[test]` (pytest), `[eval]` (`outcomeeng_evals` CLI), or `[review]` (audit) ([review])
- The `[test]` lane runs through pytest per `spx/15-test-language.adr.md` ([review])
- The `[eval]` lane runs through the `outcomeeng_evals` CLI per `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md` ([review])
- A new evidence-execution lane is added by amending this ADR in place and referencing the ADR that governs it ([review])
- A marketplace link-integrity validator under `outcomeeng/scripts/` asserts that every `[test]` link resolves to an existing pytest collectable and every `[eval]` link resolves to an existing `eval.toml`; the validator runs as part of `just check` ([review])

### NEVER

- Route an assertion through a lane that does not match its evidence mechanism — `[test]` does not execute through the eval CLI, `[eval]` does not execute through pytest as its primary surface ([review])
- Collapse the `[test]` and `[eval]` lanes into a single runner — their cost and cadence profiles are not compatible ([review])
- Introduce a new evidence-execution lane without amending this ADR and authoring the governing ADR for the lane ([review])
- Mix evidence mechanisms within a single assertion tag — the mechanism is single-valued by decision ([review])
