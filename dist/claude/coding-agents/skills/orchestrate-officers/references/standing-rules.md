# Orchestrating-session standing rules

These rules govern the session that supervises officers. Each officer remains
the Executor of its own Change; the orchestrating session holds none of that
Change's Refiner, Executor, Author, Fixer, or Verifier roles.

## Autonomous and held decisions

The orchestrating session assumes the operator is away. One escalation holds
one decision while the rest of the fleet continues.

Proceed autonomously in exactly these three decision classes, recording the
reasoning in the per-Change ledger:

1. At the two-round ceiling, choose among splitting the changeset, tracking the
   branch and findings while resuming the next Activity, or stopping.
2. Hold a deploy or release whose required external state is absent.
3. Order reversion of an edit outside the Change Frame.

Wait for the operator's word in exactly these four decision classes:

1. a third Verifier pass
2. a raised expense ceiling
3. a Change Frame amendment
4. a product-intent conflict

Before endorsing an officer proposal or escalating a Verifier finding, restate
the governing rule from loaded decisions and specs and judge every term of the
proposal or finding against that rule.

Decide an officer's question in the same read that raised it. Before going
idle, read every officer pane; a quiet inbox does not prove that no pane is
waiting at a prompt.

## Verifier launch failures

A Verifier result of `BLOCKED` is unusable unless it carries command evidence:
an exit code and stderr, a named termination, or a harness-tool failure. Report
an unusable result and never relaunch the Verifier. One fresh dispatch occurs
only on the orchestrating session's word.

A harness denial of a Verifier launch is also unusable. Report the denial; the
orchestrating session runs that verification from its own worktree.

## Durable facts and the `filed` disposition

Every accepted defect has one disposition. Until the declared Change store's
record for durable `filed` dispositions reaches Applied and the repository's
required version floor includes that capability, use the prose disposition
`filed` when a defect-owning `ISSUES.md` entry records the defect and its
settlement condition. While the verification journal records that disposition
as normal, do not raise the same finding again. Preserve the issue path and
finding provenance in the ledger. Re-evaluate this temporary prose rule when
that Change and floor condition are both satisfied.

Mail every full commit SHA and every verdict with its complete verification run
identity before compaction. Reuse a Verifier verdict for a byte-identical
subject. After a rebase, reuse it only when the repository's preservation proof
establishes an unchanged branch diff, unrelated base movement, and every extra
condition in the merge overlay; run the narrower validation required for the
base delta.

Post feedback on a Change as an unprefixed comment in the declared Change
store. Mail carries the bell and record pointer, never the feedback body.

A repair never weakens a spec assertion to fit its evidence. When evidence does
not reach one clause, preserve the clause as its own assertion rather than
deleting it.

## Ledger derivation

The per-Change ledger contains passes, full heads, verdicts, finding provenance,
reads with their cause, running spend, and wall time. It is derived from
agent-mail records and sealed verification-journal runs, never treated as an
independent source of truth. Rebuild it after compaction or restart with
`${CLAUDE_SKILL_DIR}/scripts/derive_ledger.py` through that script's documented
`derive` entry point. Spend and wall time are courtesy fields rather than
gates.

For machine-readable ledger facts, place a JSON object under a message record's
body with a `ledger` object. The ledger object can carry `pass`, `head`,
`verdict`, `findingProvenance`, `read`, `spend`, and `wallTimeSeconds`. A read
records one of these causes: `message`, `officer-state-change`, `bound-crossed`,
or `operator-cadence`. The derivation script also consumes sealed journal run
objects directly and keeps source provenance with every derived entry.

## Event reads and lifecycle

Read after a message, an officer state change, a crossed bound, or a cadence the
operator names. The session owns no self-chosen timer and creates no polling
loop. A read without a change remains quiet unless the operator requested a
report.

The orchestrating session owns launch, order, close, compaction, restart, and
Change disposal for every officer it launched. It orders `/close-change
Applied` when the officer completes terminal work. It reserves
`/release-change` for a held nonterminal Change with continuation remaining and
requires the Handoff to name completed and next Activities, blockers, and
hazards. It records an operator instruction naming an officer session, or an
officer fact describing an operator interaction, as its own failure to keep
the operator out of the officer's pane. After either Change operation succeeds,
it stops the officer and relaunches the same agent kind in the same pane before
the next order.

Run exactly three officers across the operator's orchestrating sessions. Build
an artifact that targets one agent through an officer running that agent.

## Known environment and mail facts

- The adapter inbox can return zero records while the raw store inbox still
  holds them. The declared Change store's record for the adapter-inbox defect
  tracks its repair. Until that repair ships, follow the orchestrating session's
  explicitly supplied read-only store instruction for the affected project; do
  not derive or improvise that instruction here.
- Opening an already-created linked worktree through the environment capability
  can fail. Prepare and prove the linked worktree and pane before launch, then
  start the officer in that existing pane.
- A fresh session can accept its first prompt without starting work. Read the
  pane before submitting a second prompt; a stalled result alone does not prove
  the first prompt was absent.
- Stopping an officer closes both its pane and the session in that pane. A later
  order therefore requires a relaunch into a proven pane.
- An interim Prowl doorbell can be lost when its recipient is mid-turn. The
  surrounding delivery workflow reads the peer pane for the bell line and
  rings again only when the line is absent. This skill does not operate that
  transport.
- Every worktree pool has a distinct agent-mail project. Register an identity
  separately in every pool.
- The store can reject descriptive agent names. Use the accepted word-list name
  and preserve it verbatim in orders, records, and reports.
