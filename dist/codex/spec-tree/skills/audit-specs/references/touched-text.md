<objective>
The classification that sorts each spec-audit finding into a finding on touched text, which rejects, or a standing finding, which is returned as `FILED` with its key and diff range.
</objective>

<contents>
- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_finding`

</contents>

<touched_text>

Touched text is a line of the node spec that the diff between the base and the live file adds or changes, extended to its enclosing unit, plus the text the change invalidates. The base is the merge-base of `HEAD` and `origin/HEAD`:

```text
git merge-base HEAD origin/HEAD
git diff --unified=0 <base> -- <node-spec-file-path>
```

The enclosing unit is the sentence in prose, the whole assertion (its text, tag, and heading placement) for an assertion line, and the opening clause set for a kind statement. A spec absent at the base is touched in full. A diff that cannot be resolved makes the whole spec touched, and the verdict names the failed command.

Invalidated text is:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it;
- a rule a changed line newly violates elsewhere in the spec, such as a tag placed under a heading the edit moved it away from;
- generated output whose source changed.

A touched sentence that only cites an already-defective passage leaves the finding standing, against the passage.

</touched_text>

<classification>

Classify each finding by its `location`: a finding on touched text keeps severity `REJECT` and fails its row; a finding on any other text is standing and is returned with severity `FILED`. A finding's severity labels its defect and never decides the verdict: the run approves when no `REJECT` finding exists, whatever `FILED` findings it reports.

</classification>

<finding_key>

A finding is identified by its key, `<node-spec-file-path>:<location>:<rule>`, where `location` names the section or assertion by its text rather than a line number and `rule` is one violation pattern of the verdict format. The same finding carries the same key in every run and on every head.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key in the governing node's `ISSUES.md`, found in the node directory or its nearest ancestor holding one. Its severity rises, or a `FILED` finding starts to reject, only when the run names one changed basis in the finding's `evidence`: the text now lies in the diff, the change invalidates it, or the standard's catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.

</severity_and_disposition>

<filed_finding>

A `FILED` finding carries the usual finding fields plus `key` and `range`, the `<base>..<head>` diff range showing the finding lies outside the change, and sits in the row of the property it concerns without failing that row.

</filed_finding>
