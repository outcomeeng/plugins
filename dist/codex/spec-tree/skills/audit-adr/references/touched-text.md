<objective>
The classification that sorts each ADR-audit finding into a finding on touched text, which rejects, or a standing finding, which is returned with severity `filed`, its key, and its diff range.
</objective>

<contents>
- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_finding`

</contents>

<touched_text>

Touched text is a line of the ADR that the diff between the base and the live file adds or changes, extended to its enclosing unit, plus the text the change invalidates. The base is the merge-base of `HEAD` and `origin/HEAD`:

```text
git merge-base HEAD origin/HEAD
git diff --unified=0 <base> -- <adr-file-path>
```

The enclosing unit is the sentence in prose, the whole rule (its text, tag, and subsection placement) for a rule line under `## Verification`, and the opening decision statement for a line within it. An ADR absent at the base is touched in full. A diff that cannot be resolved makes the whole ADR touched, and the verdict names the failed command.

Invalidated text is:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it;
- a rule a changed line newly violates elsewhere in the ADR, such as a tag left under a subsection the edit moved its rule away from;
- generated output whose source changed.

A touched sentence that only cites an already-defective passage leaves the finding standing, against the passage.

</touched_text>

<classification>

Classify each finding, native or composed, by its `location`: a finding on touched text keeps severity `blocking` and fails its row; a finding on any other text is standing and is returned with severity `filed`. A finding's severity labels its defect and never decides the verdict: the run approves when no `blocking` finding exists, whatever `filed` findings it reports. A composed language row takes the same classification, so a composed `FAIL` rejects the ADR only through a `blocking` finding.

</classification>

<finding_key>

A finding is identified by its key, `<adr-file-path>:<location>:<rule>`, where `location` names the section or rule by its text rather than a line number and `rule` is one finding identifier of the verdict format. The same finding carries the same key in every run and on every head.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key in the governing node's `ISSUES.md`, found in the ADR's directory or its nearest ancestor holding one. Its severity rises, or a `filed` finding starts to reject, only when the run names one changed basis in the finding's `observed` field: the text now lies in the diff, the change invalidates it, or the standard's catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.

</severity_and_disposition>

<filed_finding>

A `filed` finding carries the usual finding fields plus `key` and `range`, the `<base>..<head>` diff range showing the finding lies outside the change, and sits in the row of the property it concerns without failing that row.

</filed_finding>
