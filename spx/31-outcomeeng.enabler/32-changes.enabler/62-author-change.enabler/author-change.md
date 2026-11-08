---
id: 01a1b993-9c50-7d16-9ca9-6e1460ff5172
malleability: verification
---

# Author Change

PROVIDES the author-change skill, which records, publishes, splits, merges, and reframes Change records from Change Drafts that pass the form check
SO THAT Refiners
CAN publish only records whose form a program has checked

## Assertions

### Test.Compliance: publishing

- form-check: ALWAYS: below Applicable, and on a publish that writes the body of an Applicable record, the author-change script runs the form check on the Change Draft before the publish, and publishes nothing while the check fails.
- base-on-body: ALWAYS: the script sets a Leaf's base only on a publish that writes the record's body, and a publish that writes only metadata, such as a claim, a submission, or a blocker, keeps it.
- stale-revision: ALWAYS: the script's publish run reads the record at its start, hands that record to the form check, and compares its last edit with the last edit right before its write, and the publish fails when the two differ.
- detect-restore: ALWAYS: where the Change Store accepts no expected revision, the script reads the record's edit history after its write, restores a revision it did not write that landed between its own read and its own write, and counts the publish as failed; a revision that landed after its own write stands, and the script counts that publish as failed too.
- operator-bound-base: ALWAYS: the script has the form check fail the publish of a Sliced record whose new base changes a file the record deletes, moves, or replaces, where the Operator's review binds that operation, and a former Base that no longer resolves counts as such a change; every other such publish succeeds.
- github-race: ALWAYS: because GitHub's issue update takes no expected revision, the script records the body's last edit at its read and fails the publish when the last edit right before its write differs; after its write it reads the edit history, restores a revision another writer wrote between its read and its write, where GitHub still holds it, and fails the publish; a revision written after its write stands, and that publish fails too.
- publish: ALWAYS: the script's publish writes the title, the body, and each metadata key the Draft changes and no part it leaves unchanged, makes the lower to Sliced through operate-change's transition function when the Draft writes the body of an Applicable record, reads the record back, and completes only when every value equals the intended state, the Draft with the Maturity the lower wrote where the publish made one; otherwise it makes no later write and reports what it wrote.
- publish-body: ALWAYS: the script's publish of a Draft that writes the body of an Applicable record takes the form check, makes the lower to Sliced through operate-change's transition function, with its Transition comment, before it writes the body, leaves what follows the lower to operate-change's lower-claim rule, and reads the record back against the Draft at Maturity Sliced.
- publish-metadata: ALWAYS: the script's publish of a Draft that leaves the body unchanged writes the title and each metadata key the Draft changes, and no body, so the body, the base, and with them the audit stay as the Change Store holds them; the script's readback compares the body with the body it read at its start.

### Test.Compliance: records and Drafts

- record: ALWAYS: the script's record writes a new record from a Draft that passes the form check, with Maturity Proposed, Lifecycle Submitted for a Change with no Parent and Available for a Child, the recorder as holder, and for a Leaf the base the head of the default branch; recording is no Transition and posts no comment.
- split: ALWAYS: the script's split accepts only a Leaf below Applicable and records each Child with the split record as parent in the same Change Store; the split record then holds only its Statement of Intent, loses its base, and takes as its product the list of the Products its Children span.
- draft: ALWAYS: the script's draft writes a Change Draft from a stored record, its metadata except the holder, then its body.

### Test.Compliance: reframe and merge

- reframe: ALWAYS: the script's reframe edits a Change in place and lowers its Maturity to Proposed.
- merge: ALWAYS: the script's merge closes the absorbed Change Abandoned and adds it to the survivor's predecessors.
- transition-import: ALWAYS: the script makes the lower of a reframe, the lower of a publish that writes the body of an Applicable record, and the abandoned Transition of a merge through operate-change's transition function, reached by a `__file__`-relative import.

### Test.Compliance: form check call

- check-request: ALWAYS: the script calls the form check with one request that names the Draft's text or its path, the Product's checkout root, the operation, the record the Change Store holds or null, the record of each Change the Draft names as a blocker, read from the Change Store, and the Change Store's size limit, reads one result that holds pass or fail and every finding, and publishes only on pass.
- check-import: ALWAYS: the script reaches the form check through a `__file__`-relative import of the check function of the change-standards skill, which returns for a request the result the form-check script writes for it.
- check-reads-only: NEVER: the script's call of the form check writes a file or the Change Store; the script makes every write of a publish after the check returns pass.

### Audit: actors and judgment

- store-outside: ALWAYS: author-change takes the Change Store of a Product from the parameter the Operator records outside the Product Tree, and it moves no Change between Change Stores.
- merge-direction: ALWAYS: author-change merges two Changes only on the Operator's direction.
- same-passage: ALWAYS: of two open Changes that amend the same passage of a file, author-change names the other as a blocking Change in the one that reaches Application second.
- path-repair: ALWAYS: when a Change deletes or moves a path, author-change gives each file that names that path its own subsection when it is of a kind a subsection holds, leaves any other such file to the Applier as a Mechanical Repair or to a delegate, has a generated file repaired at its declared source and regenerated, and leaves every surviving link to Validate.
- operator-answers: ALWAYS: author-change puts every answer the Operator gives in Refinement into a Declarations line, with each condition, exception, boundary, and expected outcome.
- first-intent: ALWAYS: author-change edits a record in place, so the store's edit history keeps the first Statement of Intent readable.
