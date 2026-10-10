<objective>

The sweep table of one Change-candidate repair batch: every same-class site and every changed-section dependent with its disposition, and the result of comparing the stabilized candidate with the retained findings.

</objective>

<same_class_site>

A same-class site is any location in the candidate, in the front matter or any `##` section, that carries the defect class a finding cites: a violation of the same rule or criterion, or the same wording or structure the repair rewrites. Find each by searching the whole candidate for the rewritten pattern and the rule's characteristic text, never by reading only the sections the finding names.

</same_class_site>

<changed_dependent>

A changed-section dependent is text in another section or in the front matter that cites, quotes, restates, or relies on text the repair changes and now disagrees with it. Check each edit against these dependents:

| Edit                                          | Dependents to check                                                                            |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Changed `## Nodes` row or target malleability | Every `## Assertion operations` entry, `## Decisions` answer, and Activity that names the Node |
| Changed assertion operation                   | Every Decision that settles it and every Activity that carries it out                          |
| Changed Decision                              | Every section whose content the Decision determines                                            |
| Changed Activity, count, or sequence          | Every Activity that depends on it and every sentence that states the number or order           |
| Changed `## Slice` boundary                   | Every Node, Activity, and blocker that lies outside the new boundary                           |
| Changed `blocked_by` or `refined_from`        | Every section that names the blocker or predecessor                                            |

</changed_dependent>

<sweep_table>

One row per site or dependent found:

| Site | Class or dependent | Disposition |
| ---- | ------------------ | ----------- |

The disposition is `repaired` with the section changed, or `unresolved` with the reason. An edit made to resolve a row is itself an edit, so its own same-class sites and dependents enter the table before the sweep ends.

</sweep_table>

<retained_findings_comparison>

Before a re-audit, compare the stabilized candidate with the retained findings of the previous run, each by its unit key and rule identifier. The comparison holds when every retained `blocking` finding's location is repaired in the candidate and every retained `filed` finding is unchanged in severity and left unrepaired by the batch, and it names each retained finding that remains. A finding that the re-audit raises on text the previous run judged and did not report is delayed detection of unchanged text, not a result of the batch.

</retained_findings_comparison>
