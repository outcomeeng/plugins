# Changeset Coherence

PROVIDES an artifact-type audit that determines whether an exact committed changeset is one reviewable semantic unit and recommends dependency-ordered review units when it is not
SO THAT apply, publication, and merge workflows
CAN reject accumulated programs of work before expensive implementation audits and whole-changeset reviews

## Assertions

### Scenarios

- Given a feature branch whose local base ref lags `origin/<base>` by an already-merged commit, when the audit resolves its own committed scope, then the resolved scope carries the branch's own change and excludes the already-merged file ([test](tests/test_resolve_scope.scenario.l1.py))

### Compliance

- ALWAYS: an exact committed changeset receives `APPROVED` only when its authored artifacts realize one behavioral outcome or inseparable semantic clusters with one verification story and one rollback story ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: an exact committed changeset receives `REJECTED` when two or more semantic clusters are independently mergeable, and the verdict returns a dependency-ordered review-unit sequence that covers every semantic cluster exactly once ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: every authored artifact in scope belongs to exactly one semantic cluster, and each generated artifact shares the cluster of its producing authored artifact ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: a verdict receives `UNKNOWN` when behavioral claims, dependency evidence, generated-source relationships, verification evidence, rollback evidence, or repository calibration cannot be established; `UNKNOWN` never authorizes publication ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: generated artifacts are collapsed onto their producing authored artifact before path breadth, authored-change size, or review load is assessed ([eval](evals/coherence-verdict/eval.toml))
- NEVER: raw line count, file count, path breadth, or review-load measurements determine the verdict without semantic evidence ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: the verdict preserves the changeset's exact base and head commit identities verbatim ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: the audit records behavioral claims, semantic clusters, authored artifacts, generated fanout, verification stories, rollback stories, dependencies, independent-mergeability judgments, review-load signals, findings, publication authorization, and a recommended review-unit sequence in one structured projection ([eval](evals/coherence-verdict/eval.toml))
- ALWAYS: the configured auditor is a thin read-only wrapper whose policy lives in the audit skill and whose result is the structured coherence-verdict JSON object ([audit])
- NEVER: a plugin-side helper, tracked file, rendered comment, or wrapper prompt becomes the source of coherence-verdict policy — the policy lives in the audit skill ([audit])
- ALWAYS: `/audit-changeset-coherence` names no caller and stays invocable on its own; the author context produces a verdict by dispatching the audit to a separate verifier context rather than grading its own work in place, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([audit])
