<objective>
The classification that sorts each test-audit finding into a finding on touched text, which rejects, or a standing finding, which is returned as `FILED` with its key, `baseRefEvidence`, and `issuesEntry`.
</objective>

<contents>
- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_finding`

</contents>

<touched_text>

Touched text is a line of an inventoried artifact that the diff between the base and the live file adds or changes, extended to its enclosing unit, plus the text the change invalidates. The base is the merge-base of `HEAD` and `origin/HEAD`:

```text
git merge-base HEAD origin/HEAD
git diff --unified=0 <base> -- <artifact-path>
```

The inventoried artifacts are the spec's assertions, each linked test, and every harness, generator, fixture, discovery artifact, and governed production source of the evidence chain. The enclosing unit is the assertion with its tag and link in the spec, the test function or callback in a test, and the declaration in infrastructure or production source. An artifact absent at the base is touched in full. A diff that cannot be resolved makes every inventoried artifact touched, and the verdict names the failed command.

Invalidated text is:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it, such as an unchanged test whose assertion changed, or an unchanged assertion whose governed source changed;
- a rule a changed line newly violates in another artifact, such as a changed harness that now owns a predicate an unchanged test relies on;
- generated output whose source changed.

A touched line that only reaches an already-defective artifact leaves the finding standing, against that artifact.

</touched_text>

<classification>

Classify each finding by its `locations`: a finding on touched text keeps severity `REJECT` and fails its row; a finding on any other text is standing and is returned with severity `FILED`. A finding returned by a composed language audit takes the same classification. A finding's severity labels its defect and never decides the verdict: the run approves when no `REJECT` finding exists, whatever `FILED` findings it reports.

</classification>

<finding_key>

A finding is identified by its key, `<file>:<rule-id>`, where `file` is the repository-relative path of the artifact that holds the defect and `rule-id` is the catalogued identifier of the violated rule, from the test audit's own catalog or from a composed language skill's catalog. The finding's `locations` name each assertion and declaration where the rule is violated by its text rather than a line number. The same finding carries the same key in every run and on every head.

A rule violated both on touched text and elsewhere in one file yields two findings under one key: a `REJECT` finding whose `locations` are the touched ones, and a `FILED` finding whose `locations` are the rest.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key in the governing node's `ISSUES.md`, found in the node directory or its nearest ancestor holding one. Its severity rises, or a `FILED` finding starts to reject, only when the run names one changed basis in the finding's `message`: the text now lies in the diff, the change invalidates it, or the standard's catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.

</severity_and_disposition>

<filed_finding>

A `FILED` finding carries the usual finding fields plus `key`, `baseRefEvidence`, the `<base>..<head>` diff range showing every location lies outside the change, and `issuesEntry`, an object whose `path` is the `ISSUES.md` of the nearest node that governs the audited artifact, found by the Product Tree foundation's governing-node search for product content, or the product root's `spx/ISSUES.md` when no node governs it, and whose `heading` is the heading of the entry that records the finding. The finding sits in the row of the gate it concerns without failing that row.

</filed_finding>
