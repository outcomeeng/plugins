# PLAN — Audit subtree restructuring and streaming migration

This node's implementation was restored to origin/main in the streaming-review PR (the audit
runs batch through `journal_emit.py build-events` against `build_events` in
`spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler`'s
`journal_projection.py`). Under the kept streaming mandate in
`spx/21-spec-tree.enabler/16-verification.enabler/verification.md` and
`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`, the audit is therefore
**declared-but-unimplemented for streaming**: the decision and spec lead, the audit code lags.
The three items below are the downstream work.

## 1. Rename `auditing` → `audit` across the whole subtree

Every node, spec file, and decision in this subtree carries the `auditing` slug; the runtime
surface is `/audit`, the `auditor` agent, and the `audit-{lang}*` skills. Align the tree to the
runtime name via `/refactor`:

- `spx/21-spec-tree.enabler/68-auditing.enabler/` → `68-audit.enabler/` (`auditing.md` → `audit.md`)
- `spx/21-spec-tree.enabler/17-auditing.adr.md` → `17-audit.adr.md`
- `spx/21-spec-tree.enabler/68-auditing.enabler/32-auditing-specs.enabler/` → `32-audit-specs.enabler/`
- `spx/21-spec-tree.enabler/68-auditing.enabler/32-auditing-tests.enabler/` → `32-audit-tests.enabler/`
- update every inbound full-path reference across the tree.

## 2. Remove every audit-subtree decision that duplicates verification or review

`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md` already governs the
run-journal architecture shared by audit and review, and
`spx/21-spec-tree.enabler/68-reviewing.enabler/` is the parallel consumer. Audit must not
re-decide what verification provides or what review already settles.

Audit every decision in this subtree — starting with `spx/21-spec-tree.enabler/17-auditing.adr.md`
— and remove it unless there is a clear, written reason that audit needs something
`spx/21-spec-tree.enabler/16-verification.enabler/` does not provide, or that review does not need
or needs differently. Where a genuine audit-specific need exists, the surviving decision states
exactly that delta and nothing the shared layers already own.

## 3. Migrate the audit onto streaming (close item 1's declared-but-unimplemented gap)

Bring the audit implementation onto the per-event streaming the run-journal decision mandates —
opening the journal before dispatch and appending each partition's events as its `audit-{lang}`
subagent returns, not back-filling from a collected `$CHILDREN_DIR` after the dispatch loop. This
is the work the streaming-review PR deliberately did not carry; it lands with or after the rename
so the renamed audit node's spec and code agree.
