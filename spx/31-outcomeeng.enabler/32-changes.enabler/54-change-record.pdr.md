# Change Record

DEFINES Change record AS the metadata and the body of one Change, held only in the Change Store
DEFINES Change Draft AS a local copy of a Change record's metadata, except its holder, as YAML front matter, followed by its body
DEFINES Base AS the commit a Change record's base field names
DEFINES Transition AS one of the seven moves of a Change: claim, release, submit, advance, lower, applied, and abandoned

GOVERNS the Change record SO THAT the Operator and the agents that refine and apply Changes CAN RELY ON a record whose form a program checks before every publish below Applicable, an Applier that starts only on an audited record, and an advance to Framed or Sliced that only the Operator makes

## Verification

### Test.Mapping: record-keys

A record's metadata holds exactly these keys, each with this value, and each changes only through the operations its row names. A key with no value holds null, and a list with no entry holds [].

| Case          | Value                                                                                                             | Changes through                                                                                         |
| ------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| title         | the intended Output, in at most 15 words                                                                          | recording or a publish                                                                                  |
| product       | a Leaf's one Product; a Parent's list of the Products its Children span                                           | recording, a publish, a split, or recording a Child                                                     |
| maturity      | Proposed, Framed, Sliced, or Applicable                                                                           | recording, an advance, or a lower                                                                       |
| lifecycle     | Available, Submitted, Applied, or Abandoned                                                                       | recording, which sets Submitted for a Change with no Parent and Available for a Child, or a Transition  |
| holder        | the one person or agent that holds the Change, or null; absent from a Change Draft                                | recording, which sets the recorder, a claim, or a release                                               |
| parent        | the Parent's Change reference, or null                                                                            | recording or a split                                                                                    |
| predecessors  | the Changes this Change absorbed by a merge, [] when it absorbed none                                             | a merge                                                                                                 |
| blockers      | the Changes this Change waits for, [] when it waits for none                                                      | a publish                                                                                               |
| base          | for a Leaf, the head of the default branch at its latest publish that writes the body; a Parent holds no base key | recording a Leaf, a publish that writes its body, or its removal when a Child makes the record a Parent |
| priority      | the Change's Priority, null until the Priority decision                                                           | the Priority decision                                                                                   |
| primary_value | Offering, Quality, Capability, or Safety, null until the Priority decision                                        | the Priority decision                                                                                   |
| investment    | Harvest, Shield, Frontier, or Seed, null until the Priority decision                                              | the Priority decision                                                                                   |

### Test.Mapping: record-body

A record's body holds exactly these sections, in this order.

| Case   | Record   | Sections                                                                                      |
| ------ | -------- | --------------------------------------------------------------------------------------------- |
| leaf   | a Leaf   | Statement of Intent, then Declarations; a Proposed Leaf may hold only its Statement of Intent |
| parent | a Parent | Statement of Intent                                                                           |

### Test.Mapping: statement-of-intent

The Statement of Intent states these three parts, in this order, in at most 120 words.

| Case         | Part         | States                                                                                                                                                                                                                                  |
| ------------ | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| output       | Output       | the Output the Change achieves                                                                                                                                                                                                          |
| why          | Why          | the truth the work brings a lower layer up to, what the Operator settled by judgment, the question a prototype answers, or the Output and the condition it moves, with the observed state that gave rise to the Change where one exists |
| verification | Verification | the verification that shows the Output achieved, by its type, and what it finds                                                                                                                                                         |

### Test.Mapping: subsection-headings

Each Declarations subsection stands in Application order under the heading its row names.

| Case     | Subsection for                                                                                                   | Heading                                                                                |
| -------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| existing | an existing Node, Decision Record, or file, a moved one included                                                 | its path from spx/ at the Base                                                         |
| new      | a new Node or Decision Record                                                                                    | its kind, its slug, and the two existing siblings between which the Applier inserts it |
| created  | a contract file, Outcome record, Product spec, or file of a Product with no Product Tree that the Change creates | its path from spx/, or from the repository root for a Product with no Product Tree     |
| no-tree  | an existing file of a Product with no Product Tree                                                               | the file's path from the repository root at the Base                                   |
| in-moved | a file inside a moved Node, other than its spec                                                                  | its path after the move, after the Node's move subsection                              |

### Test.Mapping: payloads

Below its heading, a subsection holds the one payload its row names.

| Case         | Payload                                                                                       | Holds                                                   |
| ------------ | --------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| line-edits   | an optional yaml front-matter block, then one block fenced as diff                            | the lines the Change adds, removes, or keeps as context |
| replacement  | one block fenced with the file's own language, and text for a file whose own language is diff | the whole file after the Change, front matter included  |
| move-rewrite | a diff block of only the two rename headers, then a replacement                               | the move, and the whole file at its new path            |

### Test.Mapping: headers

A diff block can open with the git extended header its row names, before any - or + line, and the header declares the row's operation.

| Case   | Header                                                      | Operation                                                                                                                                                |
| ------ | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| delete | deleted file                                                | deletes the file the heading names; under a Node's directory heading, prunes the Node and its branch under the pruning check; nothing follows the header |
| create | new file                                                    | creates the file the heading names; every line after it is a + line                                                                                      |
| move   | rename from the heading's path, then rename to the new path | moves the file or the Node directory; - and + lines can follow, and under a moved Node's heading they edit its spec                                      |

### Test.Mapping: diff-lines

Each line of a diff block takes the form its row names and holds what that row states.

| Case            | Line      | Holds                                                                                                                     |
| --------------- | --------- | ------------------------------------------------------------------------------------------------------------------------- |
| added           | +         | a row as its spec or Decision Record holds it after the Change, with every line of a Scenario and every row of a table    |
| removed         | -         | a row as the Base holds it, with every line of a Scenario and every row of a table                                        |
| context         | unmarked  | a heading the Change keeps; for a table row, the heading of its Mapping or Evaluate subsection and the table's header row |
| heading-added   | + heading | a heading the Change adds                                                                                                 |
| heading-removed | - heading | a heading the Change removes; a renamed heading is a - and + pair                                                         |
| file-added      | +         | a line of a contract file, Outcome record, or Product spec after the Change                                               |
| file-removed    | -         | a line of such a file as the Base holds it                                                                                |
| file-context    | unmarked  | a line of such a file around an edit, as the Base holds it                                                                |
| no-tree-added   | +         | a statement of a Product with no Product Tree, by its slug                                                                |
| no-tree-removed | -         | a statement, a section, or a Glossary entry of a Product with no Product Tree, as the Base holds it                       |

### Test.Compliance: Declaration lines

- body-lines-only: ALWAYS: below its headers, the diff block of a Node or Decision Record holds only lines of its body, each naming its target by slug, each line of an opening by its keyword, and a DEFINES line by its keyword and its term; the diff block of a contract file, Outcome record, or Product spec holds literal lines of the file.
- no-tag: NEVER: a Declarations line adds a tag.
- plain-slug: ALWAYS: a slug whose test file, eval rule, or probe protocol is absent at the Base stands plain in its + line.
- table-case: ALWAYS: a table row's case reads as its subsection's slug, a slash, and the case slug, such as date-phrases/tomorrow-5pm.
- front-matter-block: ALWAYS: line edits that set a Node's front-matter field hold the field and its value after the Change in a yaml block before the diff, a replacement holds the whole front matter instead, a replaced spec keeps its Node's id, and a moved Node keeps its id.
- no-index: NEVER: a record names an Index for a new Node or Decision Record.
- move-reads: ALWAYS: under a move, a - line and each context line read the old path at the Base, and a + line holds the row as the new path holds it after the Change.

### Test.Compliance: Declaration operations

- one-payload: NEVER: a subsection holds both payloads, except a move that rewrites its file.
- fence: ALWAYS: a replacement's outer fence is longer than any fence inside the file, and a block with no language fails the form check.
- no-mode: NEVER: a header carries a file mode, or another git header stands in a record; a replacement or a move keeps the file's mode, which nothing checks.
- operation-kinds: ALWAYS: new file creates only a contract file, an Outcome record, the Product spec, or a file of a Product with no Product Tree; a deletion or a move acts on a Node or on a Decision Record, a spec, a contract file, an Outcome record, the Product spec, or a file of a Product with no Product Tree; a replacement acts on a file of these kinds; and every file an operation names is a regular text file.
- spec-deletion: NEVER: a Change deletes a spec apart from its Node, or deletes the Product spec.
- one-subsection-per-file: NEVER: two subsections of a Change write, move, or delete the same file, except a file inside a moved Node other than its spec, which takes its edits in its own subsection whose reads at the Base resolve through the move, a slug rename included.
- slug-rename: ALWAYS: a move that changes a Node's slug also renames its spec and its Outcome record to the new slug.
- path-naming: ALWAYS: the form check names each file at the Base that names, in a link or in any other text, the path of a file or Node the Change deletes or moves, or of a file inside such a Node, and skips every Knowledge root and every file the Product declares as dated history.
- format-at-close: ALWAYS: the Product's format command at the Base leaves a replacement unchanged; at close the command at the merge commit leaves the approved result, the approved replacement with its plain slugs linked, unchanged, and the file on the default branch reads the same as that result; after any difference the Change stays open and the Refiner rewrites the replacement under the merge-commit formatter.

### Test.Compliance: infrastructure lines

- infrastructure-line: ALWAYS: a Node subsection ends with one infrastructure line for each Assertion it adds or replaces at verification or implementation Malleability after the Change, and a subsection that hardens its Node holds one for every Assertion the Node holds after the Change.
- replaced-assertion: ALWAYS: an Assertion counts as added or replaced when its complete declaration differs from the Base, its complete declaration being its row and the group heading that fixes its verification type, or the whole subsection for a Mapping or Evaluate Assertion.
- infrastructure-form: ALWAYS: the line reads `Infrastructure:`, the Assertion's slug, and the path of each Node whose test infrastructure that Assertion's Evidence needs, each path in a code span and a comma between two paths, or `none` in their place.
- infrastructure-exists: ALWAYS: when the Refiner writes the line, each Node it names exists at the Base, or a blocking Change builds it.
- spec-node-none: NEVER: an Assertion of a spec-malleable Node carries an infrastructure line.
- none-leaf: ALWAYS: a Leaf that declares nothing holds none and its reason.

### Test.Mapping: maturity-ready

A Leaf's record meets a Maturity's row only when it meets that row and every row above it.

| Case       | The Leaf's record                                                                                                                                               |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| proposed   | its Statement of Intent states Output, Why, and Verification                                                                                                    |
| framed     | its Declarations hold a subsection for each Node and Decision Record it touches, or none and its reason                                                         |
| sliced     | at most five Node subsections, a Node subsection with an operation included                                                                                     |
| applicable | each Node its infrastructure lines name stands on the default branch with State Passing or is blocked on the Change that builds it, and the record passed audit |

### Test.Mapping: transitions

Each Transition takes a Change in the state its row requires and changes what its row states.

| Case      | Requires                                                                                                                          | Changes                                                    |
| --------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| claim     | an Available Change with no holder                                                                                                | sets the holder                                            |
| release   | a held Change                                                                                                                     | clears the holder; a Submitted Change returns to Available |
| submit    | an Available Change that waits for the Operator's next move, or whose settled judgment the holder finds reopened, with its reason | Available to Submitted                                     |
| advance   | a Submitted Change that meets its next maturity-ready row, or a Sliced Leaf that meets the applicable row                         | raises the Maturity                                        |
| lower     | a Framed, Sliced, or Applicable Change, with a reason                                                                             | lowers the Maturity                                        |
| applied   | the close condition of the Change's type                                                                                          | to Applied                                                 |
| abandoned | an open Change                                                                                                                    | to Abandoned                                               |

### Test.Compliance: binding

- review-binding: ALWAYS: the Operator's review binds the record body and the Base it read, the advance to Sliced records both, and the advance and the Application check confirm that the current record is that one or one the review carries forward to.
- review-carry: ALWAYS: after a later publish, the review of a part carries forward only while the operation keeps its kind and its paths, the Decision Records that govern the part stay the same, and the part and each line of its context read the same in the old and the new revision, at each Base and after the Change; a Base that no longer resolves carries no review forward.
- review-part: ALWAYS: a part is a row by its slug, a heading, or any other single line, with every heading above it, the header row of its table, and the line that opens its Scenario or list as its context; for a deletion or a move of a file the part is the file, and for a deletion or a move of a Node it is the Nodes its branch holds, with every spec, Decision Record, contract file, and Outcome record in them.
- audit-binding: ALWAYS: the audit binds the body and the Base it judged, the advance to Applicable records both, a publish that writes the body of an Applicable record returns the Change to Sliced and takes the form check before the audit runs again, and a publish that writes only metadata keeps the audit.

### Test.Compliance: closing

- leaf-applied: ALWAYS: a Leaf closes Applied only when the merge commit of the Changeset its holder closes it on is an ancestor of the default branch, every merge gate passed, each Node holds every result its Malleability requires, every Declarations line stands on the default branch, and the audit at close found nothing.
- terminal: NEVER: a Transition moves an Applied or Abandoned Change.
- reframe: ALWAYS: a reframe edits a Change in place and lowers its Maturity to Proposed.
- lower-claim: ALWAYS: an Applier that lowers its Applicable record to Sliced to write a decision line keeps its Claim, and after every other lowering the holder writes a Handoff and releases the Change.

### Test.Compliance: structure and lineage

- change-type: ALWAYS: a Change is a Parent when another record names it as its parent, and a Leaf otherwise; the type derives from those relations and is never stored.
- parent-maturity: ALWAYS: only the Operator's advances on a Parent's Statement of Intent set its Maturity, its Children set nothing, and a Parent never reaches Applicable.
- merge: ALWAYS: a merge closes the absorbed Change Abandoned and adds it to the survivor's predecessors.
- blocker-abandoned: ALWAYS: a blocking Change that closes Abandoned through a merge passes its block to the Change that names it as predecessor, and one that closes Abandoned without a merge returns the dependent Change to Refinement.
- blocker-cycle: NEVER: a member of a blocker cycle remains Sliced or Applicable until the Refiner removes the cycle.

### Test.Compliance: transition log

- log-block: ALWAYS: every Transition posts one comment holding one fenced YAML block and nothing else, and the comment's time is the Transition's time.
- log-keys: ALWAYS: the block holds transition, the move; maturity, the Change's Maturity at the move as the Change Store spells it; harness, the token the Provider assigns to the agent harness; session, the harness's session id; machine, the user and the short host name as user@host; and worktree, the absolute path of the worktree the session works in.
- log-extras: ALWAYS: a lower adds reason, a release adds handoff with at least the branch, the head commit, and the next subsection, and an applied Transition of a Leaf adds changeset with its merge commit.
- log-closed: NEVER: the block holds another key, prose outside reason, or a position key; the plugins name no Position.
- log-no-authority: NEVER: anyone reads authority from a Transition comment, and no delegate, no party the agent acts for, and no words of the Operator appear in it.

### Test.Compliance: form check

- form-check: ALWAYS: below Applicable, and on a publish that writes the body of an Applicable record, a program checks the form of a record before the publish, and nothing publishes while the check fails.
- base-on-body: ALWAYS: base moves only on a publish that writes the record's body, and a publish that writes only metadata, such as a claim, a submission, or a blocker, keeps it.
- stale-revision: ALWAYS: the form check fails a publish when the revision the Change Store holds changed since the publisher read it.
- detect-restore: ALWAYS: where the Change Store accepts no expected revision, the Provider reads the record's edit history after the write, restores a revision it did not write that landed between its own read and its own write, and counts the publish as failed; a revision that landed after its own write stands, and that publish counts as failed too.
- size-limit: ALWAYS: the form check fails a publish whose record exceeds the Change Store's size limit, and names the limit.
- operator-bound-base: ALWAYS: the form check fails the publish of a Sliced record whose new base changes a file the record deletes, moves, or replaces, where the Operator's review binds that operation, and a former Base that no longer resolves counts as such a change; every other such publish succeeds, and the audit reads the operation at the new Base.
- one-home: NEVER: a metadata field stands in the body, or the Change Store holds a field in two places.

### Test.Mapping: github-store

Where the Change Store is a GitHub repository, each part of a record has the one home its row names.

| Case          | Home                                                                                     |
| ------------- | ---------------------------------------------------------------------------------------- |
| title         | the issue title                                                                          |
| body          | the issue body                                                                           |
| product       | the organization issue field Product                                                     |
| maturity      | the organization issue field Maturity                                                    |
| lifecycle     | the organization issue field Lifecycle                                                   |
| holder        | the issue's one assignee, with the session and worktree its newest claim comment records |
| parent        | the organization number issue field Parent                                               |
| predecessors  | the organization text issue field Predecessors                                           |
| blockers      | the issue's native dependencies                                                          |
| base          | the organization text issue field Base                                                   |
| priority      | the organization issue field Priority                                                    |
| primary_value | the organization issue field Value                                                       |
| investment    | the organization issue field Investment                                                  |
| transition    | one issue comment                                                                        |

### Test.Compliance: github-store

- github-binding: ALWAYS: an advance to Sliced or to Applicable binds the body revision the issue's edit history holds at the time of the advance's comment and the Base value the Base field's change events hold at that time, and the Provider confirms the binding only while the current body equals that revision and the current Base equals that value, or the Operator's review carries forward to them.
- github-later-edit: ALWAYS: a body edit after an advance keeps the review of each part that review-carry carries forward, and takes a new audit.
- github-race: ALWAYS: because GitHub's issue update takes no expected revision, the Provider records the body's last edit at its read and fails the publish when the last edit right before its write differs; after its write it reads the edit history, restores a revision another writer wrote between its read and its write, where GitHub still holds it, and fails the publish; a revision written after its write stands, and that publish fails too.
- github-one-holder: ALWAYS: the Provider keeps at most one assignee on a Change issue.
- github-parent: ALWAYS: a Child lives in its Parent's Change Store, so the Parent number names the Parent's issue in that store.
- github-limit: ALWAYS: the size limit of a GitHub Change Store is 65,536 characters of issue body.

### Audit: record content

- audit-before-applicable: ALWAYS: an Auditor audits a Sliced Leaf before its holder advances it to Applicable, each Declarations line against every Decision Record that governs its Node at the Base, read as the Declarations change it, and every finding blocks.
- audit-at-close: ALWAYS: before a Leaf closes Applied, an Auditor audits the default branch against its record: each Assertion and decision stands as its line states, and the verification the Statement of Intent names finds what it states.
- operator-answers: ALWAYS: every answer the Operator gives in Refinement reaches a Declarations line, with each condition, exception, boundary, and expected outcome.
- facts-checked: ALWAYS: the Refiner checks every fact the record cites against the latest checkout of the owning repository, or, for a Product with no Product Tree, against the cited source by path and commit.
- sets-apart: ALWAYS: each part of the body holds only what sets this Change apart; a Child links settled rationale, and a Parent copies none of its Children's content.
- no-person: NEVER: a record or a Handoff names an accountable person or holds conversation text.
- first-intent: ALWAYS: the Statement of Intent as first written stays readable while the Refiner edits the current content.
- terminal-kept: ALWAYS: a Change in a terminal Lifecycle and its edit history stay queryable until the owning Product's Change-retention policy permits their removal.
- provider-rules: ALWAYS: the Change skills carry every rule they apply, cite no methodology chapter path, and name no methodology version.

### Audit: actors and judgment

- transition-actor: ALWAYS: any person or agent claims; the holder releases, submits, advances a Sliced Leaf to Applicable, and closes a Leaf Applied; only the Operator advances to Framed or Sliced, lowers when a settled judgment reopens, closes a Change Abandoned other than the Change a merge absorbs, and closes a Parent Applied; the Refiner closes the absorbed Change of a merge Abandoned, on the Operator's direction; the Applier lowers its Applicable Change to Sliced to write a decision line; a failed Application check and a publish that writes the body of an Applicable record lower to Sliced; and a Refiner's reframe lowers to Proposed.
- maturity-actor: ALWAYS: the recorder records a Leaf at Proposed; the Operator advances it to Framed on judging every Declarations line settled, and to Sliced after reviewing every decision line and every removal, deletion, move, and replacement on a Decision Record or on a Node whose Malleability is not spec, and each file in such a Node; and its holder advances it to Applicable.
- one-unit: ALWAYS: a Sliced Leaf is one unit an Applier integrates on its own.
- parent-applied: ALWAYS: only the Operator closes a Parent Applied, once the Operator judges its intent met and no Child is open.
- merge-direction: ALWAYS: the Refiner merges two Changes only on the Operator's direction.
- same-passage: ALWAYS: of two open Changes that amend the same passage of a file, the one that reaches Application second names the other as a blocking Change.
- store-outside: ALWAYS: the Change Store of each Product is a fixed parameter the Operator records outside the Product Tree, and no move between Change Stores exists.
- path-repair: ALWAYS: a file that names a path a Change deletes or moves takes its own subsection when it is of a kind a subsection holds; the Applier repairs any other such file as a Mechanical Repair, or a delegate repairs it; a generated file is repaired at its declared source and regenerated; and Validate reads every surviving link.
- github-advance-read: ALWAYS: the Operator advances to Sliced only after reading the body and the Base that stand at the advance, and the holder advances to Applicable only while the body and the Base stand as the audit read them.
