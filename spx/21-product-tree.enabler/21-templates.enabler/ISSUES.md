# Issues: Templates

Known defects, contradictions and gaps in this node.

## The lean PDR template describes no extension for normative-heavy decisions

The lean PDR template `src/plugins/product-tree/skills/understand/templates/decisions/decision-name.pdr.md` prescribes an opening of DEFINES and GOVERNS lines followed by `## Verification`, and carries no `## Rationale` and no `## Product properties` section. A normative-heavy decision needs decision-body sections and a longer statement of its reasoning, and the template describes no extension for them. [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md), approved by `/audit-pdr` after the operator's content-preservation review, stands as a documented deviation.

**Settlement condition.** The template describes an extension for normative-heavy decisions, naming that PDR as the reference. The decision side of this entry is in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/ISSUES.md`.

## DEBT: no fixture covers the levels script's missing-title error `outcomeeng/product_tree_levels.py` `MissingTitleError` `consistency`

**Evidence.** `_split_title_and_rest` in `outcomeeng/product_tree_levels.py` raises the named `MissingTitleError` for a document without a title line, and `_fenced_flags` keeps a `##` or `###` line inside a fenced code block from splitting a section. The `evaluate` directory under `outcomeeng_testing/fixtures/document_levels` holds a fenced markdown sample and covers the fence case. No fixture directory holds a title-less document, and `spx/21-product-tree.enabler/21-templates.enabler/tests/test_document_levels.mapping.l1.py` compares each fixture's derived views only, so no test reaches the `MissingTitleError` path. The CI review of pull request 734 on head `6f897c12272906b32a8d075821d0678a13311c84` reported the original defects, and the maintainer ruled the finding accepted because the script stays a proof of concept.

**Impact.** A change to the title scan could drop the named error without a failing test. The templates in the form hold no title-less shape, so no document the node governs reaches the path.

**Settlement condition.** A fixture directory holds a document without a title line, and a test asserts that the script raises `MissingTitleError` for it.

## DEBT: the levels-probe retained artifacts predate the changed examples and levels script `spx/21-product-tree.enabler/21-templates.enabler/templates.md` `levels-probe` [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md)

**Evidence.** The levels-probe row in `spx/21-product-tree.enabler/21-templates.enabler/templates.md` states that an attested run retains the level 2 view of the PDR and capability examples and of a spec holding an Evaluate subsection, the Evaluate case column included. The protocol `spx/21-product-tree.enabler/21-templates.enabler/probes/levels-probe/probe.md` names only the PDR and capability examples in its Observations, Limitations and retained artifacts (`pdr-example.level-2.txt`, `capability-example.level-2.txt`). Neither retained artifact holds an Evaluate heading, and both show the form that the changed examples and the changed levels script no longer produce: `### Scenario: capture` with one-line Given/When/Then rows, `### Probe` and `### Audit` without subjects, and `ALWAYS:` with a colon. The script run at level 2 over the changed capability example renders its Scenario rows as the slug line alone, which `capability-example.level-2.txt` does not show. The review run `run-2026-11-16_02-17-00-409-774650bc15a4` reported the finding as F-001, and the Plugins Maintainer ruled it accepted.

**Impact.** The row claims coverage that no executed protocol or retained artifact supplies, and the retained views disagree with the script's current output for the same examples. A reader of the retained views sees a form the templates no longer hold.

**Settlement condition.** A fresh attested run of levels-probe over the changed PDR and capability examples and over a spec holding an Evaluate subsection retains each level 2 view beside `probe.md`, and `probe.md` states the matching observations, artifacts and limitations.
