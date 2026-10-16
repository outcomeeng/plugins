<objective>

The classification that sorts each test-evidence finding into a finding on touched text, which is recorded on its unit and rejects, or a standing finding, which is returned as a `filed` line with its key, `baseRefEvidence`, and `issuesEntry`.

</objective>

<contents>

- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_line`

</contents>

<touched_text>

Touched text is a line of an inventoried artifact that the diff between the base and the audited tree adds or changes, extended to its enclosing unit, plus the text the change invalidates. For a node target the base is the merge-base of `HEAD` and `origin/HEAD` and the audited tree is the live working tree; for an evidence-scope target the base and the audited tree are the `base` and `head` the resolved scope reports:

```text
git merge-base HEAD origin/HEAD
git diff --unified=0 <base> -- <artifact-path>
git diff --unified=0 <base> <head> -- <artifact-path>
```

The first diff compares the base with the working tree, staged and unstaged changes included; the second serves an evidence-scope target.

The inventoried artifacts are the spec's assertions, each linked test, and every harness, generator, fixture, discovery artifact, and governed production source of the evidence chain. The enclosing unit is the assertion with its tag and link in the spec, the test function or callback in a test, and the declaration in infrastructure or production source. An artifact absent at the base is touched in full. A diff that cannot be resolved makes every inventoried artifact touched, and the finding names the failed command.

Invalidated text is:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it, such as an unchanged test whose assertion changed, or an unchanged assertion whose governed source changed;
- a rule a changed line newly violates in another artifact, such as a changed harness that now owns a predicate an unchanged test relies on;
- generated output whose source changed.

A touched line that only reaches an already-defective artifact leaves the finding standing, against that artifact.

</touched_text>

<classification>

Classify each finding by its `location`: a finding on touched text is recorded on its unit with the severity its catalog row declares, and a `blocking` finding rejects the run; a finding on any other text is standing and is returned as a `filed` line, recorded nowhere in the run. A finding returned by a composed language audit takes the same classification. A finding's severity labels its defect and never decides the terminal status: the run approves when no finding on touched text exists, whatever standing findings it reports.

</classification>

<finding_key>

A finding is identified by its key, `<unitId>:<rule>`, where `unitId` is the unit the finding sits on and `rule` is one identifier of the rule catalog. The key is the finding's idempotency key. The finding's `location` names the artifact path and the assertion or declaration by its text rather than a line number; one unit and rule yield one finding, which names every location it covers. The same finding carries the same key in every run and on every head.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key in the governing node's `ISSUES.md`, found in the node directory or its nearest ancestor holding one. Its severity rises, or a `filed` finding starts to reject, only when the run names one changed basis in the finding's `evidence`: the text now lies in the diff, the change invalidates it, or the standard's catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.

</severity_and_disposition>

<filed_line>

After the projection, return each `filed` finding on its own line, or `filed: none`:

```text
filed: <finding-key> | rule: <rule> | severity: <blocking|debt> | run: <run-token> | baseRefEvidence: <base-commit>; <diff-command> | issuesEntry: <path>#<heading>
```

`baseRefEvidence` names the base as a full commit identity and the `git diff --unified=0` command of the artifact the finding names, and states that the diff leaves every location of the finding untouched in the audited tree. `issuesEntry` gives the `ISSUES.md` of the nearest node that governs the audited artifact, found by the Spec Tree foundation's governing-node search for product content, or the product root's `spx/ISSUES.md` when no node governs it, and the heading of the entry that records the finding.

</filed_line>
