# Issues: Apply

## The decision row is dispatched twice on a changeset that changes a decision

`src/plugins/spec-tree/skills/apply/SKILL.md` requires the ADR or PDR auditor at Step 4 whenever a decision changed, and names those same auditors again in the artifact-auditor gate's dispatch list. A changeset that changes a decision therefore launches its decision auditor twice, contradicting the once-per-kind rule the lane table states. Both generated copies under `dist/` render the same duplicate instruction.

**Evidence.** Finding F-001 of review run `2026-09-19_04-35-13-090-46287928ddf3` against `src/plugins/spec-tree/skills/apply/SKILL.md`.

**Settlement condition**: the artifact-auditor gate's dispatch list names neither `adr-auditor` nor `pdr-auditor`, leaving decision auditing to Step 4 alone.

**Why separate**: the dedup carries different evidence from the gate-taxonomy change that surfaced it, and repairing it inside that changeset would prejudge the split its Frame requires.
