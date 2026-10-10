<objective>
The classification that sorts each returned finding into a finding on touched text, which is recorded and rejects, or a standing finding, which is returned as `filed`.
</objective>

<contents>
- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_line`

</contents>

<touched_text>

Touched text is a line the resolved `base..head` scope adds or changes — found by comparing each subject's head-side body with its base-side body, read as `<request_contract>` states, and for an advisory target also the live modifications — extended to its enclosing sentence, assertion, rule, or declaration, plus the text the change invalidates:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it;
- a rule a changed line newly violates in another file;
- generated output whose source changed.

</touched_text>

<classification>

Classify each finding a concern returns by its `location`: a finding on touched text is recorded and rejects; a finding on any other text is standing and is returned as `filed`. A finding's severity labels its defect and never decides the verdict: the run approves when no finding on touched text exists, whatever standing findings it reports.

</classification>

<finding_key>

A finding is identified by its finding key, `<stable-scope-key>:<rule>`, whose rule segment is the concern's rule identifier. The key names the unit and rule and never a line number, so the same finding carries the same key in every run and on every head, and two runs produced the same finding exactly when their keys are equal.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key — in the governing node's `ISSUES.md` or the evidence the run loaded — across runs. Its severity rises, or a `filed` finding starts to reject, only when the run names one changed basis in that finding's `evidence`: the text now lies in the diff, the change invalidates it, or the standard's catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.

</severity_and_disposition>

<filed_line>

After the projection, return each `filed` finding on its own line, or `filed: none`:

```text
filed: <finding-key> | rule: <rule> | severity: <blocking|debt> | run: <run-token> | range: <base>..<head>
```

The line carries the key, the rule identifier, the run token, and the diff range that shows the finding lies outside the change.

</filed_line>
