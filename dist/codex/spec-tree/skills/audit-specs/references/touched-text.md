<objective>

The classification that sorts each spec-audit finding into a finding on touched text, which is recorded on its unit and rejects, or a standing finding, which is returned as a `filed` line with its key, `baseRefEvidence`, and `issuesEntry`.

</objective>

<contents>

- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_line`

</contents>

<touched_text>

Touched text is a line of the node spec that the diff between the base and the audited tree adds or changes, extended to its enclosing unit, plus the text the change invalidates. The base is the merge-base of `HEAD` and `origin/HEAD`. The audited tree is the live working tree, which holds the retained input of the run:

```text
git merge-base HEAD origin/HEAD
git diff --unified=0 <base> -- <node-spec-file-path>
```

The diff compares the base with the working tree, staged and unstaged changes included; a `<base>..HEAD` range is no endpoint, because it leaves those changes out.

The enclosing unit is the sentence in prose, the whole assertion (its text, tag, and heading placement) for an assertion line, and the opening clause set for a kind statement. A spec absent at the base is touched in full. A diff that cannot be resolved makes the whole spec touched, and the finding names the failed command.

Invalidated text is:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it;
- a rule a changed line newly violates elsewhere in the spec, such as a tag placed under a heading the edit moved it away from;
- generated output whose source changed.

A touched sentence that only cites an already-defective passage leaves the finding standing, against the passage.

</touched_text>

<classification>

Classify each finding by its `location`: a finding on touched text is recorded on its unit with the severity its catalog row declares, and a `blocking` finding rejects the run; a finding on any other text is standing and is returned as a `filed` line, recorded nowhere in the run. A finding's severity labels its defect and never decides the terminal status: the run approves when no finding on touched text exists, whatever standing findings it reports. A finding about the target itself rather than its text, `unsupported-target`, is recorded on the root.

</classification>

<finding_key>

A finding is identified by its key, `<unitId>:<rule>`, where `unitId` is the unit the finding sits on (`spec:root:<node-spec-file-path>` or `spec:property:<property>:<node-spec-file-path>`) and `rule` is one finding identifier. The key is the finding's idempotency key. The finding's `location` field names the section or assertion by its text rather than a line number; one unit and rule yield one finding, which names every location it covers. The same finding carries the same key in every run and on every head.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key in the governing node's `ISSUES.md`, found in the node directory or its nearest ancestor holding one. Its severity rises, or a `filed` finding starts to reject, only when the run names one changed basis in the finding's `evidence`: the text now lies in the diff, the change invalidates it, or the standard's catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.

</severity_and_disposition>

<filed_line>

After the projection, return each `filed` finding on its own line, or `filed: none`:

```text
filed: <finding-key> | rule: <rule> | severity: <blocking|debt> | run: <run-token> | baseRefEvidence: <base-commit>; <diff-command> | issuesEntry: <path>#<heading>
```

`baseRefEvidence` names the base as a full commit identity and the `git diff --unified=0 <base> -- <node-spec-file-path>` command, and states that the diff leaves every location of the finding untouched in the audited tree. `issuesEntry` gives the `ISSUES.md` of the nearest node that governs the audited artifact, found by the Spec Tree foundation's governing-node search for product content, or the product root's `spx/ISSUES.md` when no node governs it, and the heading of the entry that records the finding.

</filed_line>
