# Issues: Apply

## The decision row is dispatched twice on a changeset that changes a decision

`src/plugins/spec-tree/skills/apply/SKILL.md` requires the ADR or PDR auditor at Step 4 whenever a decision changed, and names those same auditors again in the artifact-auditor gate's dispatch list. A changeset that changes a decision therefore launches its decision auditor twice, contradicting the once-per-kind rule the lane table states. Both generated copies under `dist/` render the same duplicate instruction.

**Evidence.** Finding F-001 of review run `2026-09-19_04-35-13-090-46287928ddf3` against `src/plugins/spec-tree/skills/apply/SKILL.md`.

**Settlement condition**: the artifact-auditor gate's dispatch list names neither `adr-auditor` nor `pdr-auditor`, leaving decision auditing to Step 4 alone.

**Why separate**: the dedup carries different evidence from the gate-taxonomy change that surfaced it, and repairing it inside that changeset would prejudge the split its Frame requires.

## The apply skill's eager payload exceeds the progressive-disclosure ceiling

`src/plugins/spec-tree/skills/apply/SKILL.md` renders to 47,850 code points under `dist/claude/` and a comparable size under `dist/codex/`, entirely eager, with no `references/` directory in the bundle. `/skill-standards` `<progressive_disclosure>` sets a 40,000-code-point ceiling for a skill invoking the eager-foundation exception; the 500-line limit is met only because the lines are long. A directive-description skill that activates on every implementation-shaped prompt pays that payload on every load, false activations included.

**Evidence.** Finding f-007 of the skill audit of `src/plugins/spec-tree/skills/apply/SKILL.md`. The same render measures 41,147 code points at `origin/main` commit `e27435f7f3a97aecd5bc366c893551f11e796e64`, so the breach precedes this branch.

**Settlement condition**: the rendered skill measures at or below 40,000 code points, with the conditional operational detail no invocation needs at trigger time — the verification-checkpoint record contract, the launch-contract repair rules, the result-carryover projection, and Step 7a's result branches — loaded from cited `references/` files at the step that consumes each.

**Why separate**: moving four sections into a new `references/` directory restructures the skill's information architecture rather than amending the lines that carry a rule, and the restructured surface needs its own skill audit.
