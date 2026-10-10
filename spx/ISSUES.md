# Issues: Product

## Opening decision statement of the merging PDR runs seven sentences

Rule `declaration-form`, severity WARNING, unit [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md), unit label "opening decision statement". Standing finding under properties 11 and 13 of [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), found by the `spec-tree:pdr-auditor` run 1 of 2 on head `c5c7a2e7a1d800106ebcffb7e8dc8dc486a80db5`.

**Evidence**: the opening decision statement of [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) runs seven sentences where the PDR template asks for one to three. The text lies outside the changeset: [`git diff 810ea183243253d88d5c00c315c6a4684ef0f78f...c5c7a2e7a1d800106ebcffb7e8dc8dc486a80db5 -- spx/15-merging.pdr.md`](spx/15-merging.pdr.md) changes only lines 32 and 42 to 44, and the opening statement sits on line 3.

**Impact**: a reader meets a long opening before the decision's first property.

**Settlement condition**: the statement is cut to one to three sentences.
