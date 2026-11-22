---
id: 01a0b1fc-579f-7092-98af-601f9780d693
malleability: spec
---

# Changes

PROVIDES the Change skills change-standards, author-change, audit-change, manage-change, and report-changes
SO THAT product engineers and the agents that refine and apply Changes
CAN move a prioritized Output from proposal to applicable work without placing mutable work state in product truth

## Assertions

### Probe: merged record fix

- [merged-record-fix](probes/merged-record-fix/probe.md): a Leaf whose Changeset merged into the default branch, and whose record a later publish fixes, keeps the Operator's review of each part the fix leaves unchanged and closes Applied

### Audit: Change skills

- skill-set: The author-change skill records, publishes, splits, merges, and reframes a Change; the manage-change skill makes every other Transition on one Change; the audit-change skill audits a record; the report-changes skill lists the open Changes; and the change-standards skill states the record they share.
- record-form-only: The Change skills write and read only the record the Change record decision states, and read another form only to carry its proposal into a new record.
- provider-rules: The Change skills carry every rule they apply, cite no methodology chapter path, and name no methodology version.

### Test.Mapping: [read-relations-parent](tests/test_audit_change_relations_parent.mapping.l1.py)

`read-relations` maps each form of a `Parent` number field value to the issue number it names, and an absent value to `null`.

| Case    | Parent field value | Parent |
| ------- | ------------------ | ------ |
| integer | 7                  | 7      |
| float   | 7.0                | 7      |
| absent  | absent             | `null` |

### Test.Compliance: audit-change runner

- [read-relations-absorbers](tests/test_audit_change_relations.compliance.l1.py): ALWAYS: `read-relations` returns as `absorbers` the issue that the named issue's duplicate link names, or none when the named issue is not closed as a duplicate, and never the issues the named issue's own `Predecessors` value names
- [read-relations-pages](tests/test_audit_change_relations.compliance.l1.py): ALWAYS: `read-relations` reads the named issue's Children through the store's filter on the `Parent` field, never a read of every issue of the store, in pages of 100 Children up to 10 pages, and returns a blocked result naming `100 Children per page, 10 pages` when the tenth page still reports a further page
- [read-relations-fields](tests/test_audit_change_relations.compliance.l1.py): ALWAYS: `read-relations` returns a blocked result naming `50 issue field values per issue` when an issue's field-value connection reports a further page, and returns no Product or Parent read from that partial connection
- [runner-no-file](tests/test_audit_change_run.compliance.l1.py): NEVER: the bundled runner of `audit-change` writes a file other than the Change Draft that `retain-record` writes to the file `spx draft create --kind change` creates; each invocation reads one JSON request on stdin and writes one JSON result on stdout, and the SPX run journal and that Change Draft are the only state that persists between requests
- [runner-checkout-root](tests/test_audit_change_run.compliance.l1.py): ALWAYS: the `audit-change` request names the Product's checkout root, which its caller resolves from `spx/local/changes.md`, and the runner reads every path a record names, the Decision Records and Nodes its Declarations name, under that root, runs its git and spx commands with that root as the working directory, returns a blocked result naming the root when the request carries none or the root is no repository checkout, and keeps its containment check of those paths against that root, so a change audit whose record paths lie in another worktree than the session's seals its run
- [retain-record](tests/test_audit_change_record.compliance.l1.py): ALWAYS: the runner's `retain-record` operation composes the Change Draft of the named issue from each part's home in the store, creates the Draft's one file through one `spx draft create --kind change` command with the Product's checkout root as the working directory, writes the composed Draft to the absolute path that command returns, passing no Draft text on standard input, and returns the retained Draft's identifier, its absolute path, and its digest; a retained Draft that differs from the composed one blocks with `retained-input-mismatch`, and a failed or unrunnable store or `spx` command blocks with `command-failed`
- [draft-scope](tests/test_audit_change_run.compliance.l1.py): ALWAYS: the runner reads its candidate at the absolute path `spx draft create` returned, and starts, appends to, reconciles, and finishes its run with the scope type `file` and the scope the canonical `<owner>/<repo>#<N>` reference of the audited Change, the scope `manage-change` reads the audit from
- [read-authority](tests/test_audit_change_authority.compliance.l1.py): ALWAYS: the runner's `read-authority` operation reads a Change's field-change events at 100 per page and at most 10 pages, reads no comment, and returns a blocked result naming the bound when the read fills it
- [read-published](tests/test_audit_change_published.compliance.l1.py): ALWAYS: the runner's `read-published` operation takes an operation name and a canonical `<owner>/<repo>#<N>` issue identity, reads that issue's body through one `gh` query, writes nothing, and returns the body or the empty string; a malformed request is `invalid-request`, a failed or unrunnable `gh` call is `command-failed`, and an answer without a body string is `unreadable-output`
