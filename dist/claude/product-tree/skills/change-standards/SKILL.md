---
name: change-standards
user-invocable: false
description: >-
  Change record standards for metadata, body, Declarations, Maturity,
  Transitions, structure, the form check, and the GitHub Change Store. Loaded
  by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The complete Change record contract: the record's metadata and body, the Declarations form, the Maturity conditions, the seven Transitions and their log, the structure and lineage rules, the form check, and the home of each part of a record in a GitHub Change Store.
</objective>

<loading_contract>

Apply every rule below to any record, Change Draft, or Transition. Each rule's slug is its one name; a form-check finding, an audit finding, and a refusal name the slug of the rule it applies.

Read `${CLAUDE_SKILL_DIR}/references/github-store.md` before any read or write of a GitHub Change Store. It names the overlay that declares the store and the commands that read and write each home `<github_store>` assigns.

Run the form check as `<form_check>` states before every publish it covers.

</loading_contract>

<terms>

- **Change record**: the metadata and the body of one Change, held only in the Change Store.
- **Change Draft**: a local copy of a record's metadata, except its holder, as YAML front matter, followed by its body. A Draft is no record and has no holder.
- **Base**: the commit the `base` field names.
- **Transition**: one of the seven moves of a Change: claim, release, submit, advance, lower, applied, and abandoned.
- **Leaf** and **Parent**: a Change is a Parent when another record names it as its `parent`, and a Leaf otherwise.
- **Operator**: the person who owns the Product's judgment; only the Operator makes the moves `<maturity>` and `<transitions>` reserve to the Operator.
- **Refiner**: the holder during Refinement. **Applier**: the holder during Application.
- **Mechanical repair**: a fix of a finding that changes no behavior or decision: a path or link, a typo, a wording the finding states, or a renamed identifier, never Decision Record text.

</terms>

<record_keys>

`record-keys`: the metadata of a record holds exactly these twelve keys, each with the value stated beside it, and each key changes only through the operations stated beside it. A key with no value holds `null`, and a list with no entry holds `[]`.

| Key             | Value                                                                                                             | Changes through                                                                                                                                                                       |
| --------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`         | the intended Output, in at most 15 words                                                                          | recording or a publish                                                                                                                                                                |
| `product`       | one Product                                                                                                       | recording or a publish                                                                                                                                                                |
| `maturity`      | `Proposed`, `Framed`, `Sliced`, or `Applicable`                                                                   | recording, an advance, or a lower                                                                                                                                                     |
| `lifecycle`     | `Available`, `Submitted`, `Applied`, or `Abandoned`                                                               | recording, which sets `Submitted` for a Change with no Parent and `Available` for a Child, or a Transition                                                                            |
| `holder`        | the one person or agent that holds the Change, or `null`; absent from a Change Draft                              | recording, which sets the recorder, a claim, or a release                                                                                                                             |
| `parent`        | the Change reference of the Parent, or `null`                                                                     | recording or a split                                                                                                                                                                  |
| `predecessors`  | the Changes this Change absorbed by a merge, `[]` when it absorbed none                                           | a merge                                                                                                                                                                               |
| `blockers`      | the Changes this Change waits for, `[]` when it waits for none                                                    | a publish                                                                                                                                                                             |
| `base`          | for a Leaf, the head of the default branch at its latest publish that writes the body; a Parent holds no base key | recording a Leaf, a publish that writes its body, or its removal when a Child makes the record a Parent                                                                               |
| `priority`      | the Priority the Operator sets, `null` until the Priority decision; for a Child, the Priority of its Parent       | the Priority decision, which the Operator makes on a Submitted Proposed Change with no Parent, or a later change by the Operator; for a Child, a change to the Priority of its Parent |
| `primary_value` | `Offering`, `Quality`, `Capability`, or `Safety`, `null` until the Priority decision                              | the Priority decision                                                                                                                                                                 |
| `investment`    | `Harvest`, `Shield`, `Frontier`, or `Seed`, `null` until the Priority decision                                    | the Priority decision                                                                                                                                                                 |

A Change reference is the canonical `owner/repo#N` form. A Draft lists the keys in the order of this table, `holder` left out.

- `draft-lifecycle`: a Draft of a Change not yet recorded holds the Lifecycle that recording gives it.
- `draft-base`: the `base` of a Draft of a Leaf names the head of the default branch against which the Refiner wrote its Declarations.
- `base-on-body`: `base` moves only on a publish that writes the record's body; a publish that writes only metadata, such as a claim, a submission, or a blocker, keeps it.

</record_keys>

<record_body>

`record-body`: a record's body holds exactly these sections, in this order, each a level-two heading:

| Record   | Sections                                                                                                |
| -------- | ------------------------------------------------------------------------------------------------------- |
| a Leaf   | `## Statement of Intent`, then `## Declarations`; a Proposed Leaf may hold only its Statement of Intent |
| a Parent | `## Statement of Intent`                                                                                |

`statement-of-intent`: the Statement of Intent states these three parts, in this order, as one list item each, in at most 120 words:

| Part         | States                                                                                                                                                                                                                                  |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Output       | the Output the Change achieves                                                                                                                                                                                                          |
| Why          | the truth the work brings a lower layer up to, what the Operator settled by judgment, the question a prototype answers, or the Output and the condition it moves, with the observed state that gave rise to the Change where one exists |
| Verification | the verification that shows the Output achieved, by its type, and what it finds                                                                                                                                                         |

Each part opens with its name and a colon, such as `- Output: …`.

- `outcome-why`: the Why of a Change that creates an Outcome record, or opens an Experiment on one, states the Output the record belongs to and the condition the record declares.
- `sets-apart`: each part of the body holds only what sets this Change apart; a Child links settled rationale, and a Parent copies none of its Children's content.
- `no-person`: a record or a Handoff names no accountable person and holds no conversation text.
- `first-intent`: the Statement of Intent as first written stays readable in the Change Store's edit history while the Refiner edits the current content.
- `one-home`: no metadata field stands in the body, and the Change Store holds no field in two places.

</record_body>

<declarations>

The Declarations section holds one subsection per artifact, each a level-three heading, in the order the Applier applies them.

`subsection-coverage`: the Refiner writes one subsection for each Node the Change touches, each Decision Record the Change writes, and each contract file, Outcome record, or Product spec the Change adds or edits. `none-leaf`: a Leaf that declares nothing holds `none` and its reason under `## Declarations`.

`subsection-headings`: the Refiner heads each subsection by what it changes:

| Subsection for                                                                                                   | Heading                                                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| an existing Node, Decision Record, or file, a moved one included                                                 | its path from `spx/` at the Base                                                                                                                                          |
| a new Node or Decision Record                                                                                    | its path from `spx/`, with `NN` in place of its Index, and a `Depends on:` line below the heading; for a Decision Record, a `Precedes:` line below the `Depends on:` line |
| a contract file, Outcome record, Product spec, or file of a Product with no Product Tree that the Change creates | its path from `spx/`, or from the repository root for a Product with no Product Tree                                                                                      |
| an existing file of a Product with no Product Tree                                                               | the path of the file from the repository root at the Base                                                                                                                 |
| a file inside a moved Node, other than its spec                                                                  | its path after the move, in a subsection after the one that moves the Node                                                                                                |

- `depends-on-form`: the line below the heading of a new Node or Decision Record reads `Depends on:` and the path of each sibling the artifact depends on, each path in a code span and a comma between two paths, or `none` in their place.
- `precedes-form`: the subsection of a new Decision Record holds, below its `Depends on:` line, a line that reads `Precedes:` and the path of each sibling the Decision Record must precede, each path in a code span and a comma between two paths, or `none` in their place.
- `depends-on-prerequisites`: the Refiner names a sibling in a `Depends on:` line only when the new artifact becomes invalid, unverifiable, or incoherent without that sibling, never only because it precedes the artifact, resolves every prerequisite before it writes the line, and never writes `none` for a dependency left unresolved.
- `precedes-siblings`: the Refiner names in a `Precedes:` line each sibling in the scope of the new Decision Record, since a Decision Record governs the higher-Index siblings in its scope.
- `new-path-reference`: the Refiner names a new Node or Decision Record by the same path in every later subsection, `NN` included.
- `no-index`: a record names no Index for a new Node or Decision Record.
- `new-sibling-names`: two new siblings in one Change never share a slug and a kind.

`payloads`: below its heading and any `Depends on:` and `Precedes:` lines, a subsection holds one payload of one of these kinds:

| Payload      | Form                                                                                            | Holds                                                   |
| ------------ | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| line edits   | an optional `yaml` front-matter block, then one block fenced as `diff`                          | the lines the Change adds, removes, or keeps as context |
| replacement  | one block fenced with the file's own language, and `text` for a file whose own language is diff | the whole file after the Change, front matter included  |
| move-rewrite | a `diff` block of only the two rename headers, then a replacement                               | the move, and the whole file at its new path            |

- `one-payload`: a subsection never holds both payloads, except a move that rewrites its file.
- `fence`: a replacement's outer fence is longer than any fence inside the file, and a block with no language fails the form check.
- `front-matter-block`: line edits that set a Node's front-matter field hold the field and its value after the Change in a `yaml` block before the diff; a replacement holds the whole front matter instead; a replaced spec keeps its Node's `id`, and a moved Node keeps its `id`.

`headers`: a `diff` block can open with one git extended header, before any `-` or `+` line, and the header declares its operation:

| Header                                                          | Operation                                                                                                                                                |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `deleted file`                                                  | deletes the file the heading names; under a Node's directory heading, prunes the Node and its branch under the pruning check; nothing follows the header |
| `new file`                                                      | creates the file the heading names; every line after it is a `+` line                                                                                    |
| `rename from` the heading's path, then `rename to` the new path | moves the file or the Node directory; `-` and `+` lines can follow, and under a moved Node's heading they edit its spec                                  |

- `no-mode`: no header carries a file mode, and no other git header stands in a record; a replacement or a move keeps the file's mode.
- `operation-kinds`: `new file` creates only a contract file, an Outcome record, the Product spec, or a file of a Product with no Product Tree; a deletion or a move acts on a Node or on a Decision Record, a spec, a contract file, an Outcome record, the Product spec, or a file of a Product with no Product Tree; a replacement acts on a file of these kinds; every file an operation names is a regular text file.
- `spec-deletion`: a Change never deletes a spec apart from its Node, and never deletes the Product spec.
- `one-subsection-per-file`: two subsections never write, move, or delete the same file, except a file inside a moved Node other than its spec, which takes its edits in its own subsection whose reads at the Base resolve through the move, a slug rename included.
- `slug-rename`: a move that changes a Node's slug also renames its spec and its Outcome record to the new slug.
- `move-reads`: under a move, a `-` line and each context line read the old path at the Base, and a `+` line holds the row as the new path holds it after the Change.
- `path-naming`: the form check names each file at the Base that names, in a link or in any other text, the path of a file or Node the Change deletes or moves, or of a file inside such a Node, and skips every Knowledge root and every file the Product declares as dated history.
- `path-repair`: a file that names such a path takes its own subsection when it is of a kind a subsection holds; the Applier repairs any other such file as a mechanical repair, or a delegate repairs it; a generated file is repaired at its declared source and regenerated; Validate reads every surviving link.
- `format-at-close`: the Product's format command at the Base leaves a replacement unchanged; at close the command at the merge commit leaves the approved result, the approved replacement with its plain slugs linked, unchanged, and the file on the default branch reads the same as that result; after any difference the Change stays open and the Refiner rewrites the replacement under the merge-commit formatter.

`diff-lines`: each line of a `diff` block takes one of these forms:

| Line               | Holds                                                                                                                     |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| `+`                | a row as its spec or Decision Record holds it after the Change, with every line of a Scenario and every row of a table    |
| `-`                | a row as the Base holds it, with every line of a Scenario and every row of a table                                        |
| unmarked           | a heading the Change keeps; for a table row, the heading of its Mapping or Evaluate subsection and the table's header row |
| `+` heading        | a heading the Change adds                                                                                                 |
| `-` heading        | a heading the Change removes; a renamed heading is a `-` and `+` pair                                                     |
| `+` in a file      | a line of a contract file, Outcome record, or Product spec after the Change                                               |
| `-` in a file      | a line of such a file as the Base holds it                                                                                |
| unmarked in a file | a line of such a file around an edit, as the Base holds it                                                                |
| `+` with no tree   | a statement of a Product with no Product Tree, by its slug                                                                |
| `-` with no tree   | a statement, a section, or a Glossary entry of a Product with no Product Tree, as the Base holds it                       |

- `body-lines-only`: below its headers, the `diff` block of a Node or Decision Record holds only lines of its body, each naming its target by slug, each line of an opening by its keyword, and a `DEFINES` line by its keyword and its term; the `diff` block of a contract file, Outcome record, or Product spec holds literal lines of the file.
- `no-tag`: a Declarations line adds no tag.
- `plain-slug`: a slug whose test file, eval rule, or probe protocol is absent at the Base stands plain in its `+` line; the Applier links it once a round writes that artifact.
- `table-case`: the slug of the Mapping or Evaluate subsection of a table row, a slash, and the case slug name the row, such as `date-phrases/tomorrow-5pm`, and the first cell of the row holds the case slug alone.

Infrastructure lines:

- `infrastructure-line`: a Node subsection ends with one infrastructure line for each Assertion it adds or replaces at `verification` or `implementation` Malleability after the Change, and a subsection that hardens its Node holds one for every Assertion the Node holds after the Change.
- `replaced-assertion`: an Assertion counts as added or replaced when its complete declaration differs from the Base: its row and the group heading that fixes its verification type, or the whole subsection for a Mapping or Evaluate Assertion.
- `infrastructure-form`: the line reads `Infrastructure:`, the Assertion's slug, and the path of each Node whose test infrastructure the Assertion's Evidence needs, each path in a code span and a comma between two paths, or `none` in their place.
- `infrastructure-exists`: when the Refiner writes the line, each Node it names exists at the Base, or a blocking Change builds it.
- `spec-node-none`: an Assertion of a `spec`-malleable Node carries no infrastructure line.

</declarations>

<maturity>

`maturity-ready`: the Operator and the holder advance a Leaf to a Maturity only once the condition of that Maturity and of every lower Maturity holds for the Leaf:

| Maturity   | Condition                                                                                                                                                       |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Proposed   | its Statement of Intent states Output, Why, and Verification                                                                                                    |
| Framed     | at the advance, the Operator judges every Declarations line settled                                                                                             |
| Sliced     | at most five Node subsections, counting each one that deletes, moves, or creates, and an Applier can integrate the Leaf on its own                              |
| Applicable | each Node its infrastructure lines name is on the default branch with State Passing, or the Change that builds it blocks the Leaf; an Auditor passed the record |

- `maturity-actor`: the recorder records a Leaf at Proposed; the Operator advances it to Framed on judging every Declarations line settled, and to Sliced after reviewing every decision line and every removal, deletion, move, and replacement on a Decision Record or on a Node whose Malleability is not `spec`, and each file in such a Node; its holder advances it to Applicable.
- `combined-advance`: a Leaf ready for Framed within the five-Node bound is ready for Sliced too, and the Operator can advance it to Framed and to Sliced in one move.
- `one-unit`: a Sliced Leaf is one unit an Applier integrates on its own.
- `parent-maturity`: only the Operator's advances on a Parent's Statement of Intent set its Maturity, its Children set nothing, and a Parent never reaches Applicable.
- `review-binding`: the Operator's review binds the record body and the Base it read; the advance to Sliced records both, and the advance and the Application check confirm that the current record is that one or one the review carries forward to.
- `review-part`: a part is a row by its slug, a heading, or any other single line, with every heading above it, the header row of its table, and the line that opens its Scenario or list as its context; for a deletion or a move of a file the part is the file, and for a deletion or a move of a Node it is the Nodes its branch holds, with every spec, Decision Record, contract file, and Outcome record in them.
- `review-carry`: after a later publish, the review of a part carries forward only while the operation keeps its kind and its paths, the Decision Records that govern the part stay the same, and the part and each line of its context read the same in the old and the new revision, at each Base and after the Change; a Base that no longer resolves carries no review forward.
- `audit-before-applicable`: an Auditor audits a Sliced Leaf before its holder advances it to Applicable, each Declarations line against every Decision Record that governs its Node at the Base, read as the Declarations change it, and every finding blocks.
- `audit-binding`: the audit binds the body and the Base it judged; the advance to Applicable records both; a publish that writes the body of an Applicable record returns the Change to Sliced and takes the form check before the audit runs again; a publish that writes only metadata keeps the audit.
- `audit-at-close`: before a Leaf closes Applied, an Auditor audits the default branch against its record: each Assertion and decision stands as its line states, and the verification the Statement of Intent names finds what it states.
- `operator-answers`: every answer the Operator gives in Refinement reaches a Declarations line, with each condition, exception, boundary, and expected outcome.
- `facts-checked`: the Refiner checks every fact the record cites against the latest checkout of the owning repository, or, for a Product with no Product Tree, against the cited source by path and commit.
- `index-assignment`: the Applier assigns the Index of a new Node or Decision Record from the siblings its `Depends on:` line and, for a Decision Record, its `Precedes:` line name. Before it selects an Index, the Applier resolves every prerequisite, and for a new Node it first resolves an inversion of the kind order or a misclassification. For each sibling the `Depends on:` line names, the Applier states what becomes invalid, unverifiable, or incoherent without that sibling, and the evidence basis of the prerequisite: provider/consumer, logical prerequisite, vertical slice, shared substrate, feature extension, or decision constraint. The Applier places the artifact above each sibling the `Depends on:` line names and below each sibling the `Precedes:` line names, takes an existing peer Index when that Index satisfies the prerequisites and the scope of every governing Decision Record, and never takes the next free number as a default.

</maturity>

<transitions>

`transitions`: each Transition takes a Change in the state its row requires and changes what its row states:

| Transition | Requires                                                                                                                             | Changes                                                    |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| claim      | an Available Change with no holder                                                                                                   | sets the holder                                            |
| release    | a held Change                                                                                                                        | clears the holder; a Submitted Change returns to Available |
| submit     | an Available Change that waits for the Operator's next move, or whose settled judgment the holder finds reopened, with its reason    | Available to Submitted                                     |
| advance    | a Submitted Change that meets the condition of each Maturity up to the new one, or a Sliced Leaf that meets the Applicable condition | raises the Maturity                                        |
| lower      | a Framed, Sliced, or Applicable Change, with a reason                                                                                | lowers the Maturity                                        |
| applied    | the close condition of the Change's type                                                                                             | to Applied                                                 |
| abandoned  | an open Change                                                                                                                       | to Abandoned                                               |

`transition-actor`: any person or agent claims. The holder releases, submits, advances a Sliced Leaf to Applicable, and closes a Leaf Applied. Only the Operator advances to Framed or Sliced, lowers when a settled judgment reopens, closes a Change Abandoned other than the Change a merge absorbs, and closes a Parent Applied. On the direction of the Operator, the Refiner closes the Change a merge absorbs Abandoned. The Applier lowers its Applicable Change to Sliced to write a decision line that differs from the reviewed line. The Applier returns the Change to Sliced when the Application check fails. Any person or agent that writes the body of an Applicable record in a publish returns the Change to Sliced. A reframe by the Refiner lowers the Change to Proposed.

- `claim-kept`: a holder keeps its Claim when its session restarts. The holder of a Submitted Change keeps the Claim also when its session ends. When a holder releases a Submitted Change, the pending move of the Operator lapses, and the next holder submits the Change again.
- `lower-claim`: an Applier that lowers its Applicable record to Sliced to write a decision line keeps its Claim; after every other lowering the holder writes a Handoff and releases the Change.
- `reframe`: a reframe edits a Change in place and lowers its Maturity to Proposed.
- `terminal`: no Transition moves an Applied or Abandoned Change.
- `leaf-applied`: a Leaf closes Applied only when the merge commit of the Changeset its holder closes it on is an ancestor of the default branch, every merge gate passed, each Node holds every result its Malleability requires, every Declarations line stands on the default branch, and the audit at close found nothing.
- `parent-applied`: only the Operator closes a Parent Applied, once the Operator judges its intent met and no Child is open.

Transition log:

- `log-block`: every Transition posts one comment holding one fenced YAML block and nothing else, and the comment's time is the Transition's time.
- `log-keys`: the block holds `transition`, the move; `maturity`, the Change's Maturity at the move as the Change Store spells it; `harness`, the token the Provider assigns to the agent harness; `session`, the harness's session id; `machine`, the user and the short host name as `user@host`; and `worktree`, the absolute path of the worktree the session works in.
- `log-position`: the block can also hold `position`, the Position the holder holds, as its one optional key.
- `log-extras`: a lower adds `reason`; a release adds `handoff` with at least the branch, the head commit, and the next subsection; an applied Transition of a Leaf adds `changeset` with its merge commit.
- `log-closed`: the block holds no other key and no prose outside `reason`.
- `log-no-authority`: nobody reads authority from a Transition comment, and no delegate, no party on whose behalf the holder acts, and no words of the Operator appear in it.

A Handoff is the latest continuation a holder persists: the active branch or Changeset, its head commit, the completed Declarations subsections, the next subsection, blockers, and hazards, each subsection by its path. It holds only what the next holder cannot derive quickly from the Change, the Product Tree, the repository, and the Changeset history.

</transitions>

<structure>

- `change-type`: a Change is a Parent when another record names it as its parent, and a Leaf otherwise; the type derives from those relations and is never stored.
- `one-product`: every Change names one Product. A Parent names none of its Children and none of their Products.
- `split`: the Refiner splits a Leaf into Children only below Applicable, and records a Child under a Parent at any Maturity of either.
- `merge`: a merge closes the absorbed Change Abandoned and adds it to the survivor's `predecessors`.
- `merge-direction`: the Refiner merges two Changes only on the Operator's direction.
- `blocker-applied`: a blocking Change satisfies the blocker when it closes Applied.
- `blocker-abandoned`: a blocking Change that closes Abandoned through a merge passes its block to the Change that names it as predecessor, and one that closes Abandoned without a merge returns the dependent Change to Refinement.
- `blocker-cycle`: no member of a blocker cycle remains Sliced or Applicable until the Refiner removes the cycle.
- `same-passage`: of two open Changes that amend the same passage of a file, the one that reaches Application second names the other as a blocking Change.
- `store-outside`: the Change Store of each Product is a fixed parameter the Operator records outside the Product Tree, and no move between Change Stores exists.
- `terminal-kept`: a Change in a terminal Lifecycle and its edit history stay queryable until the owning Product's Change-retention policy permits their removal.

</structure>

<form_check>

`form-check`: below Applicable, and on a publish that writes the body of an Applicable record, a program checks the form of a record before the publish, and nothing publishes while the check fails. The program is `${CLAUDE_SKILL_DIR}/scripts/form_check.py`; it reads a Draft and the checkout and writes nothing:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/form_check.py" --root <checkout-root> --draft <draft-path>
```

On a publish that replaces a record the Change Store holds, add `--issue <owner/repo#N> --read-edited-at <timestamp>`, the timestamp being the `lastEditedAt` the publisher read with the record, or the `createdAt` of a record never edited; on the publish of a Sliced record, add `--published <path>`, a file holding the Draft composed from the stored record. The check prints one JSON object on stdout. A judged Draft yields `status` (`pass` or `fail`), `findings` (one `{rule, location, detail}` entry per breach), and `informational` (one `{file, names}` entry per file at the Base that names a deleted or moved path and takes a mechanical repair under `path-repair`, and one `{nodeSubsections, bound}` entry when the Node subsections exceed the five-Node bound), and exits 0 on `pass` and 1 on `fail`. An unusable invocation yields `status` `unusable` and `detail`, which names the argument or the read that failed, and exits 2.

It fails a Draft for each breach of the rules `record-keys`, `record-body`, `statement-of-intent`, `subsection-headings`, `payloads`, `headers`, `diff-lines`, `body-lines-only`, `no-tag`, `plain-slug`, `table-case`, `front-matter-block`, `no-index`, `depends-on-form`, `precedes-form`, `new-path-reference`, `move-reads`, `one-payload`, `fence`, `no-mode`, `operation-kinds`, `spec-deletion`, `one-subsection-per-file`, `new-sibling-names`, `slug-rename`, `path-naming`, `infrastructure-line`, `replaced-assertion`, `infrastructure-form`, `infrastructure-exists`, `spec-node-none`, `none-leaf`, `one-product`, `draft-lifecycle`, `draft-base`, `size-limit`, `stale-revision`, `operator-bound-base`, and `one-home`, and names the slug of the rule each finding breaks.

- `stale-revision`: the form check fails a publish when the revision the Change Store holds changed since the publisher read it.
- `detect-restore`: where the Change Store accepts no expected revision, the publisher reads the record's edit history after the write, restores a revision it did not write that landed between its own read and its own write, and counts the publish as failed; a revision that landed after its own write stands, and that publish counts as failed too.
- `size-limit`: the form check fails a publish whose record exceeds the Change Store's size limit, and names the limit.
- `operator-bound-base`: the form check fails the publish of a Sliced record whose new `base` changes a file the record deletes, moves, or replaces, where the Operator's review binds that operation, and a former Base that no longer resolves counts as such a change; every other such publish succeeds, and the audit reads the operation at the new Base.

</form_check>

<testing>

`scripts/form_check.py` was run with these inputs, each output matching the expected one; no run writes a file, so none leaves anything to clean up:

| Input                                                                                                                                                                                                                                                                                                                                                                | Expected output                                                                                                                                                                                                                                                                       | Observed    |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| a stored Leaf's Draft, six Declarations subsections that read at its Base, against its checkout                                                                                                                                                                                                                                                                      | `pass`, no finding, exit 0                                                                                                                                                                                                                                                            | as expected |
| a Draft with a list `product`, Maturity `Executable`, Lifecycle `Claimed`, Value `Product`, a metadata line in the body, a two-part Statement of Intent, an indexed absent Node, a tagged `+` row without a slug, a new Node without `Depends on:`, a block with no language, a `index` header, a `-` line the Base lacks, and an infrastructure line on a spec Node | `fail`, exit 1, with findings `one-product`, `record-keys`, `draft-lifecycle`, `one-home`, `statement-of-intent`, `no-index`, `no-tag`, `body-lines-only`, `depends-on-form`, `fence`, `front-matter-block`, `no-mode`, `one-subsection-per-file`, `diff-lines`, and `spec-node-none` | as expected |
| that Draft with `--issue` naming its stored record and a read stamp older than the stored edit                                                                                                                                                                                                                                                                       | `fail`, exit 1, one `stale-revision` finding naming both stamps                                                                                                                                                                                                                       | as expected |
| `--root` a relative path                                                                                                                                                                                                                                                                                                                                             | `unusable`, exit 2, naming `--root`                                                                                                                                                                                                                                                   | as expected |
| `--draft` a missing file                                                                                                                                                                                                                                                                                                                                             | `unusable`, exit 2, naming `--draft` and the read error                                                                                                                                                                                                                               | as expected |
| `--issue` without `--read-edited-at`                                                                                                                                                                                                                                                                                                                                 | `unusable`, exit 2, naming the two arguments                                                                                                                                                                                                                                          | as expected |

</testing>

<github_store>

`github-store`: where the Change Store is a GitHub repository, each part of a record has this one home:

| Part            | Home                                                                                     |
| --------------- | ---------------------------------------------------------------------------------------- |
| `title`         | the issue title                                                                          |
| body            | the issue body                                                                           |
| `product`       | the organization issue field Product                                                     |
| `maturity`      | the organization issue field Maturity                                                    |
| `lifecycle`     | the organization issue field Lifecycle                                                   |
| `holder`        | the issue's one assignee, with the session and worktree its newest claim comment records |
| `parent`        | the organization number issue field Parent                                               |
| `predecessors`  | the organization text issue field Predecessors                                           |
| `blockers`      | the issue's native dependencies                                                          |
| `base`          | the organization text issue field Base                                                   |
| `priority`      | the organization issue field Priority                                                    |
| `primary_value` | the organization issue field Value                                                       |
| `investment`    | the organization issue field Investment                                                  |
| a Transition    | one issue comment                                                                        |

- `github-binding`: an advance to Sliced or to Applicable binds the body revision the issue's edit history holds at the time of the advance's comment and the Base value the Base field's change events hold at that time; the binding is confirmed only while the current body equals that revision and the current Base equals that value, or the Operator's review carries forward to them.
- `github-later-edit`: a body edit after an advance keeps the review of each part that `review-carry` carries forward, and takes a new audit.
- `github-race`: GitHub's issue update takes no expected revision, so the publisher records the body's last edit at its read and fails the publish when the last edit right before its write differs; after its write it reads the edit history, restores a revision another writer wrote between its read and its write, where GitHub still holds it, and fails the publish; a revision written after its write stands, and that publish fails too.
- `github-one-holder`: a Change issue carries at most one assignee.
- `github-parent`: a Child lives in its Parent's Change Store, so the Parent number names the Parent's issue in that store.
- `github-limit`: the size limit of a GitHub Change Store is 65,536 characters of issue body.
- `store-options`: the Maturity, Lifecycle, Value, and Investment fields receive only the values `record-keys` names for `maturity`, `lifecycle`, `primary_value`, and `investment`; a field whose options differ from those values stops every write to it with a blocked result naming the field.

</github_store>

<success_criteria>

- Each rule appears once, under its slug, and every form-check finding, audit finding, and refusal names the slug it applies.
- The twelve keys, the two body sections, the four Maturities, the four Lifecycles, the seven Transitions, and the Leaf and Parent types stay distinct, and no rule reads authority from a body line or a Transition comment.
- The form check covers every rule `<form_check>` lists and writes nothing.
- Every part of a record has exactly one home in a GitHub Change Store.

</success_criteria>
