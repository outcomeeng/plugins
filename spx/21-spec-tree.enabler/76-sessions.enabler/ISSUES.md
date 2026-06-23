# Issues: Sessions Enabler

## 1. Pickup sessions can omit the required skills checklist

`spec-tree:pickup` requires a `<skills>` section to be presented before node context loads, but session `2026-06-22_14-38-40` contained no `<skills>` section. Pickup therefore had no authoritative handoff-provided list of required skills, missed skills, or the intended TDD-flow position, even though the workflow requires that checklist before continuing.

### Required handling

- Update the handoff session-format guidance so sessions always include a `<skills>` section with required skills, missed skills, and the next workflow position.
- Add tests or audits that reject a generated handoff session missing the checklist.
- Keep pickup behavior explicit when the section is absent: surface the gap as `Unverifiable` session metadata rather than inventing a checklist.
