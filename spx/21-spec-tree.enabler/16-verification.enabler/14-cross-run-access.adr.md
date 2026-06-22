# Cross-Run Access

The run-journal channel reads across the sealed runs of one branch-and-verification-type scope, returning each run's event prefix in run order, so a consumer computes a cross-run projection — the findings resolved and reopened across commits — over the run set through the one backend-neutral channel, without enumerating a storage path or holding a separate state index. Each backend realizes the access over its own run history: the local run-journal-file backend over the sealed run files under the scope, the pull-request backend over the prior run verdicts on the comment thread.

## Rationale

A stateful agentic verification run classifies a finding as resolved — present in a prior run, absent now — or reopened — resolved earlier, present again — by comparing the current run against the scope's prior runs. The per-run contract of `spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md` reaches one run by token and exposes no path to the prior runs of the same scope, so a consumer needing cross-run state would either enumerate a backend storage path — contradicting that decision's one-backend-neutral-channel rule — or keep a separate state index, the end-of-run state model the run-journal architecture removes. Reading the scope's sealed runs through the channel keeps the journal the run set's sole source of truth and the cross-run projection a pure function of those runs' event prefixes, the same discipline a single-run projection follows over one event prefix. Only sealed runs are in scope — an open run is one commit's verification still in progress — and run order lets the consumer fold the set into the current open, resolved, and reopened state deterministically. Backend selection stays an edge concern: each backend enumerates its own run history, and the consumer names none.

## Verification

### Audit

- ALWAYS: the run-journal channel reads across the sealed runs of one branch-and-verification-type scope, returning each run's event prefix in run order ([audit])
- ALWAYS: a cross-run projection is a pure function of the scope's sealed-run event prefixes — the consumer folds the run set to compute resolved and reopened, holding no state outside the journal ([audit])
- ALWAYS: cross-run access reaches the scope's runs through the one backend-neutral channel and hard-codes no storage path, backend, or surface — each backend enumerates its own run history ([audit])
- ALWAYS: cross-run access reads only sealed runs — an open run is excluded from the set until its terminal seal ([audit])
- NEVER: a consumer reads across runs by enumerating backend storage paths directly — a run-file glob, a state directory — or by maintaining a run index outside the journal ([audit])
