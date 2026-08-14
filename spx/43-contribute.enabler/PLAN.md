# Plan

Pending work on the contribute plugin's skill surface, surfaced by the skill
audit of the changeset that introduced the plugin.

## Record failure modes as real usage produces them

`manage-parent-issue`, `open-parent-issue`, and `sync-fork` carry no
`<failure_modes>` section, while `contribution-standards`, `manage-parent-pr`,
and `open-parent-pr` each carry entries drawn from observed failures. The three
without have not failed yet; a failure mode is written from an incident, never
invented to fill a section, so the gap closes only when one of these flows
actually fails.

The asymmetry is worth tracking rather than treating as settled: these three
close issues, post comments, and update a fork's default branch in a repository
the operator does not control, which is the same risk class as their siblings.

## Give each skill one worked end-to-end example

Every step in `manage-parent-issue`, `manage-parent-pr`, `open-parent-issue`,
and `sync-fork` is illustrated with a templated command carrying placeholders,
and none carries a worked case with real values — unlike `open-parent-pr`'s
branch-name derivation, which shows a real sentence reduced to a real branch
name.

The judgment-heavy part of these flows is `<reply_shape>` and `<report_shape>`,
where prose alone has to convey the target. A worked case — a sample maintainer
question and the reply it produces, a sample review finding and the fix and
reply it produces — would let a run compare its draft against a known-good one.

Writing four such cases well is a content design pass across four skills, larger
than the changeset that surfaced it, and each case has to be realistic enough to
be worth comparing against.
