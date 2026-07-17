# Changeset Coherence

PROVIDES an artifact-type audit that determines whether an exact committed changeset is one reviewable semantic unit and recommends dependency-ordered review units when it is not
SO THAT apply, publication, and merge workflows
CAN reject accumulated programs of work before expensive implementation audits and whole-changeset reviews

## Assertions

<!-- `/apply` owns verification-type and assertion-type selection for every assertion below. -->

- An exact committed changeset receives `APPROVED` only when its authored artifacts realize one behavioral outcome or inseparable semantic clusters with one verification story and one rollback story.
- An exact committed changeset receives `REJECTED` when two or more semantic clusters are independently mergeable, and the verdict returns a dependency-ordered review-unit sequence covering every authored artifact.
- A verdict receives `UNKNOWN` when behavioral claims, dependency evidence, generated-source relationships, verification evidence, rollback evidence, or repository calibration cannot be established; `UNKNOWN` never authorizes publication.
- Generated artifacts are collapsed onto their producing authored artifact before path breadth, authored-change size, or review load is assessed.
- Raw line count, file count, and review-load measurements trigger semantic scrutiny and never determine the verdict by themselves.
- The audit records behavioral claims, semantic clusters, authored artifacts, generated fanout, verification stories, rollback stories, dependencies, independent-mergeability judgments, review-load signals, findings, and a recommended review-unit sequence in one structured projection.
- The configured auditor is a thin read-only wrapper whose policy lives in the audit skill and whose durable result is an SPX verification-run projection.
