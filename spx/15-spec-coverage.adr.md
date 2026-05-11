# Spec Coverage Scope

## Purpose

This decision governs which evidence mechanism applies to which kind of assertion across the marketplace, so that every plugin carries verifiable evidence proportional to its deliverable rather than `[review]` by default.

## Context

**Business impact:** The marketplace spans plugins whose deliverable is executable code (Python tooling, validators, harnesses), plugins whose deliverable is LLM-driven behavior (auditing skills, classifiers, content producers), and plugins whose value lies in design or semantic principle (style guides, reference standards). A single evidence mechanism cannot honestly cover all three — `[test]` is brittle for LLM behavior, `[review]` is unfalsifiable for executable code, and `[eval]` is overhead for deterministic logic.

**Technical constraints:** Executable code is observed by a test runner. LLM-driven behavior is observed by replaying curated cases through the producing skill and parsing its structured verdict against per-eval expected fields. Design or intent has no structural signal a runner can compare against. Each evidence mechanism corresponds to one of these observation channels; mismatched pairings either degrade falsifiability or impose disproportionate cost.

## Decision

All plugins get at least one enabler node in the spec tree. Plugins with implementation code carry `[test]` evidence on assertions about executable behavior. Plugins whose deliverable is LLM-driven behavior — auditing skills, classifiers, content producers — carry `[eval]` evidence on assertions about that behavior, scored against curated cases through the eval harness governed by `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`. Assertions whose subject is the design or intent of the skill (rather than its runtime behavior) carry `[review]` evidence.

## Rationale

The spec tree's value derives from the truth hierarchy: specs declare, evidence verifies, code complies. Three evidence mechanisms cover the three subject categories:

- `[test]` for deterministic code paths verified by a test runner.
- `[eval]` for LLM-driven behavior that emits a structurally validatable verdict whose shape each eval declares. The eval harness replays curated cases, parses verdicts, and scores against expected fields; non-determinism is bounded by pass@k and threshold gating. Falsifiability comes from the per-eval verdict schema, not from interpreting prose.
- `[review]` for semantic constraints about design or intent that no structural grader can falsify.

Tautological tests over markdown structure are excluded by the NEVER clause — parsing a skill file to check for the presence of a heading proves formatting, not behavior. Eval evidence avoids this failure mode because the case set drives the skill end-to-end and the grader inspects the verdict the skill produces.

The alternative — excluding LLM-driven plugins from `[test]`-class evidence entirely — was rejected because it conflated two failure modes: prose-interpreting tests (genuinely brittle) and structural-verdict evals over curated cases (deterministic at the grader, bounded at the runner). The per-eval verdict schema — declared in each case's expected fields and the eval's prompt template — provides the structural contract that makes the second category falsifiable.

## Trade-offs accepted

| Trade-off                                                                        | Mitigation / reasoning                                                                                                                           |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Eval runs depend on a live LLM and accrue per-case cost                          | The eval harness gates expensive runs at `l3`, caps spend per case, and re-runs are scheduled via threshold-aware CI rather than on every change |
| Pass@k and threshold gates leave a small probability of flake                    | Threshold tuning is a calibration concern owned by the eval-harness enabler; the verdict schema removes prose ambiguity from the grader          |
| Adding implementation code or LLM-driven behavior to a plugin escalates coverage | This is the intended forcing function — new behavior brings new evidence requirements                                                            |

## Compliance

### Recognized by

Implementation plugins carry `[test]` assertions on assertions about executable behavior. Plugins whose deliverable is LLM-driven behavior carry `[eval]` assertions referencing case files under the node's `tests/` directory and graded by the eval harness. Assertions about skill design, intent, or semantic principle carry `[review]`.

### MUST

- Create at least one enabler node for every checked-in marketplace plugin — the tree is the complete product map ([review])
- Use `[test]` evidence for assertions about executable code — review is not a substitute for automated verification ([review])
- Use `[eval]` evidence for assertions about LLM-driven skill behavior where the producing skill emits a structured verdict whose shape the eval declares — the per-eval verdict schema makes the grader deterministic and the case set bounds the claim ([review])
- Use `[review]` evidence for assertions about skill design or intent that no structural verdict can falsify ([review])

### NEVER

- Create automated tests for pure-skill plugins that parse markdown structure — formatting-shaped evidence proves nothing about behavior ([review])
- Grade eval cases by interpreting free-form LLM prose — the grader reads structural verdict fields against per-eval expected structures; prose summaries are auxiliary, not authoritative ([review])
