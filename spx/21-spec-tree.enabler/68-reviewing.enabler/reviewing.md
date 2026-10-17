---
id: 01a0ebba-5f68-71ca-ab5a-263c04ba74f4
malleability: spec
---

# Reviewing

PROVIDES the review verification kind — judgment-style assessment of a changeset for consistency among its specification, tests, and implementation and for the quality of each level
SO THAT developers reviewing their own changes before opening a pull request, and CI reviewing a branch against its base ref
CAN obtain a structured, schema-validated review — findings classified by one shared taxonomy — that stays comparable across every review surface

## Assertions

### Compliance

- ALWAYS: a review skill conforms to the verification contract in `spx/21-spec-tree.enabler/16-verification.enabler/verification.md` — one persistence model, one verification discipline, one wrapper-agent shape — so review composes against the same machinery as every other verification kind ([audit])
- ALWAYS: review judges a changeset against a base ref for consistency among its specification, tests, and implementation and for the quality of each level — authored-instruction conformance belongs to the audit kind and static analysis belongs to the validate kind, each a separate verification kind ([audit])
- ALWAYS: review classifies every finding by the shared review taxonomy — one of two severities (`blocking`, `debt`) paired with one of five concerns (`consistency`, `security`, `performance`, `evidence`, `architecture`) per [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) — so findings stay comparable across every review surface ([audit])
- ALWAYS: a review carries findings only — no decision or verdict field — so each review surface (the local review predicate inside `VERIFICATION_READINESS`, the `MERGE_READINESS` CI review, the Author) applies its own policy and the Reviewer never decides; the consumer acts on a `blocking` finding by validity and phase and on a `debt` finding by its ruling, per [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) ([audit])
- ALWAYS: the Reviewer judges finding validity and severity; the Author judges the disposition of each `blocking` finding, and a `debt` finding on text the changeset touches or invalidates takes its disposition — fix, accept, or drop — from the ruling of a position above the changeset's author, per [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) ([audit])
- ALWAYS: a review labels `TRACKED` each `debt` finding whose entry key the governing node's `ISSUES.md` records, a `TRACKED` finding blocks nothing, and the label stands beside the severity, never as a third severity, per [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) ([audit])
- NEVER: review classifies a finding by a third scope-shaped severity (`follow_up`), a severity rank (`P0`–`P3`, `critical`/`high`/`medium`/`low`/`minor`/`nit`), or a legacy class label (`NEEDS-ANSWER`, `NOTE`) — the taxonomy is the two severities only; open questions are reframed as findings and bare commentary is omitted ([audit])
