---
id: 01a0b1fc-579f-7092-98af-601f9780d693
malleability: spec
---

# Changes

PROVIDES the Change coordination contract for defining, maturing, persisting, authoring, and auditing one intended Output
SO THAT product engineers and agent sessions coordinating work
CAN move a prioritized Output from proposal to executable work without placing mutable work state in product truth

## Assertions

- A Change record has YAML front matter with the closed key set `title`, `product`, `maturity`, `lifecycle`, `refined_from`, and `blocked_by`, plus a body that opens with `## Intent` and adds the sections each Maturity requires; every key is required, and an unknown key is a defect.
- `change-standards` carries one independently loadable Definition of Ready for each Maturity level: Proposed, Framed, Sliced, and Executable.
- No Definition of Ready requires an operator review statement at Proposed, and each Definition of Ready is the complete criterion set for its Maturity.
- `change-standards` selects the 4.0 Change chapter — `versions/4.0/methodology/change/changes.md` inside the declared `methodology.source` — for a `methodology.version` declaration of `4.0` or `4.0.N` with `N` a non-negative integer, states that comparison, and rejects every other declaration.
- `author-change` runs one workflow per Maturity level; each workflow loads only that level's Definition of Ready and advances Maturity only when the Definition of Ready holds and the store shows the Product's Maintainer's move of the Change out of `Submitted` at the Maturity it leaves, which is the authority for that Maturity.
- `author-change`'s Executable workflow derives the Frame's selected `VERIFICATION_READINESS` predicates, result obligations with their producers, and decision-record audits from the merge composition the selected methodology states for the changeset, and writes each verification Activity to cite that statement.
- `audit-change` reads the complete record front matter first, judges one record against the Definition of Ready for its declared Maturity, and emits a structured Agentic verdict under `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`, whose result carries the run token, the rendered projection's run-level fields, every finding payload verbatim, and the one command that reproduces the complete rendered projection from the sealed run.
- `audit-change` rejects an Executable record whose selected `VERIFICATION_READINESS` predicates, result obligations, or decision-record audits disagree with what the merge composition selects for the changeset, or whose evidence obligations name a Verifier outside them.
- ALWAYS: `audit-change` reaches the candidate, every repository path, and the SPX store only through its bundled Python runner, and never invokes `rm`, `mktemp`, a shell redirect to a file, or one of its scripts other than as the runner invocation the skill prescribes.
- ALWAYS: `audit-change` issues each runner invocation as its own command, never chained with `&&` or `;` and never piped into a command that masks its exit status, and a nonzero runner exit stops the audit with a blocked result naming the request and the exit status.
- NEVER: `audit-change` or its `change-auditor` wrapper writes a file; every payload passes over stdin and stdout, and the SPX run journal holds the run.
- Persistence writes each front-matter field to its one home in the configured store and reads each back unchanged; the store body carries the Intent and the sections its Maturity adds, without front matter, no field is written to a second home, a store limit never shapes the record, and the persistence skill instruction selects the client for the configured store.
- A record whose front matter does not carry the contract's closed key set is outside the contract; it receives no migration, alias, inferred front matter, body-line lineage interpretation, or audit verdict, and the Auditor reports it as outside the contract.
- `claim-change` claims only an `Available` record: it adds the holder, records the Claim naming the claiming session and the worktree root the Change is claimed for — the session's own assigned root, or a root it names — and moves Lifecycle `Available` to `Claimed`, writing neither Maturity nor any body section; any other Lifecycle, an existing holder, or a field mismatch is reported without mutation.
- `release-change` writes the Handoff into the Change — branch or changeset, completed and next Activities, blockers, and hazards, never a secret — removes the holder, moves Lifecycle `Claimed` to `Available`, or to `Submitted` for its `submit` result, and leaves Maturity unchanged, so any agent session may claim an `Available` Change next; it runs only for a session whose assigned worktree root equals the winning Claim's, and reports any other caller without mutation.
- `close-change` takes the terminal Lifecycle as its one argument, refuses any value outside `Applied`, `Refined`, and `Abandoned`, refuses `Refined` while no successor exists in the store, a known successor is absent from it, or a successor does not name this Change in `refined_from`, and moves `Claimed` to the named value after writing the terminal record; it runs only for a session whose assigned worktree root equals the winning Claim's, and reports any other caller without mutation.
- The plugin ships no `/pickup`, `/handoff`, or `/issue` skill and no session-queue entry path; a follow-up is a Proposed Change created through `author-change`.

### Compliance

- NEVER: the bundled Python runner of `audit-change` writes a file; each invocation reads one JSON request on stdin and writes one JSON result on stdout, and the SPX run journal is the only state that persists between requests ([test](tests/test_audit_change_run.compliance.l1.py))
- `confirm-change` moves a `Submitted` Change to `Available`, posting one comment that records the confirmation or the rejection with its reason and names the delegate, the operator it acts for, its agent harness, and its agent session; it writes no Maturity and no body section, and reports any other Lifecycle without mutation ([audit]).
- `audit-change` reads every authority event from the store's field-change events and confirmation comments, never from the body, and judges a record carrying body authority text as defective ([audit]).
- The `audit-change` runner's `read-authority` operation reads a Change's field-change events and comments at 100 per page and at most 10 pages, and returns a blocked result naming the bound when the read fills it ([test](tests/test_audit_change_authority.compliance.l1.py)).
