<objective>

The sweep table of one Change Draft repair batch: every same-class site and every changed-part dependent with its disposition, resolved before the repaired Draft takes the form check again.

</objective>

<same_class_site>

A same-class site is any location in the Draft, in the front matter or any section, that carries the defect class a finding cites: a breach of the rule the finding names by its slug, as `product-tree:change-standards` states that rule, or the same wording or structure the repair rewrites. The finding's examples are instances of the class, never its definition, and the repair changes nothing the rule does not require. Find each by searching the whole Draft for the rewritten pattern and the rule's characteristic text, never by reading only the subsection the finding names.

</same_class_site>

<changed_dependent>

A changed-part dependent is text elsewhere in the Draft that cites, restates, or relies on text the repair changes and now disagrees with it. Check each edit against these dependents:

| Edit                                                  | Dependents to check                                                                                    |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| A changed Statement of Intent part                    | The title, and every Declarations line that carries a result the Verification part names               |
| A changed decision line                               | Every Assertion line that cites the decision, and every subsection the decision's scope governs        |
| A changed heading path, or a new artifact's `NN` path | Every later subsection, `Depends on:`, `Precedes:`, and `Infrastructure:` line that names the path     |
| A changed malleability                                | The subsection's infrastructure lines under `infrastructure-line` and `spec-node-none`                 |
| A changed operation header                            | The payload kind under `payloads`, and every file `path-naming` names for a deleted or moved path      |
| A changed `base`                                      | Every `-` line and context line, which read at the Base, and `operator-bound-base` for a Sliced record |

</changed_dependent>

<sweep_table>

Record one row per site and per dependent:

| Location | Rule slug | Disposition (`repaired`, `unaffected`, or `not-applicable`) | Check that shows it |
| -------- | --------- | ----------------------------------------------------------- | ------------------- |

Leave no row without a disposition. A `repaired` row names the check that shows the class closed, such as the form check's next result.

</sweep_table>
