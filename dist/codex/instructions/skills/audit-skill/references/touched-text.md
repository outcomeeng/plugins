<objective>
The classification that sorts each skill-audit finding into a finding on touched text, which keeps its catalog severity and rejects the run, or a standing finding, which is recorded with severity `filed`, its key, and its diff range and rejects nothing.
</objective>

<contents>
- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_finding`

</contents>

<touched_text>

Touched text, inside one changed bundle file or included fragment, is each line that `git diff --unified=0 '<base-oid>...<head-oid>' -- '<path>'` adds or changes, extended to its enclosing unit, plus the text the change invalidates. The enclosing unit is:

| Content                   | Unit                                                                           |
| ------------------------- | ------------------------------------------------------------------------------ |
| Prose                     | The sentence                                                                   |
| A list or table           | The list item or the table row                                                 |
| Frontmatter               | The field                                                                      |
| A tagged section          | The tag's opening and closing lines when either changed, otherwise the content |
| A script or template body | The enclosing declaration or block                                             |

A file with status `A` is touched in full. A deleted file has no text; the references, siblings, and routes its deletion leaves behind are invalidated text.

Invalidated text is:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it;
- a rule a changed line newly violates in another file of the bundle, such as a route target the edit removed or a reference the edit orphaned;
- generated output whose source changed.

A touched sentence that only cites an already-defective passage leaves the finding standing, against the passage.

</touched_text>

<classification>

Classify each finding by its locations. A finding with any location on touched text keeps the severity its catalog row declares, `blocking` or `debt`, and rejects the run. A finding whose locations all lie outside touched text is standing and takes severity `filed`. A finding's severity labels its defect and never decides the verdict: the run is `approved` when no `blocking` or `debt` finding exists, whatever `filed` findings it records.

Counter-driven rules, such as `eager_payload_ceiling` and a `SKILL.md` line limit, are judged on the whole file. Such a finding is on touched text when the change made the file cross the limit or raised its count while already over, and is standing otherwise.

</classification>

<finding_key>

A finding is identified by its idempotency key, `<unit>:<rule-id>`, the same in every run and on every head. The key never changes with a line number, a location, or the severity.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key in the `ISSUES.md` of the node governing the bundle, when the repository carries one. Its severity rises, or a `filed` finding starts to reject, only when the run names one changed basis in the finding's `evidence.observed`: the text now lies in the diff, the change invalidates it, or a standards catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.

</severity_and_disposition>

<filed_finding>

A `filed` finding uses the finding payload of `<persistence_contract>` with `severity` set to `filed`, and its `evidence.observed` opens with the diff range `<base-oid>..<head-oid>` showing that every location lies outside the change. Its unit is the changed file it lies in; text in a bundle file the changeset leaves unchanged is read as context and carries no finding.

</filed_finding>
