---
id: 01a0b1fc-579f-7092-98af-601f9780d693
malleability: spec
---

# Changes

PROVIDES the Change coordination contract for defining, maturing, persisting, authoring, and auditing one intended Output
SO THAT product engineers and agent sessions coordinating work
CAN move a prioritized Output from proposal to executable work without placing mutable work state in product truth

## Assertions

- A Change record has YAML front matter with the closed key set `title`, `product`, `maturity`, `lifecycle`, `refined_from`, and `blocked_by`, plus a body with fixed top-level sections; every key is required, and an unknown key is a defect.
- `change-standards` carries one independently loadable Definition of Ready for each Maturity level: Proposed, Framed, Sliced, and Executable.
- `author-change` runs one workflow per Maturity level; each workflow loads only that level's Definition of Ready and advances Maturity only when the Definition of Ready holds and the level's authority is present.
- `audit-change` reads the complete record front matter first, judges one record against the Definition of Ready for its declared Maturity, and emits a structured Agentic verdict under `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`.
- Persistence maps every front-matter field to the coordination store's native features through `gh` and reads every field back with the same value; the record depends on no store feature, and the persistence step remains a skill instruction.
- A Change record authored outside this contract is outside `audit-change` and receives no compatibility interpretation or migration.
