# Merged record fix

The protocol lives at `probes/merged-record-fix/probe.md`, the target of the link on the slug of the `merged-record-fix` row in `../../changes.md`.

## Intent

A Leaf's record can need a fix after its Changeset has merged into the default branch: a path, a link, or a line that the merge made stale. The Operator reviewed the record's decision lines before Sliced. The uncertainty is whether such a fix keeps that review for every part the fix leaves unchanged, and whether the Leaf still closes Applied, or whether the merge, which moved every `+` line onto the default branch, forces a new review of the whole record.

## Environment and preconditions

- A Leaf in the GitHub Change Store whose Changeset references it and has merged into the default branch.
- The Leaf's record composed as a Draft, and the stored record composed as the `--published` Draft.
- The `change-standards` form check as the default branch holds it, run from a checkout of the Product.
- The Product's Advisor, who audits the record before Applicable and at close.

## Protocol

1. Compose the stored record as a Draft. Write the fix into a second Draft that keeps the Base the latest advance to Sliced recorded.
2. Run the form check on the fix Draft with `--issue`, `--read-edited-at` and `--published`. Record its result.
3. Publish the fix through `author-change`. When the record was Applicable, make the `lower` Transition to Sliced, because the publish wrote its body.
4. Ask the Advisor for an audit of the fixed record. Record which lines it judges anew and which keep their earlier judgment.
5. Ask the Advisor for the audit at close. On its approval, close the Leaf Applied through `manage-change` on the merged Changeset.

## Attested run

- Date: 2026-11-22

Observation 1, the whole chain on outcomeeng/changes#1005:

- Its Changeset merged as outcomeeng/plugins@326cb8b54fd1b0e8ee638d53cf012806a3f24199 (PR 780) at 2026-11-18T11:38:47Z.
- After the merge, publishes at 2026-11-18T12:45:53Z and 12:56:06Z fixed its record's Verification line, after an earlier audit at close had rejected that line. No decision line changed. The first publish lowered the record from Applicable to Sliced, as its [lower Transition](https://github.com/outcomeeng/changes/issues/1005#issuecomment-6978933329) records.
- The Advisor's audit at close, run 2026-11-22_00-21-47-752-938fd6035fe5, judged the fixed record against the default branch and is sealed approved with no finding, as [1005-audit-at-close.json](1005-audit-at-close.json) shows.
- The Leaf closed Applied at 2026-11-22T00:31:42Z on the merged Changeset, as its [applied Transition](https://github.com/outcomeeng/changes/issues/1005#issuecomment-7071609415) records.

Observation 2, the kept review on outcomeeng/changes#1009:

- Its Changeset merged as outcomeeng/plugins@183ea9bdc66569a2d67c1990328cdba21af836a1 (PR 783). Its latest advance to Sliced recorded Base 4ad9f6a3582c141ea1af3ae0dc8729205ad3797b.
- Step 1: the fix changes one Declarations line. The `form-check-merged-base` row under `spx/21-product-tree.enabler/79-changes.enabler` now links `tests/test_form_check_rows.compliance.l2.py`, as the row stands on the default branch. The Draft keeps Base 4ad9f6a358.
- Step 2: the form check passed. [form-check-sliced-base.json](form-check-sliced-base.json) holds its output, rerun after the publish with the edit stamp the publish left. The same check on a Draft whose Base moves to 183ea9bdc6 also passes, as [form-check-new-base.json](form-check-new-base.json) shows, because 1009's edits change rows whose slugs still stand at the new Base.
- Step 3: the body was published at 2026-11-22T01:36:56Z with the Base unchanged, and the `lower` Transition returned the record to Sliced.
- Step 4: the Advisor's run 2026-11-22_01-38-27-586-f4f1c36add89 is sealed approved with no finding, as [audit-run.json](audit-run.json) shows. Reading every line at the Sliced Base, it judged the one changed line, and every other line kept the judgment of its earlier approved run 2026-11-21_19-11-00-950-edf14b579e0c, byte-identical at the same Base and under the same Decision Records. No decision line changed, so the Operator's review of each decision line carried forward.

## Verdict

`passed`: outcomeeng/changes#1005, a Leaf whose Changeset merged and whose record publishes after the merge fixed, closed Applied after an audit at close that found nothing, with no new review of a decision line. On outcomeeng/changes#1009, the audit of a fix published after the merge judged only the changed line and kept every unchanged line's judgment.

## Limitations

- Both fixes changed lines that are no decision line. A fix that changes a decision line takes the Operator's review of that line, which neither run exercised.
- Both runs fixed slug rows or the Statement of Intent. An edit of a plain line in a Decision Record, which the form check reads at the new Base, was not exercised.
