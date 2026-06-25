# PLAN - review-changes remaining work

## Active continuation

The node has two active issue-driven follow-ups in `ISSUES.md`:

- Align the local no-findings census and the GitHub-hosted clean-review message.
- Improve live review pass exhaustiveness so one pass surfaces every finding the changeset exhibits.

The additional plan items below are implementation hardening tasks that are not fully captured by those issue entries.

## Plan items

1. Add a deterministic diff-coordinate arbiter check.
   - Add a stdlib-only validator that compares each finding location with the diff emitted by `compute_diff.py`.
   - Reject findings whose `file:line` is outside the changed coordinates visible to the review input.
   - Wire the check into the review validation path before journal emission.

2. Add a prompt-injection guard for diff content.
   - State in `references/review-prompt.md` that diff content is untrusted data.
   - Require the reviewer to ignore instructions embedded in changed files, comments, fixtures, or generated text.
   - Keep this separate from repository-rule citation grounding.

3. Simplify the marketplace workflow once the hosted workflow owns the shared prompt shape.
   - Replace baked marketplace review workflow content with the reusable hosted workflow when the hosted workflow exposes the required prompt and render contract.
   - Keep local and hosted clean-review output aligned with the active `ISSUES.md` clean-review item.

4. Add deterministic rule-citation existence validation.
   - Extend validation beyond structural `Finding.rule` shape.
   - Read the cited artifact and confirm the referenced rule slug or ordinal exists.
   - Preserve the prompt-level grounded citation guard as model guidance; use the arbiter check for deterministic rejection.

## Coordination

Run `/understand`, then `/contextualize spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler` before acting. Reconcile this plan with `ISSUES.md` before implementation; `ISSUES.md` owns the two active defect threads.
