<objective>
The classification that sorts each test-audit finding into a finding on touched text, which is recorded and rejects, or a standing finding, which is returned as `filed` with its key, `baseRefEvidence`, and `issuesEntry`.
</objective>

<contents>
- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_line`

</contents>

<touched_text>

Touched text is a line of an inventoried artifact that the diff between the base and the audited tree adds or changes, extended to its enclosing unit, plus the text the change invalidates. The base is the merge-base of `HEAD` and `origin/HEAD`. The audited tree is the live working tree:

```text
git merge-base HEAD origin/HEAD
git diff --unified=0 <base> -- <artifact-path>
```

The diff compares the base with the working tree, staged and unstaged changes included; a `<base>..HEAD` range is no endpoint, because it leaves those changes out.

For a `changeset` target the base is the merge-base of the resolved `base` and `head`, which equals the merge-base above for the selectors `HEAD` and a branch; the head equals the checkout's `HEAD`, so the same diff command applies.

The inventoried artifacts are the spec's assertions, each linked test, and every harness, generator, fixture, discovery artifact, and governed production source of the evidence chain. The enclosing unit is the assertion with its tag and link in the spec, the test function or callback in a test, and the declaration in infrastructure or production source. An artifact absent at the base is touched in full. A diff that cannot be resolved makes every inventoried artifact touched, and the run names the failed command.

Invalidated text is:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it, such as an unchanged test whose assertion changed, or an unchanged assertion whose governed source changed;
- a rule a changed line newly violates in another artifact, such as a changed harness that now owns a predicate an unchanged test relies on;
- generated output whose source changed.

A touched line that only reaches an already-defective artifact leaves the finding standing, against that artifact. A finding that names a blocked inspection lies on touched text, because the defect is the audit's inability to judge the evidence, not a passage of it.

</touched_text>

<classification>

Classify each finding by its `location`: a finding on touched text is recorded on its unit and rejects; a finding on any other text is standing and is returned as `filed`, recorded nowhere in the run. A finding returned by a composed language audit takes the same classification. A finding's severity labels its defect and never decides the verdict: the run approves when no finding on touched text exists and no unit is `incomplete`, whatever standing findings it reports.

</classification>

<finding_key>

A finding is identified by its key, `<unitId>:<rule-id>`, where `unitId` is the grandchild unit key of the linked test file it concerns and `rule-id` is the catalogued identifier of the violated rule, from the test audit's own catalog or from a composed language skill's catalog. The key names the unit and rule and never a line number, so the same finding carries the same key in every run and on every head. The finding's `location` names each assertion and declaration where the rule is violated by its text.

A rule violated both on touched text and elsewhere on one unit yields two findings under one key: the one on touched text is recorded on its unit, and the other is returned as `filed`.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key in the governing node's `ISSUES.md`, found in the node directory or its nearest ancestor holding one, across runs. Its severity is `blocking` for a merge-safety defect and `debt` for a real defect that does not jeopardize merge safety. Its severity rises, or a `filed` finding starts to reject, only when the run names one changed basis in the finding's `evidence`: the text now lies in the diff, the change invalidates it, or the standard's catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.

</severity_and_disposition>

<filed_line>

After the projection, return each `filed` finding on its own line, or `filed: none`:

```text
filed: <finding-key> | rule: <rule> | severity: <blocking|debt> | run: <run-token> | baseRefEvidence: <base-commit>; <diff-command> | issuesEntry: <path>#<heading>
```

`baseRefEvidence` names the base as a full commit identity and the `git diff --unified=0 <base> -- <artifact-path>` command for each artifact the finding locates, and states that the diff leaves every location untouched in the audited tree. `issuesEntry` gives the `ISSUES.md` of the nearest node that governs the audited artifact, found by the Product Tree foundation's governing-node search for product content, or the product root's `spx/ISSUES.md` when no node governs it, and the heading of the entry that records the finding.

</filed_line>
