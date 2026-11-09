---
id: 01a0b1fc-579f-7092-98af-601f9780d693
malleability: spec
---

# Changes

PROVIDES the Change skills change-standards, author-change, audit-change, manage-change, and report-changes
SO THAT product engineers and the agents that refine and apply Changes
CAN move a prioritized Output from proposal to applicable work without placing mutable work state in product truth

## Assertions

### Audit: Change skills

- skill-set: The author-change skill records, publishes, splits, merges, and reframes a Change; the manage-change skill makes every other Transition on one Change; the audit-change skill audits a record; the report-changes skill lists the open Changes; and the change-standards skill states the record they share.
- record-form-only: The Change skills write and read only the record the Change record decision states, and read another form only to carry its proposal into a new record.
- provider-rules: The Change skills carry every rule they apply, cite no methodology chapter path, and name no methodology version.

### Test.Property: report-changes

- report-rows: `report-changes` lists each open Change of the declared store that passes its filters, one row each with the Change's number, URL, title, Product, Maturity, Lifecycle, Priority, holder, and Parent as the store holds them, in the Priority order the coordination overlay declares, a Change with no Priority last, then by ascending issue number, over every page of the store ([test](tests/test_report_changes.property.l1.py))

### Test.Compliance: report-changes

- report-no-shorter-list: NEVER: `report-changes` returns a shorter list in place of a failure; a read that fails, returns unreadable output, or fills a bound — `100 issues per page, 10 pages`, `50 field values`, `100 blockers, one page`, `100 assignees`, or `100 events per page, 10 pages` — yields a blocked result naming the read or the bound and no row, and a Change whose Priority the declared order omits yields a blocked result naming the priority-order read and no row ([test](tests/test_report_changes.compliance.l1.py))
- report-no-write: NEVER: `report-changes` writes; it runs reading `gh` commands only, posts no comment, writes no field, assignee, or blocker, and its script writes no file ([test](tests/test_report_changes.compliance.l1.py))

### Test.Mapping: audit-change runner

- read-relations-parent: `read-relations` maps a `Parent` number field value, integer or float, to the issue number it names and an absent value to `null` ([test](tests/test_audit_change_relations_parent.mapping.l1.py))

### Test.Compliance: audit-change runner

- read-relations-absorbers: ALWAYS: `read-relations` returns as `absorbers` the issues whose `Predecessors` value, split at every comma followed by one space, names the named issue, and never the issues the named issue's own `Predecessors` value names ([test](tests/test_audit_change_relations.compliance.l1.py))
- read-relations-pages: ALWAYS: `read-relations` reads the store's issue pages in order until the store reports no further page, and returns a blocked result naming `100 issues per page, 10 pages` when the tenth page still reports a further page ([test](tests/test_audit_change_relations.compliance.l1.py))
- read-relations-fields: ALWAYS: `read-relations` returns a blocked result naming `50 issue field values per issue` when an issue's field-value connection reports a further page, and returns no Product or Parent read from that partial connection ([test](tests/test_audit_change_relations.compliance.l1.py))
- runner-no-file: NEVER: the bundled runner of `audit-change` writes a file; each invocation reads one JSON request on stdin and writes one JSON result on stdout, and the SPX run journal is the only state that persists between requests ([test](tests/test_audit_change_run.compliance.l1.py))
- runner-checkout-root: ALWAYS: the `audit-change` request names the Product's checkout root, which its caller resolves from the coordination overlay, and the runner reads the candidate and every path a record names, the Decision Records and Nodes its Declarations name, under that root, runs its git and spx commands with that root as the working directory, returns a blocked result naming the root when the request carries none or the root is no repository checkout, and keeps its containment check against that root, so a change audit whose candidate and record paths lie in another worktree than the session's seals its run ([test](tests/test_audit_change_run.compliance.l1.py))
- read-authority: ALWAYS: the runner's `read-authority` operation reads a Change's field-change events at 100 per page and at most 10 pages, reads no comment, and returns a blocked result naming the bound when the read fills it ([test](tests/test_audit_change_authority.compliance.l1.py))
- read-published: ALWAYS: the runner's `read-published` operation takes an operation name and a canonical `<owner>/<repo>#<N>` issue identity, reads that issue's body through one `gh` query, writes nothing, and returns the body or the empty string; a malformed request is `invalid-request`, a failed or unrunnable `gh` call is `command-failed`, and an answer without a body string is `unreadable-output` ([test](tests/test_audit_change_published.compliance.l1.py))
