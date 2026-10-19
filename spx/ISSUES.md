# Issues: Product

## Opening decision statement of the merging PDR runs seven sentences

Rule `declaration-form`, severity WARNING, unit [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md), unit label "opening decision statement". Standing finding under properties 11 and 13 of [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), found by the `spec-tree:pdr-auditor` run 1 of 2 on head `c5c7a2e7a1d800106ebcffb7e8dc8dc486a80db5`.

**Evidence**: the opening decision statement of [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) runs seven sentences where the PDR template asks for one to three. The text lies outside the changeset: [`git diff 810ea183243253d88d5c00c315c6a4684ef0f78f...c5c7a2e7a1d800106ebcffb7e8dc8dc486a80db5 -- spx/15-merging.pdr.md`](spx/15-merging.pdr.md) changes only lines 32 and 42 to 44, and the opening statement sits on line 3.

**Impact**: a reader meets a long opening before the decision's first property.

**Settlement condition**: the statement is cut to one to three sentences.

## A blocking deferral entry carries no binding to its finding `spx/15-merging.pdr.md` `merge-readiness` `spx/15-merging.pdr.md`

Category consistency, severity debt, finding F-001 of local review run 2026-10-19_02-54-13-208-c01dea92c8ca on head `f804826386378a8c482223e1a52ad608e74f158a`, at line 34 of [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md). The sentence is the merge-readiness decision the governing Change states in exact text, so the changeset writes no repair to it and the finding is returned `filed`.

**Evidence**: line 34 resolves a `blocking` finding by "its recorded deferral (an entry in the owning node's `ISSUES.md` whose reason names why its fix is a separate larger concern)". A `debt` finding binds to its `ISSUES.md` entry by its entry key, stated on lines 49 and 50. No sentence binds a blocking deferral entry to its finding. Any unrelated `ISSUES.md` entry in the owning node that carries a large-concern reason satisfies the predicate for a blocking merge-safety finding. The same "its recorded deferral" description recurs in the shipped merge-policy, action-tokens, manage-pr, merge, and open-pr skill text and in the managing-pr scenario, so each inherits the gap.

**Impact**: a blocking finding's deferral is not checkable against the finding it defers, so an unrelated entry can release the merge-readiness predicate.

**Settlement condition**: a blocking deferral entry is matched to its finding by the same entry key a debt ruling uses.
