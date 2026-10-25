<objective>
The classification that sorts each PDR-audit finding into a finding on touched text, which rejects, or a standing finding, which is returned with severity `filed`, its key, `baseRefEvidence`, and `issuesEntry`.
</objective>

<contents>
- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_finding`

</contents>

<touched_text>

Touched text is a line of the PDR that the diff between the base and the live file adds or changes, extended to its enclosing unit, plus the text the change invalidates. The base is the merge-base of `HEAD` and `origin/HEAD`:

```text
git merge-base HEAD origin/HEAD
git diff --unified=0 <base> -- <pdr-file-path>
```

The enclosing unit is the sentence in prose, the whole property for a line under Product properties, the whole rule (its text, tag, and subsection placement) for a rule line under `## Verification`, and the opening decision statement for a line within it. A PDR absent at the base is touched in full. A diff that cannot be resolved makes the whole PDR touched, and the verdict names the failed command.

Invalidated text is:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it;
- a rule a changed line newly violates elsewhere in the PDR, such as a tag left under a subsection the edit moved its rule away from;
- generated output whose source changed.

A touched sentence that only cites an already-defective passage leaves the finding standing, against the passage. A finding that the PDR contradicts the product spec or an ancestor PDR lies on touched text when the changed PDR text is one side of the contradiction.

</touched_text>

<classification>

Classify each finding by its `locations`: a finding on touched text keeps severity `blocking` and fails its row; a finding on any other text is standing and is returned with severity `filed`. A finding's severity labels its defect and never decides the verdict: the run approves when no `blocking` finding exists, whatever `filed` findings it reports. The `missing-target` finding concerns the input rather than PDR text and keeps severity `blocking`.

</classification>

<finding_key>

A finding is identified by its key, `<pdr-file-path>:<rule-id>`, where `rule-id` is the catalogued identifier of the violated rule. The finding's `locations` name each section, property, or rule where the rule is violated by its text rather than a line number. The same finding carries the same key in every run and on every head.

A rule violated both on touched text and elsewhere yields two findings under one key: a `blocking` finding whose `locations` are the touched ones, and a `filed` finding whose `locations` are the rest.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key in the governing node's `ISSUES.md`, found in the PDR's directory or its nearest ancestor holding one. Its severity rises, or a `filed` finding starts to reject, only when the run names one changed basis in the finding's `evidence`: the text now lies in the diff, the change invalidates it, or the standard's catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.
</severity_and_disposition>

<filed_finding>

A `filed` finding carries the usual finding fields plus `key`, the `<path>:<rule-id>` the verdict keys every finding by, `baseRefEvidence`, the `<base>..<head>` diff range showing every location lies outside the change, and `issuesEntry`, an object whose `path` is the `ISSUES.md` of the nearest node that governs the audited artifact, found by the Product Tree foundation's governing-node search for product content, or the product root's `spx/ISSUES.md` when no node governs it, and whose `heading` is the heading of the entry that records the finding. The finding sits in the row of the property it concerns without failing that row.

</filed_finding>
