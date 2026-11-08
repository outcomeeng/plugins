---
id: 01a1b977-df00-71e7-b691-faf1b119c652
malleability: verification
---

# Operate Change

PROVIDES the operate-change skill, which makes every Transition of one Change, other than the moves of recording and publishing, as writes in a declared order with a complete readback
SO THAT the Operator and the agents that refine and apply Changes
CAN claim, release, submit, advance, lower, and close a Change, and learn from its result which writes landed when a Transition stops part way

## Assertions

### Test.Mapping: transitions

operate-change makes each Transition only on a Change in the state its row requires, changes only what its row states, and reports any other state without a write. ([test](tests/test_operate_change.mapping.l1.py))

| Case      | Requires                                                                                                                          | Changes                                                                                              |
| --------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| claim     | an Available Change with no holder                                                                                                | sets the holder                                                                                      |
| release   | a held Change                                                                                                                     | clears the holder; a Submitted Change returns to Available                                           |
| submit    | an Available Change that waits for the Operator's next move, or whose settled judgment the holder finds reopened, with its reason | Available to Submitted, its comment naming the reopened judgment in reason when the holder finds one |
| advance   | a Submitted Change that meets its next maturity-ready row, or a Sliced Leaf that meets the applicable row                         | raises the Maturity                                                                                  |
| lower     | a Framed, Sliced, or Applicable Change, with a reason                                                                             | lowers the Maturity                                                                                  |
| applied   | the close condition of the Change's type                                                                                          | to Applied                                                                                           |
| abandoned | an open Change                                                                                                                    | to Abandoned                                                                                         |

### Test.Mapping: maturity-ready

operate-change advances a Leaf to a Maturity only when its record meets that row and every row above it. operate-change judges each row by the form check's result and the Change Store; whether the Declarations name every Node and Decision Record the Change touches stays with the Operator's review, and whether the record passed audit stays with the Auditor's sealed result for the current body revision and Base. ([test](tests/test_operate_change.mapping.l1.py))

| Case       | The Leaf's record                                                                                                                                               |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| proposed   | its Statement of Intent states Output, Why, and Verification                                                                                                    |
| framed     | its Declarations hold a subsection for each Node and Decision Record it touches, or none and its reason                                                         |
| sliced     | at most five Node subsections, a Node subsection with an operation included                                                                                     |
| applicable | each Node its infrastructure lines name stands on the default branch with State Passing or is blocked on the Change that builds it, and the record passed audit |

### Test.Mapping: store-writes

Where the Change Store is a GitHub repository, operate-change writes each part a Transition changes to the one home its row names. ([test](tests/test_operate_change.mapping.l1.py))

| Case       | Home                                                                                     |
| ---------- | ---------------------------------------------------------------------------------------- |
| maturity   | the organization issue field Maturity                                                    |
| lifecycle  | the organization issue field Lifecycle                                                   |
| holder     | the issue's one assignee, with the session and worktree its newest claim comment records |
| transition | one issue comment                                                                        |

### Test.Compliance: closing

- leaf-applied: ALWAYS: operate-change closes a Leaf Applied only when the merge commit of the Changeset its holder closes it on is an ancestor of the default branch, every merge gate passed, each Node holds every result its Malleability requires, every Declarations line stands on the default branch, and the audit at close found nothing. ([test](tests/test_operate_change.compliance.l1.py))
- terminal: NEVER: operate-change moves an Applied or Abandoned Change. ([test](tests/test_operate_change.compliance.l1.py))
- terminal-kept: NEVER: operate-change deletes a Change, its body's edit history, or a Transition comment. ([test](tests/test_operate_change.compliance.l1.py))
- lower-claim: ALWAYS: operate-change keeps the Claim of an Applier that lowers its Applicable record to Sliced to write a decision line, and after every other lowering it writes the holder's Handoff and releases the Change. ([test](tests/test_operate_change.compliance.l1.py))

### Test.Compliance: binding

- review-binding: ALWAYS: operate-change advances to Sliced only while the current body revision and Base equal the pair the Operator's review read, or a pair that review carries forward to, and posts the advance comment only while that pair stands, so the body revision the edit history holds and the Base value the Base field's change events hold at the comment's time are the bound pair; its claim for Application confirms that the current record is that pair or one the review carries forward to. ([test](tests/test_operate_change.compliance.l1.py))
- audit-binding: ALWAYS: operate-change advances to Applicable only on a sealed audit result whose judged body revision and Base equal the current body revision and Base, comparing the SHA-256 of the current body and the current Base with the pair the sealed result names, posts the advance comment only while that pair stands, so the body revision the edit history holds and the Base value the Base field's change events hold at the comment's time are the bound pair, and refuses a sealed result for another revision or another Base; the review's carry-forward carries no audit onto a revision the audit did not judge. ([test](tests/test_operate_change.compliance.l1.py))
- review-carry: ALWAYS: after a later publish, operate-change carries the review of a part forward only while the operation keeps its kind and its paths, the Decision Records that govern the part stay the same, and the part and each line of its context read the same in the old and the new revision, at each Base and after the Change; a Base that no longer resolves carries no review forward. ([test](tests/test_operate_change.compliance.l1.py))
- review-part: ALWAYS: operate-change takes a part as a row by its slug, a heading, or any other single line, with every heading above it, the header row of its table, and the line that opens its Scenario or list as its context; for a deletion or a move of a file the part is the file, and for a deletion or a move of a Node it is the Nodes its branch holds, with every spec, Decision Record, contract file, and Outcome record in them. ([test](tests/test_operate_change.compliance.l1.py))

### Test.Compliance: structure and blockers

- change-type: ALWAYS: operate-change takes a Change as a Parent when another record names it as its parent, and as a Leaf otherwise, deriving the type from those relations and never storing it. ([test](tests/test_operate_change.compliance.l1.py))
- parent-maturity: ALWAYS: operate-change sets a Parent's Maturity only through an advance or a lower of its Statement of Intent, sets nothing on a Parent when a Child moves, and never advances a Parent to Applicable. ([test](tests/test_operate_change.compliance.l1.py))
- blocker-abandoned: ALWAYS: when a blocking Change closes Abandoned through a merge, operate-change passes its block to the Change that names it as predecessor, and when one closes Abandoned without a merge, it returns the dependent Change to Refinement. ([test](tests/test_operate_change.compliance.l1.py))
- blocker-cycle: NEVER: operate-change advances a member of a blocker cycle to Sliced or Applicable, or claims one for Application. ([test](tests/test_operate_change.compliance.l1.py))

### Test.Compliance: transition function

- transition-function: ALWAYS: operate-change's module exposes one transition function that makes one Transition, posts its comment, and returns the result its script writes, so author-change reaches it by a `__file__`-relative import. ([test](tests/test_operate_change.compliance.l1.py))

### Test.Compliance: transition log

- log-block: ALWAYS: operate-change posts one comment for every Transition it makes, holding one fenced YAML block and nothing else, and the comment's time is the Transition's time. ([test](tests/test_operate_change.compliance.l1.py))
- log-keys: ALWAYS: the block holds transition, the move; maturity, the Change's Maturity at the move as the Change Store spells it; harness, the token the Provider assigns to the agent harness; session, the harness's session id; machine, the user and the short host name as user@host; and worktree, the absolute path of the worktree the session works in. ([test](tests/test_operate_change.compliance.l1.py))
- log-extras: ALWAYS: a lower adds reason, a submit of a Change whose settled judgment the holder finds reopened adds reason naming that judgment, a release adds handoff with at least the branch, the head commit, and the next subsection, and an applied Transition of a Leaf adds changeset with its merge commit. ([test](tests/test_operate_change.compliance.l1.py))
- handoff-keys: ALWAYS: the handoff of a release comment is a mapping that holds branch, the branch name; head, the full head commit; next, the next subsection by its heading; and pull_request, the pull request's URL, when one exists. ([test](tests/test_operate_change.compliance.l1.py))
- log-closed: NEVER: the block holds another key, prose outside reason, or a position key. ([test](tests/test_operate_change.compliance.l1.py))
- log-closed-check: NEVER: operate-change posts a Transition block that holds a key the log-keys and log-extras lines do not name. ([test](tests/test_operate_change.compliance.l1.py))
- log-no-authority: NEVER: operate-change reads authority from a Transition comment, or writes a delegate, a party the agent acts for, or words of the Operator into one. ([test](tests/test_operate_change.compliance.l1.py))

### Test.Compliance: GitHub store

- github-binding: ALWAYS: operate-change's advance to Sliced or to Applicable binds the body revision the issue's edit history holds at the time of the advance's comment and the Base value the Base field's change events hold at that time; at the advance to Sliced it confirms that pair equals the pair the Operator's review read or one that review carries forward to, and at the advance to Applicable it confirms that pair equals the pair the sealed audit result judged, with no carry-forward. ([test](tests/test_operate_change.compliance.l1.py))
- github-one-holder: ALWAYS: operate-change keeps at most one assignee on a Change issue. ([test](tests/test_operate_change.compliance.l1.py))
- github-parent: ALWAYS: operate-change reads a Parent number as an issue in the Child's own Change Store. ([test](tests/test_operate_change.compliance.l1.py))
- write-order: ALWAYS: operate-change makes a Transition's writes in this order: the Maturity field, the Lifecycle field, the assignee, the Transition comment, and last the issue's open or closed state; it skips each write the Transition's row does not change, so a comment stands only after every field and assignee write of its Transition landed. ([test](tests/test_operate_change.compliance.l1.py))
- ordered-write: ALWAYS: operate-change makes each write of a Transition in the write-order, reads the Change back, and completes only when every value equals the intended state; after a failed write or a differing readback it makes no later write, undoes no write that landed, and reports the writes that landed, the one that failed, and the observed state. ([test](tests/test_operate_change.compliance.l1.py))

### Audit: actors

- transition-actor: ALWAYS: operate-change lets any person or agent claim; lets the holder release, submit, advance a Sliced Leaf to Applicable, and close a Leaf Applied; makes an advance to Framed or Sliced, a lower when a settled judgment reopens, a close Abandoned other than of the Change a merge absorbs, and a close of a Parent Applied only on the Operator's move; closes the absorbed Change of a merge Abandoned for the Refiner, on the Operator's direction; lets the Applier lower its Applicable Change to Sliced to write a decision line; lowers to Sliced after a failed Application check; and makes the lower of a reframe, the lower of a publish that writes the body of an Applicable record, and the abandoned Transition of a directed merge through its transition function, for author-change.
- maturity-actor: ALWAYS: operate-change advances a Leaf to Framed only when the Operator judges every Declarations line settled, to Sliced only after the Operator reviewed every decision line and every removal, deletion, move, and replacement on a Decision Record or on a Node whose Malleability is not spec, and each file in such a Node, and to Applicable only for its holder.
- one-unit: ALWAYS: operate-change advances to Sliced only a Leaf that is one unit an Applier integrates on its own.
- parent-applied: ALWAYS: operate-change closes a Parent Applied only on the Operator's move, once the Operator judges its intent met and no Child is open.
