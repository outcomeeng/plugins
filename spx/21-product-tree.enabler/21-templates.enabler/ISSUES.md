# Issues: Templates

Known defects, contradictions and gaps in this node.

## The lean PDR template describes no extension for normative-heavy decisions

The lean PDR template `src/plugins/product-tree/skills/understand/templates/decisions/decision-name.pdr.md` prescribes an opening of DEFINES and GOVERNS lines followed by `## Verification`, and carries no `## Rationale` and no `## Product properties` section. A normative-heavy decision needs decision-body sections and a longer statement of its reasoning, and the template describes no extension for them. [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md), approved by `/audit-pdr` after the operator's content-preservation review, stands as a documented deviation.

**Settlement condition.** The template describes an extension for normative-heavy decisions, naming that PDR as the reference. The decision side of this entry is in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/ISSUES.md`.

## DEBT: the levels script fails on a missing title and splits fenced headings `outcomeeng/product_tree_levels.py` `_split_title_and_rest` `consistency`

**Evidence.** `_split_title_and_rest` in `outcomeeng/product_tree_levels.py` selects the first `#` line with `next(...)` and no default, so a document without a title line raises a bare `StopIteration`. `_is_heading` treats a `##` or `###` line inside a fenced code block as a heading, so a rule or example that holds a fenced markdown sample splits into bogus sections at levels 1 and 2. The CI review of pull request 734 on head `6f897c12272906b32a8d075821d0678a13311c84` reported both, and the maintainer ruled the finding accepted because the script stays a proof of concept.

**Impact.** The script fails with an unnamed error on a title-less file and misreads a document that fences headings. The templates in the form hold neither shape, so no document the node governs reaches either path.

**Settlement condition.** The script raises a named error for a missing title, tracks code fences while it scans headings, and a fixture directory covers each case.
