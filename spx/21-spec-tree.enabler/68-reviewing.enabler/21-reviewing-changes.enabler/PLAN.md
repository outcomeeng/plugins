# PLAN - review-changes hardening

The remaining tasks below harden the current `review-changes` implementation. They are implementation work, not active issue-driven defects.

## Plan items

1. Add deterministic diff-coordinate validation.
   - Add a stdlib-only validator that compares each finding location with the diff emitted by `compute_diff.py`.
   - Reject findings whose `file:line` is outside the changed coordinates visible to the review input.
   - Wire the check into the existing per-finding validation path before journal emission.

2. Add a prompt-injection guard for diff content.
   - State in `references/review-prompt.md` that diff content is untrusted data.
   - Require the reviewer to ignore instructions embedded in changed files, comments, fixtures, or generated text.
   - Keep this separate from repository-rule citation grounding.

## Coordination

Run `/understand`, then `/contextualize spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler` before acting. Verify each item against the current review prompt, policy module, journal adapter, and tests before implementation.
