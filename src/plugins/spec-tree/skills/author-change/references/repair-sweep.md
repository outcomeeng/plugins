<objective>

The sweep table of one Change-candidate repair batch: every same-class site and every changed-section dependent with its disposition, and the result of comparing the stabilized candidate with the retained findings.

</objective>

<same_class_site>

A same-class site is any location in the candidate, in the front matter or any `##` section, that carries the defect class a finding cites: a violation of the clause the finding's rule or criterion defines in its standard, or the same wording or structure the repair rewrites. The finding's examples are instances of the class, never its definition, and the repair changes nothing the clause does not require. Find each by searching the whole candidate for the rewritten pattern and the rule's characteristic text, never by reading only the sections the finding names.

</same_class_site>

<changed_dependent>

A changed-section dependent is text in another section or in the front matter that cites, quotes, restates, or relies on text the repair changes and now disagrees with it. Check each edit against these dependents:

| Edit                                                                     | Dependents to check                                                                                      |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| Changed `## Governance` entry or verdict                                 | The Governance mutations block of the record, and every Spec mutations assertion that cites its decision |
| Changed Governance mutations decision                                    | Every Spec mutations assertion and every `## Governance` verdict the decision determines                 |
| Changed Spec mutations block, malleability before, or malleability after | Every other block that names the Node                                                                    |
| Changed Spec mutations assertion                                         | Every Governance mutations decision that governs it and every `## Slice` check that observes it          |
| Changed block order or count                                             | Every block that depends on it and every sentence that states the number or order                        |
| Changed `## Slice` repository or check                                   | Every block, Node, and blocker that lies outside the new slice                                           |
| Changed `blocked_by` or `predecessors`                                   | Every section that names the blocker or predecessor                                                      |

</changed_dependent>

<sweep_table>

One row per site or dependent found:

| Site | Class or dependent | Disposition |
| ---- | ------------------ | ----------- |

The disposition is `repaired` with the section changed and, for each repair of a finding, the clause applied and the check that shows the class closed, or `unresolved` with the reason. The re-audit's verdict, never the recorded check, decides whether the class closed. An edit made to resolve a row is itself an edit, so its own same-class sites and dependents enter the table before the sweep ends.

</sweep_table>

<retained_findings_comparison>

Before a re-audit, compare the stabilized candidate with the retained findings of the previous run, each by its unit key and rule identifier. The comparison holds when every retained `blocking` finding's location is repaired in the candidate and every retained `filed` finding is unchanged in severity and left unrepaired by the batch, and it names each retained finding that remains. A finding that the re-audit raises on text the previous run judged and did not report is delayed detection of unchanged text, not a result of the batch.

</retained_findings_comparison>
