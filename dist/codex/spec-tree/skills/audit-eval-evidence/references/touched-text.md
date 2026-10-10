<objective>
The classification that sorts each eval-evidence finding into a finding on touched text, which rejects, or a standing finding, which is returned as `FILED` with its key and diff range.
</objective>

<contents>
- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_finding`

</contents>

<touched_text>

Touched text is a line of an inspected artifact that the diff between the base and the live file adds or changes, extended to its enclosing unit, plus the text the change invalidates. The base is the merge-base of `HEAD` and `origin/HEAD`:

```text
git merge-base HEAD origin/HEAD
git diff --unified=0 <base> -- <artifact-path>
```

The inspected artifacts are the spec's `[eval]` assertions, `eval.toml`, the prompt, the cases, `history.jsonl`, the prompt template, and the producer artifact or selected producer section. The enclosing unit is the assertion with its tag and link in the spec, the table or key in `eval.toml`, the case record in `cases.jsonl`, the history row in `history.jsonl`, and the section or declaration in the prompt, template, or producer. An artifact absent at the base is touched in full. A diff that cannot be resolved makes every inspected artifact touched, and the verdict names the failed command.

Invalidated text is:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it, such as an unchanged case whose assertion changed, or an unchanged history row whose recorded definition the change altered;
- a rule a changed line newly violates in another artifact, such as a changed producer section that an unchanged prompt no longer reflects;
- generated output whose source changed, such as a materialized prompt whose producer section or template changed.

A touched line that only reaches an already-defective artifact leaves the finding standing, against that artifact.

</touched_text>

<classification>

Classify each finding by its `file`, `line`, and `assertion`: a finding on touched text keeps severity `REJECT` and fails its row; a finding on any other text is standing and is returned with severity `FILED`. A finding's severity labels its defect and never decides the verdict: the verdict is not `FAIL` for a `FILED` finding, whatever `FILED` findings it reports. A missing required artifact is touched when the change adds or changes the assertion link that names it.

</classification>

<finding_key>

A finding is identified by its key, `<file>:<assertion>:<rule>`, where the second segment names the assertion by its text rather than a line number and the third is the finding's `rule`. The same finding carries the same key in every run and on every head.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key in the governing node's `ISSUES.md`, found in the node directory or its nearest ancestor holding one. Its severity rises, or a `FILED` finding starts to reject, only when the run names one changed basis in the finding's `message`: the text now lies in the diff, the change invalidates it, or the standard's catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.

</severity_and_disposition>

<filed_finding>

A `FILED` finding carries the six canonical fields plus `key` and `range`, the `<base>..<head>` diff range showing the finding lies outside the change, and sits in the row of the gate it concerns without failing that row.

</filed_finding>
