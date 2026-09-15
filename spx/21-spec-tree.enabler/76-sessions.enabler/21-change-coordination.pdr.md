# Change Coordination

A Change stores Product, Maturity, and Status only in its Changes project fields; its issue body stores the Output and refinement content, comments store Claim and Handoff records, and the assignee represents the current holder. Every lifecycle transition writes its canonical fields in a declared order and verifies the complete resulting state before the workflow continues.

## Rationale

One canonical home per mutable fact prevents issue prose, project fields, comments, and assignee state from disagreeing silently. Ordered writes with complete readback make partial transitions visible and recoverable.

## Product properties

1. Product, Maturity, and Status are canonical project fields; the body, comments, and assignee carry only their declared content.
2. Creation, refinement, claim, release, and terminal closure expose a complete, verified state or stop with a diagnostic naming completed writes, the failed operation, and observed state.
3. Legacy body metadata is removed only after project fields are verified, with conflicting field values reconstructed from issue history before removal.

## Verification

### Audit

- ALWAYS: Change creation adds the issue to the Changes project, writes Product, writes Maturity as Proposed, writes Status as Available, and verifies all three fields plus an empty assignee state before publishing a Handoff ([audit])
- ALWAYS: in-place refinement updates the issue body, writes the target Maturity, reasserts Status as Available, and verifies Product, Maturity, Status, and an empty assignee state before continuing ([audit])
- ALWAYS: pickup verifies Product, Maturity, Status as Available, and an empty holder; adds the assignee; posts the earliest Claim after the latest release; writes Status as Claimed; and verifies the three fields, assignee, and Claim before executing an Activity ([audit])
- ALWAYS: release posts the canonical Handoff, removes the assignee, writes Status as Available, and verifies the three fields, empty assignee state, and latest Handoff before completing ([audit])
- ALWAYS: terminal application, successor refinement, and abandonment write Applied, Refined, or Abandoned through the same ordered write, authorized-record, and complete-readback protocol ([audit])
- NEVER: a Change transition performs a later mutation after a required write fails or readback differs from the intended state; its diagnostic names every completed write, the failed operation, and the observed partial state ([audit])
- NEVER: a new or refined Change body carries Product, Maturity, Lifecycle, or Status metadata; legacy body metadata is removed only after the canonical fields are verified, and a conflict is reconstructed from issue history before removal ([audit])
