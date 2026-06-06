# Spec Coverage Scope

Every checked-in marketplace plugin has at least one enabler node in the spec tree. Plugins with implementation code carry `[test]` evidence on assertions about executable behavior. Plugins whose deliverable is LLM-driven behavior — auditing skills, classifiers, content producers — carry `[eval]` evidence scored against curated cases through the eval harness governed by `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`. Assertions whose subject is the design or intent of a skill rather than its runtime behavior carry `[audit]` evidence.

## Rationale

The spec tree's value derives from the truth hierarchy — specs declare, evidence verifies, code complies — and three evidence mechanisms cover the three subject categories: `[test]` for deterministic code paths verified by a test runner; `[eval]` for LLM-driven behavior that emits a structurally validatable verdict, where the per-eval verdict schema makes the grader deterministic and the case set bounds the claim; `[audit]` for semantic constraints about design or intent that no structural grader can falsify. Tautological tests over markdown structure prove formatting, not behavior, so they are excluded — eval evidence avoids that failure mode because the case set drives the skill end-to-end and the grader inspects the verdict the skill produces. Excluding LLM-driven plugins from `[test]`-class evidence entirely would conflate two failure modes — prose-interpreting tests, which are genuinely brittle, and structural-verdict evals over curated cases, which are deterministic at the grader and bounded at the runner.

## Verification

### Audit

- ALWAYS: create at least one enabler node for every checked-in marketplace plugin — the tree is the complete product map ([audit])
- ALWAYS: use `[test]` evidence for assertions about executable code — audit is not a substitute for automated verification ([audit])
- ALWAYS: use `[eval]` evidence for assertions about LLM-driven skill behavior where the producing skill emits a structured verdict whose shape the eval declares — the per-eval verdict schema makes the grader deterministic and the case set bounds the claim ([audit])
- ALWAYS: use `[audit]` evidence for assertions about skill design or intent that no structural verdict can falsify ([audit])
- NEVER: create automated tests for pure-skill plugins that parse markdown structure — formatting-shaped evidence proves nothing about behavior ([audit])
- NEVER: grade eval cases by interpreting free-form LLM prose — the grader reads structural verdict fields against per-eval expected structures ([audit])
