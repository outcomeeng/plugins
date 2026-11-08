---
id: 01a0b1fc-579f-7092-98af-601f9780d693
malleability: spec
---

# Changes

PROVIDES the Change skills change-standards, author-change, audit-change, operate-change, and report-changes
SO THAT product engineers and the agents that refine and apply Changes
CAN move a prioritized Output from proposal to applicable work without placing mutable work state in product truth

## Assertions

### Audit: Change skills

- skill-set: The author-change skill records, publishes, splits, merges, and reframes a Change; the operate-change skill makes every other Transition on one Change; the audit-change skill audits a record; the report-changes skill lists the open Changes; and the change-standards skill states the record they share.
- record-form-only: The Change skills write and read only the record the Change record decision states, and read another form only to carry its proposal into a new record.
- provider-rules: The Change skills carry every rule they apply, cite no methodology chapter path, and name no methodology version.

### Test.Property: report-changes

- report-rows: `report-changes` lists each open Change of the declared store that passes its filters, one row each with the Change's number, URL, title, Product, Maturity, Lifecycle, Priority, holder, and Parent as the store holds them, in the Priority order the coordination overlay declares, a Change with no Priority last, then by ascending issue number, over every page of the store ([test](tests/test_report_changes.property.l1.py))

### Test.Compliance: report-changes

- report-no-shorter-list: NEVER: `report-changes` returns a shorter list in place of a failure; a read that fails, returns unreadable output, or fills a bound — `100 issues per page, 10 pages`, `50 field values`, `100 blockers, one page`, `100 assignees`, or `100 events per page, 10 pages` — yields a blocked result naming the read or the bound and no row, and a Change whose Priority the declared order omits yields a blocked result naming the priority-order read and no row ([test](tests/test_report_changes.compliance.l1.py))
- report-no-write: NEVER: `report-changes` writes; it runs reading `gh` commands only, posts no comment, writes no field, assignee, or blocker, and its script writes no file ([test](tests/test_report_changes.compliance.l1.py))
