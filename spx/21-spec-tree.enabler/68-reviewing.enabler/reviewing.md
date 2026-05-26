# Reviewing

PROVIDES the reviewing verification kind — judgment-style assessment of a changeset for consistency among its specification, tests, and implementation and for the quality of each level
SO THAT developers reviewing their own changes before opening a pull request, and CI reviewing a branch against its base ref
CAN obtain a structured, arbiter-validated review — findings classified by one shared taxonomy — that stays comparable across every reviewing surface

## Assertions

### Compliance

- ALWAYS: a reviewing skill conforms to the verification contract in `spx/21-spec-tree.enabler/16-verification.enabler/verification.md` — one persistence model, one verification discipline, one wrapper-agent shape — so reviewing composes against the same machinery as every other verification kind ([review])
- ALWAYS: reviewing judges a changeset against a base ref for consistency among its specification, tests, and implementation and for the quality of each level — conformance to spec-tree authoring standards is auditing's concern and static analysis is validation's, each a separate verification kind ([review])
- ALWAYS: reviewing classifies every finding by the shared review taxonomy — one of three severities (`blocking`, `debt`, `follow_up`) paired with one of six concerns (`consistency`, `security`, `performance`, `evidence`, `standards`, `architecture`) per `REVIEW.template.md` — so findings stay comparable across every reviewing surface ([review])
- ALWAYS: a review carries findings only — no decision or verdict field — so each reviewing surface (the `REVIEW_READINESS` local gate, the `MERGE_READINESS` CI review, the author) applies its own policy and the reviewer never decides; the consumer acts by validity and phase per `spx/15-agent-pr-authority.pdr.md`, never by the finding's severity label ([review])
- NEVER: reviewing classifies a finding by a severity rank (`P0`–`P3`, `critical`/`high`/`medium`/`low`/`minor`/`nit`) or a legacy class label (`NEEDS-ANSWER`, `NOTE`) — the taxonomy is the three severities only; open questions are reframed as findings and bare commentary is omitted ([review])
