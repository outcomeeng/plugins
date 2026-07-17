# Changeset Coherence

PROVIDES an artifact-type audit that determines whether an exact committed changeset is one reviewable semantic unit and recommends dependency-ordered review units when it is not
SO THAT apply, publication, and merge workflows
CAN reject accumulated programs of work before expensive implementation audits and whole-changeset reviews

## Assertions

### Compliance

- ALWAYS: an exact committed changeset receives `APPROVED` only when its authored artifacts realize one behavioral outcome or inseparable semantic clusters with one verification story and one rollback story ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: an exact committed changeset receives `REJECTED` when two or more semantic clusters are independently mergeable, and the verdict returns a dependency-ordered review-unit sequence covering every authored artifact ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: a verdict receives `UNKNOWN` when behavioral claims, dependency evidence, generated-source relationships, verification evidence, rollback evidence, or repository calibration cannot be established; `UNKNOWN` never authorizes publication ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: generated artifacts are collapsed onto their producing authored artifact before path breadth, authored-change size, or review load is assessed ([eval](evals/coherence-verdict/eval.toml))
- NEVER: raw line count, file count, or review-load measurements determine the verdict without semantic evidence ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: the audit records behavioral claims, semantic clusters, authored artifacts, generated fanout, verification stories, rollback stories, dependencies, independent-mergeability judgments, review-load signals, findings, publication authorization, and a recommended review-unit sequence in one structured projection ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: the configured auditor is a thin read-only wrapper whose policy lives in the audit skill and whose result is the structured coherence-verdict JSON object ([audit])
