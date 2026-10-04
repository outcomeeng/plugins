# Issues

## The delta-only assertion has no cross-sibling enforcement gate

`test-verification.md` asserts that every language-specific test-standard node cites this node and `15-test-infrastructure.pdr.md` and declares only its language delta, never restating or weakening the seam rules this node owns ([audit]). No gate enforces that assertion across the sibling language nodes. The changeset reviewer (`spec-tree:changes-reviewer`), the per-language artifact auditors (`audit-{python,rust,typescript}-{tests,code,architecture}`), and `/align` each judge one node or one changeset in isolation; none compares `spx/43-python.enabler`, `spx/43-rust.enabler`, and `spx/43-typescript.enabler` against this superset or against each other. A future edit that restates a superset rule inside a language node, or lets two language nodes diverge, passes every gate — the same blind spot that let the pre-superset duplication reach the default branch unflagged.

**Resolution shape** (fix deferred by operator decision, to be scoped in the skill and agent specialization work): add cross-sibling equivalence detection to the gate set — an `/align` check that every language test-standard node cites this node and declares only deltas, an audit assertion on each language node verifying delta-only content against the cited superset, or a review dimension that compares sibling language standards.

**Evidence.** Named by the operator after observing that the seam specs of all three languages were extremely repetitive and that no auditor or changeset reviewer flagged the repetition across the changeset that carried it.

## Accepted adversarial-review findings against the shipped test-skill families

An adversarial review of the merged PR #519 changeset (`988af420b503b010d85bda6e0afa3a748b5929b5..c42fceef6ef807429e7047d043e517b5e468df0d`) produced nine valid findings; the closing verification of their spec-layer fixes is the sealed review run `2026-08-14_14-34-24-824-a1416573df24`, and the remaining findings below are verifiable directly in the shipped surfaces they name. The five spec-layer findings are resolved: the level discriminator with its boundary rewording of scenario cases 4 and 5, the provenance-bound construction laws with rejected mapping case 25, the default-runner obligation with the pytest and Vitest declarations, the assertion-type taxonomy word at the spec sites, and the realization-only rewrite of both language execution-level delta lines.

Two skill-family findings remain:

- The shipped `/audit-tests` skill does not consume the shared standard's evidence-cell criteria: it loads the legacy rule families only, extracts no declared execution level from the filename, and its finding schema carries no execution-level or filename property — a test declaring `l1` while reaching a remote dependency can still be approved. Fold the audit step and verdict-schema extension for the filename, level-floor, harness, availability, and type-permission criteria into the operator-parked audit-tests rebuild that derives graded cases from the corpus decision. Deferred as a separate larger concern because it changes the audit methodology, its verdict schema, and its eval suites together. Surfaced by the PR #522 current-head review (head 16f35be0428979373d0865e97463dacd9bb1e41b).
- The TypeScript predicate-in-harness sites and the blanket binding ban are already owned by `spx/43-typescript.enabler/25-typescript-standards.enabler/ISSUES.md` and get no second record here.

## The test-infrastructure PDR departs from the lean decision template

`15-test-infrastructure.pdr.md` is migrated to the lean decision template and keeps its `## Product properties` cap of three items, but departs from the template's four-section shape in two ways its normative substance forces: three decision-body sections (`## Category Semantics`, `## Evidence Chain`, `## Spec Traceability`) between the opening statement and `## Rationale`, and a multi-paragraph `## Rationale` that absorbs the former context and trade-offs content, trade-offs table included. The per-language path table, the category tables, the evidence-chain rules, traceability and the folded reasoning are the decision itself and have no home in the minimal shape. `/audit-pdr` approved the migrated structure, and the operator completed the human content-preservation review against the pre-migration revision. The lean PDR template in `src/plugins/spec-tree/skills/understand/templates/decisions/decision-name.pdr.md` describes no extension for normative-heavy decisions.

**Settlement condition.** The lean PDR template describes an extension for normative-heavy decisions, with decision-body sections and a longer Rationale and this PDR as the reference, or the PDR restructures into the minimal four-section shape without losing normative content. Until then the PDR stands as a documented deviation. The template side of this entry is in `spx/21-spec-tree.enabler/21-templates.enabler/ISSUES.md`.

## Two Verifier rules collide on pinning a spec-declared tuning value

The changes-reviewer requires a test to pin `SIGNAL_GRACE_SECONDS` to the spec's two-second grace period with an independent literal, citing the mutation-check rule in `15-test-infrastructure.pdr.md`. The test-evidence-auditor rejects exactly that literal as a source-ownership violation, citing `spx/12-shipped-scripting.adr.md`: a test restating a spec-declared value is a second declaration whose agreement is audit evidence. The operator ruled that the ADR governs: no literal pin, the spec-to-constant agreement stays audit evidence, and the reviewer finding is dropped as unbacked.

**Settlement condition.** One of the two decisions is amended so they compose: the mutation-check rule excludes spec-declared values whose agreement the ADR routes to audit, or the ADR carves an exception for magnitude pins, so a reviewer and an evidence auditor reading both reach one verdict.

**Evidence.** Review runs `2026-08-31_00-51-25-312-913144ba274d`, `2026-08-31_00-56-11-491-d5964232aade` and `2026-08-31_01-31-25-945-65d0eb76b2fc` (blocking) each requested the pin; evidence-audit verdicts on heads `629c24b790980aefa873ee6ffd4212e5f8611151` and `4ede96f0d1cb1c3855792f6c04bcca2c65e3e1ee` rejected or upheld removal of the same literal; the operator ruling is in the PR #549 body. `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/ISSUES.md` records the reviewer side.

## The evidence-types decision carries ten audit rules

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md` carries 10 audit rules, past the roughly-7 signal in `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md`. The count is accepted: the rules are one decision's verification surface over one subject, the assertion-type by execution-level cross-product, and its cell-composition rule binds the per-type sections to the level semantics. Splitting execution-level rules from per-type permission rules would separate the composition from the sections it composes and re-open the per-language divergence the decision exists to close. A Verifier skips this decomposition signal.

## The test-verification spec is a deliberate superset node

`test-verification.md` carries roughly 24 Compliance assertions, past the same signal. The node is the single language-neutral superset of the test-evidence seam rules, and every language test-standard node cites it and declares only its language delta. Decomposing the superset into per-concern children would re-fragment the union the design unifies, and language nodes would cite a parent whose rules are spread across children, reintroducing the cross-language drift the superset removes. A Verifier skips this decomposition signal.
