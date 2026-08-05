# Plan: Prose Plugin

Governing spec: `spx/43-prose.enabler/prose.md` (router-pair surface over composed per-kind triples).

## Eval evidence for the prose surface (deferred by operator decision)

The router-pair surface ships with `[audit]`-class evidence; eval evidence is the recorded follow-up:

1. **Kind-detection evals** — the first candidate suite: given a text, does the router resolve the kind the taxonomy assigns it. Grades the structured verdict's `kind` field, so it couples to the producer per `spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md`.
2. **Style-adherence evals** — per-kind suites grading written output against the kind's standards. Larger authoring effort; depends on the verdict contract having settled in use.

The structured-verdict prerequisite recorded in `spx/43-prose.enabler/ISSUES.md` is resolved by the router-pair surface: `/audit-prose` declares the machine-readable verdict evals grade.
