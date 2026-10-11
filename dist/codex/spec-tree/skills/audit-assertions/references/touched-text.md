<objective>
The classification that sorts each assertion-audit finding into a finding on touched text, which is recorded and rejects, or a standing finding, which is returned as `filed` with its key, `baseRefEvidence`, and `issuesEntry`.
</objective>

<contents>
- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_line`

</contents>

<touched_text>

Touched text is a line of the target spec or of a subject path an assertion names that the diff between the base and the audited tree adds or changes, extended to its enclosing unit, plus the text the change invalidates. The base is the merge-base of `HEAD` and `origin/HEAD`. The audited tree is the live working tree, which holds the retained input of the run for the target spec and the file the run read for each subject:

```text
git merge-base HEAD origin/HEAD
git diff --unified=0 <base> -- <path>
```

Run the second command once for the target spec and once for each subject path a finding's location lies in. The diff compares the base with the working tree, staged and unstaged changes included; a `<base>..HEAD` range is no endpoint, because it leaves those changes out.

The enclosing unit is the whole assertion (its text and tag) for a line of the spec, the sentence in prose, and the declaration, rule, or section in a subject. A path absent at the base is touched in full. A diff that cannot be resolved makes the target spec and every subject touched in full, and the verdict names the failed command.

Invalidated text is:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it, such as an unchanged assertion whose named subject changed;
- a rule a changed line newly violates in another file;
- generated output whose source changed.

A touched line that only reaches an already-defective passage leaves the finding standing, against that passage.

</touched_text>

<classification>

Classify each finding by its `location`: a finding on touched text is recorded on its unit and rejects; a finding on any other text is standing and is returned as `filed`, recorded nowhere in the run. A subject the assertion names that cannot be located lies in the assertion's own text, so its finding takes the classification of that assertion. A finding's severity labels its defect and never decides the verdict: the run approves when no finding on touched text exists, whatever standing findings it reports.

</classification>

<finding_key>

A finding is identified by its key, `<unitId>:<rule>`, whose `unitId` is the unit key `assertion:<designator>:<path>` (the designator is the rule slug, or `ordinal-<n>` when pathless) and whose rule is the finding's rule identifier. The key names the unit and rule and never a line number, so the same finding carries the same key in every run and on every head.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key in the governing node's `ISSUES.md`, found in the node directory or its nearest ancestor holding one, across runs. Its severity is `blocking` for a merge-safety defect and `debt` for a real defect that does not jeopardize merge safety, and never depends on scope. Its severity rises, or a `filed` finding starts to reject, only when the run names one changed basis in the finding's `evidence`: the text now lies in the diff, the change invalidates it, or the standard's catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.

</severity_and_disposition>

<filed_line>

After the projection, return each `filed` finding on its own line, or `filed: none`:

```text
filed: <finding-key> | rule: <rule> | severity: <blocking|debt> | run: <run-token> | baseRefEvidence: <base-commit>; <diff-command>... | issuesEntry: <path>#<heading>
```

`baseRefEvidence` names the base as a full commit identity and each `git diff --unified=0 <base> -- <path>` command for the paths the finding's locations lie in, and states that the diff leaves every location untouched in the audited tree. `issuesEntry` gives the `ISSUES.md` of the nearest node that governs the audited artifact, found by the Spec Tree foundation's governing-node search for product content, or the product root's `spx/ISSUES.md` when no node governs it, and the heading of the entry that records the finding.

</filed_line>
