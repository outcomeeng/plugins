# Merged record fix

The protocol lives at `probes/merged-record-fix/probe.md`, the target of the link on the slug of the `merged-record-fix` row in `../../changes.md`.

## Intent

A Leaf's record can need a fix after its Changeset has merged into the default branch: a path, a link, or a line that the merge made stale. The Operator reviewed the record's decision lines before Sliced. The uncertainty is whether such a fix keeps that review for every part the fix leaves unchanged, or whether the merge, which moved every `+` line onto the default branch, forces a new review of the whole record.

## Environment and preconditions

- A Leaf in the GitHub Change Store whose Changeset references it through `Refs:` trailers and has merged into the default branch.
- The Leaf's record composed as a Draft, and the stored record composed as the `--published` Draft.
- The `change-standards` form check as the default branch holds it, run from a checkout of the Product.
- The Product's Advisor, who audits the record before Applicable and at close.

## Protocol

1. Compose the stored record as a Draft. Write the fix into a second Draft that keeps the Base the latest advance to Sliced recorded.
2. Run the form check on the fix Draft with `--issue`, `--read-edited-at` and `--published`. Record its result.
3. Publish the fix through `author-change`, and make the `lower` Transition to Sliced, because the publish wrote the body of an Applicable record.
4. Ask the Advisor for the audit before Applicable of the fixed record. Record which lines it judges anew and which keep their earlier judgment.
5. Advance the Leaf to Applicable on that audit, then close it Applied after the audit at close.

## Attested run

- Date: 2026-11-22
- Subject: outcomeeng/changes#1009, whose Changeset merged as outcomeeng/plugins@183ea9bdc66569a2d67c1990328cdba21af836a1 (PR 783). Its latest advance to Sliced recorded Base 4ad9f6a3582c141ea1af3ae0dc8729205ad3797b.
- Step 1: the fix changes one Declarations line. The `form-check-merged-base` row under `spx/21-product-tree.enabler/79-changes.enabler` now links `tests/test_form_check_rows.compliance.l2.py`, as the row stands on the default branch. The Draft keeps Base 4ad9f6a358.
- Step 2: the form check passed. [form-check-sliced-base.json](form-check-sliced-base.json) holds its output, rerun after the publish with the edit stamp the publish left. The same check on a Draft whose Base moves to 183ea9bdc6 also passes, as [form-check-new-base.json](form-check-new-base.json) shows, because 1009's edits change rows whose slugs still stand at the new Base.
- Step 3: the body was published at 2026-11-22T01:36:56Z with the Base unchanged, and the `lower` Transition returned the record to Sliced.
- Step 4: the Advisor's run 2026-11-22_01-38-27-586-f4f1c36add89 is sealed approved with no finding, as [audit-run.json](audit-run.json) shows. Reading every line at the Sliced Base, it judged the one changed line, and every other line kept the judgment of its earlier approved run 2026-11-21_19-11-00-950-edf14b579e0c, byte-identical at the same Base and under the same Decision Records. No decision line changed, so the Operator's review of each decision line carried forward.
- Step 5: the Leaf advanced to Applicable on that run.

## Verdict

`passed`: the fix published at the Sliced Base. The Advisor's audit judged only the changed line and kept every unchanged line's judgment, and no decision line needed a new review from the Operator.

## Limitations

- The close Applied of step 5 follows the merge of the Changeset that adds this protocol, because the audit at close confirms that this Probe finds what it states. The Change Store records that close.
- The run fixed a Declarations line that is no decision line. A fix that changes a decision line takes the Operator's review of that line, which this run did not exercise.
- 1009's edits change slug rows. An edit of a plain line, which the form check reads at the Sliced Base only on a branch that carries the edit-line reading, is covered by the compliance cases of `form-check-merged-base`, not by this run.
