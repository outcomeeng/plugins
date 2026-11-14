---
id: 01a1d6b6-1ebb-7e9e-b098-25d90afaadea
malleability: spec
---

# Report changes

PROVIDES the report-changes skill, which lists the open Changes of a Change Store with what each waits for
SO THAT the Operator and the agents that refine and apply Changes
CAN see which Changes wait, which are held, and which are blocked

The record each row reads is the one [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states.

## Assertions

### Test.Compliance: store homes

- pdr-rules: ALWAYS: report-changes reads each part of a record it reports from the home the github-store mapping of the Change record decision names.

### Test.Property: report rows

- report-rows: report-changes lists each open Change of the declared store that passes its filters, one row each with the Change's number, URL, title, Product, Maturity, Lifecycle, Priority, holder, and Parent as the store holds them, in the Priority order `spx/local/changes.md` declares, a Change with no Priority last, then by ascending issue number, over every page of the store. ([test](tests/test_report_changes.property.l1.py))

### Test.Mapping: report-columns

Each row derives these columns from the Change and its Transition comments.

| Case                          | Column      | Value                                                                                                                                                                                                                                                                                                                                      |
| ----------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| root                          | root        | the Change reached by following parent to one with none, or unresolved when the chain closes on a cycle or an absent Change                                                                                                                                                                                                                |
| blockers                      | blockers    | each blocker with its state                                                                                                                                                                                                                                                                                                                |
| changeset                     | changeset   | the branch and head commit the newest release comment's handoff names, with the pull request's checks when it names one, or none when the Change has no release comment                                                                                                                                                                    |
| next-action                   | next action | the next subsection that handoff names, verbatim, or none recorded when the Change has no release comment                                                                                                                                                                                                                                  |
| waiting-priority              | waiting     | waiting: Priority, for a Submitted Proposed Change with no Parent                                                                                                                                                                                                                                                                          |
| waiting-operator              | waiting     | waiting: the Operator's next move, for any other Submitted Change                                                                                                                                                                                                                                                                          |
| waiting-holder                | waiting     | holder: the holder with its claim's session and worktree, for a held Available Change, adding checks when its pull request holds a check that has not concluded success                                                                                                                                                                    |
| waiting-blockers              | waiting     | blockers: the numbers of the blockers that hold it, for an unheld Available Change; an open blocker holds it, and a blocker closed Abandoned is followed through the predecessors relation, step by step, to its survivor, the last Change no other Change's predecessors name, which holds it while open; an Applied survivor releases it |
| waiting-refinement            | waiting     | refinement, for an unheld Available Change with a blocker closed Abandoned whose survivor is closed Abandoned                                                                                                                                                                                                                              |
| blockers-two-merges-applied   | waiting     | claim, for an unheld Available Change whose one blocker A merged into B, B merged into C, and C closed Applied                                                                                                                                                                                                                             |
| blockers-two-merges-abandoned | waiting     | refinement, for an unheld Available Change whose one blocker A merged into B, B merged into C, and C closed Abandoned without a merge                                                                                                                                                                                                      |
| waiting-claim                 | waiting     | claim, for any other unheld Available Change                                                                                                                                                                                                                                                                                               |

### Test.Compliance: report-changes

- report-no-shorter-list: NEVER: report-changes returns a shorter list in place of a failure; a read that fails, returns unreadable output, or fills a bound yields a blocked result naming the read or the bound and no row, and a Change whose Priority the declared order omits yields a blocked result naming the priority-order read and no row. ([test](tests/test_report_changes.compliance.l1.py))
- report-no-write: NEVER: report-changes writes; it runs reading gh commands only, posts no comment, writes no field, assignee, or blocker, and its script writes no file and reads no overlay and no repository content. ([test](tests/test_report_changes.compliance.l1.py))

### Test.Scenario: reachability

- reachability: Given a store page that holds one open Change, when the report-changes script lists the store, then it returns one row for that Change under the request and result names the script exports. ([test](tests/test_report_changes.scenario.l1.py))

### Audit: report-changes

- report-request-values: ALWAYS: report-changes takes the Change Store and its Priority order from `spx/local/changes.md` and passes them to its script as request values.
