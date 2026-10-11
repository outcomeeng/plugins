<objective>

The trace table of one Framed or Executable candidate before its first audit, the sweep table of one Change-candidate repair batch: every same-class site and every changed-section dependent with its disposition, and the result of comparing the stabilized candidate with the retained findings.

</objective>

<same_class_site>

A same-class site is any location in the candidate, in the front matter or any `##` section, that carries the defect class a finding cites: a violation of the same rule or criterion, or the same wording or structure the repair rewrites. Find each by searching the whole candidate for the rewritten pattern and the rule's characteristic text, never by reading only the sections the finding names.

</same_class_site>

<changed_dependent>

A changed-section dependent is text in another section or in the front matter that cites, quotes, restates, or relies on text the repair changes and now disagrees with it. Check each edit against these dependents:

| Edit                                                                     | Dependents to check                                                                                      |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| Changed `## Nodes` row, Malleability before, or Malleability after       | Every `## Assertion operations` entry, `## Decisions` answer, and `## Mutations` row that names the Node |
| Changed assertion operation                                              | Every Decision that settles it and every `## Mutations` row that carries it out                          |
| Changed Decision                                                         | Every section whose content the Decision determines                                                      |
| Changed `## Mutations` row, count, or sequence                           | Every `## Mutations` row that depends on it and every sentence that states the number or order           |
| Changed `## Mutations` repository, observable check, or Node transitions | Every Node, `## Mutations` row, and blocker that lies outside the new slice                              |
| Changed `blocked_by` or `refined_from`                                   | Every section that names the blocker or predecessor                                                      |

</changed_dependent>

<sweep_table>

One row per site or dependent found:

| Site | Class or dependent | Disposition |
| ---- | ------------------ | ----------- |

The disposition is `repaired` with the section changed, or `unresolved` with the reason. An edit made to resolve a row is itself an edit, so its own same-class sites and dependents enter the table before the sweep ends.

</sweep_table>

<trace_check>

The trace table of one candidate, built in the conversation before the first `<audit_gate>` dispatch and kept out of the record, because `record-shape` makes an unknown level-two section a defect. One row per result the Intent's Evidence promises:

| Result | Assertion operation | Node | `## Mutations` row | Producer | Verification predicate | Later row that invalidates it |
| ------ | ------------------- | ---- | ------------------ | -------- | ---------------------- | ----------------------------- |

A Framed candidate fills the columns through Node; the later columns hold `not yet` there. An Executable candidate fills every column. A cell is a gap when it is empty, names no exact target, or bundles several Nodes into one entry. The last column holds the row whose edits change the subject of a predicate an earlier row records, or `none`; every other row of a predicate's Node that follows it is checked, and a predicate checked before such a row is a gap unless a final verification repeats it after the row.

A result passes the check by the route its subject takes:

- A result on an existing file passes when an Assertion operation names its owning Node and the exact target in the existing text.
- A Node the changeset touches only through a dependency needs no Assertion operation and passes with its own `## Mutations` row naming the results and producers that the merge composition selects for it.
- A result on a Node the Change creates passes with an Assertion operation naming the Node and the exact target it adds.

The check names each gap before the dispatch, and the candidate is repaired and re-swept under `<same_class_site>` and `<changed_dependent>` until the table holds none. A candidate without a gap passes unchanged.

</trace_check>

<retained_findings_comparison>

Before a re-audit, compare the stabilized candidate with the retained findings of the previous run, each by its unit key and rule identifier. The comparison holds when every retained `blocking` finding's location is repaired in the candidate and every retained `filed` finding is unchanged in severity and left unrepaired by the batch, and it names each retained finding that remains. A finding that the re-audit raises on text the previous run judged and did not report is delayed detection of unchanged text, not a result of the batch.

</retained_findings_comparison>
