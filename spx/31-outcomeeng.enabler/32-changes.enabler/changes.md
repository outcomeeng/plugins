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
- Persistence maps every front-matter field to the configured coordination store's native features and reads every field back unchanged; a store limit never shapes the record, and the persistence skill instruction selects the client for the configured store.
- A record whose front matter does not carry the contract's closed key set is outside the contract; it receives no migration, alias, inferred front matter, body-line lineage interpretation, or audit verdict, and the auditor reports it as outside the contract.
- `claim-change` claims only an `Available` record: it adds the holder, records the Claim, and moves Lifecycle `Available` to `Claimed`, writing neither Maturity nor any body section; any other Lifecycle, an existing holder, or a field mismatch is reported without mutation.
- `release-change` writes the Handoff into the Change — branch or changeset, completed and next Activities, blockers, and hazards, never a secret — removes the holder, moves Lifecycle `Claimed` to `Available`, and leaves Maturity unchanged, so any agent may claim the Change next.
- `close-change` takes the terminal Lifecycle as its one argument, refuses any value outside `Applied`, `Refined`, and `Abandoned`, refuses `Refined` while a known successor is absent from the store, and moves `Claimed` to the named value after writing the terminal record.
- The plugin ships no `/pickup`, `/handoff`, or `/issue` skill and no session-queue entry path; a follow-up is a Proposed Change created through `author-change`.
