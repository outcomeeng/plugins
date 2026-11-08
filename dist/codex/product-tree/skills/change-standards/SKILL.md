---
name: change-standards
user-invocable: false
description: >-
  Change record standards — the record's metadata and body, the Change Draft,
  and the form check that judges a Draft. Loaded by other skills, not invoked
  directly.
allowed-tools: Read
---

<objective>
The Change record, the Change Draft, and the form check's request and result, stated as the Change record decision states them.
</objective>

<terms>

- **Change record**: the metadata and the body of one Change, held only in the Change Store.
- **Change Draft**: a local copy of a Change record's metadata, except its holder, as YAML front matter, followed by its body.
- **Base**: the commit a Change record's base field names.
- **Transition**: one of the seven moves of a Change: claim, release, submit, advance, lower, applied, and abandoned.

</terms>

<record_keys>

A record's metadata holds exactly these keys, each with this value, and each changes only through the operations its row names. A key with no value holds null, and a list with no entry holds [].

| Key           | Value                                                                                                             | Changes through                                                                                         |
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

Where the Change Store is a GitHub repository, each part of a record has one home: title in the issue title, body in the issue body, product, maturity, lifecycle, priority, and investment in the organization issue fields of those names, primary_value in the field Value, holder in the issue's one assignee, parent in the number field Parent, predecessors and base in the text fields of those names, blockers in the issue's native dependencies, and each Transition in one issue comment.

</record_keys>

<record_body>

A record's body holds exactly these sections, in this order.

| Record   | Sections                                                                                      |
| -------- | --------------------------------------------------------------------------------------------- |
| a Leaf   | Statement of Intent, then Declarations; a Proposed Leaf may hold only its Statement of Intent |
| a Parent | Statement of Intent                                                                           |

A Change is a Parent when another record names it as its parent, and a Leaf otherwise.

The Statement of Intent states these three parts, in this order, in at most 120 words.

| Part         | States                                                                                                                                                                                                                                  |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Output       | the Output the Change achieves                                                                                                                                                                                                          |
| Why          | the truth the work brings a lower layer up to, what the Operator settled by judgment, the question a prototype answers, or the Output and the condition it moves, with the observed state that gave rise to the Change where one exists |
| Verification | the verification that shows the Output achieved, by its type, and what it finds                                                                                                                                                         |

Each part opens a list item that starts with its label: `- Output:`, `- Why:`, and `- Verification:`.
</record_body>

<declarations>

Each Declarations subsection stands in Application order under the heading its row names.

| Subsection for                                                                                                   | Heading                                                                                |
| ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| an existing Node, Decision Record, or file, a moved one included                                                 | its path from spx/ at the Base                                                         |
| a new Node or Decision Record                                                                                    | its kind, its slug, and the two existing siblings between which the Applier inserts it |
| a contract file, Outcome record, Product spec, or file of a Product with no Product Tree that the Change creates | its path from spx/, or from the repository root for a Product with no Product Tree     |
| an existing file of a Product with no Product Tree                                                               | the file's path from the repository root at the Base                                   |
| a file inside a moved Node, other than its spec                                                                  | its path after the move, after the Node's move subsection                              |

The heading of a new Node or Decision Record reads `` new <kind> `<slug>`, between `<sibling>` and `<sibling>` ``.

Below its heading, a subsection holds the one payload its row names.

| Payload      | Holds                                                                                                                                                         |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| line edits   | an optional yaml front-matter block, then one block fenced as diff, holding the lines the Change adds, removes, or keeps as context                           |
| replacement  | one block fenced with the file's own language, and text for a file whose own language is diff, holding the whole file after the Change, front matter included |
| move-rewrite | a diff block of only the two rename headers, then a replacement holding the move and the whole file at its new path                                           |

A diff block can open with the git extended header its row names, before any - or + line, and the header declares the row's operation.

| Header                                                      | Operation                                                                                                                                                |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| deleted file                                                | deletes the file the heading names; under a Node's directory heading, prunes the Node and its branch under the pruning check; nothing follows the header |
| new file                                                    | creates the file the heading names; every line after it is a + line                                                                                      |
| rename from the heading's path, then rename to the new path | moves the file or the Node directory; - and + lines can follow, and under a moved Node's heading they edit its spec                                      |

Each line of a diff block takes the form its row names and holds what that row states.

| Line                    | Holds                                                                                                                     |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| +                       | a row as its spec or Decision Record holds it after the Change, with every line of a Scenario and every row of a table    |
| -                       | a row as the Base holds it, with every line of a Scenario and every row of a table                                        |
| unmarked                | a heading the Change keeps; for a table row, the heading of its Mapping or Evaluate subsection and the table's header row |
| + heading               | a heading the Change adds                                                                                                 |
| - heading               | a heading the Change removes; a renamed heading is a - and + pair                                                         |
| + line of a file        | a line of a contract file, Outcome record, or Product spec after the Change                                               |
| - line of a file        | a line of such a file as the Base holds it                                                                                |
| unmarked line of a file | a line of such a file around an edit, as the Base holds it                                                                |
| + line, no Product Tree | a statement of a Product with no Product Tree, by its slug                                                                |
| - line, no Product Tree | a statement, a section, or a Glossary entry of a Product with no Product Tree, as the Base holds it                       |

</declarations>

<declaration_rules>

Declaration lines:

- body-lines-only: ALWAYS: below its headers, the diff block of a Node or Decision Record holds only lines of its body, each naming its target by slug, each line of an opening by its keyword, and a DEFINES line by its keyword and its term; the diff block of a contract file, Outcome record, or Product spec holds literal lines of the file.
- no-tag: NEVER: a Declarations line adds a tag.
- plain-slug: ALWAYS: a slug whose test file, eval rule, or probe protocol is absent at the Base stands plain in its + line.
- table-case: ALWAYS: a table row's case reads as its subsection's slug, a slash, and the case slug, such as date-phrases/tomorrow-5pm.
- front-matter-block: ALWAYS: line edits that set a Node's front-matter field hold the field and its value after the Change in a yaml block before the diff, a replacement holds the whole front matter instead, a replaced spec keeps its Node's id, and a moved Node keeps its id.
- no-index: NEVER: a record names an Index for a new Node or Decision Record.
- move-reads: ALWAYS: under a move, a - line and each context line read the old path at the Base, and a + line holds the row as the new path holds it after the Change.

Declaration operations:

- one-payload: NEVER: a subsection holds both payloads, except a move that rewrites its file.
- fence: ALWAYS: a replacement's outer fence is longer than any fence inside the file, and a block with no language fails the form check.
- no-mode: NEVER: a header carries a file mode, or another git header stands in a record; a replacement or a move keeps the file's mode, which nothing checks.
- operation-kinds: ALWAYS: new file creates only a contract file, an Outcome record, the Product spec, or a file of a Product with no Product Tree; a deletion or a move acts on a Node or on a Decision Record, a spec, a contract file, an Outcome record, the Product spec, or a file of a Product with no Product Tree; a replacement acts on a file of these kinds; and every file an operation names is a regular text file.
- spec-deletion: NEVER: a Change deletes a spec apart from its Node, or deletes the Product spec.
- one-subsection-per-file: NEVER: two subsections of a Change write, move, or delete the same file, except a file inside a moved Node other than its spec, which takes its edits in its own subsection whose reads at the Base resolve through the move, a slug rename included.
- slug-rename: ALWAYS: a move that changes a Node's slug also renames its spec and its Outcome record to the new slug.
- path-naming: ALWAYS: the form check names each file at the Base that names, in a link or in any other text, the path of a file or Node the Change deletes or moves, or of a file inside such a Node, and skips every Knowledge root and every file the Product declares as dated history.

Infrastructure lines:

- infrastructure-line: ALWAYS: a Node subsection ends with one infrastructure line for each Assertion it adds or replaces at verification or implementation Malleability after the Change, and a subsection that hardens its Node holds one for every Assertion the Node holds after the Change.
- replaced-assertion: ALWAYS: an Assertion counts as added or replaced when its complete declaration differs from the Base, its complete declaration being its row and the group heading that fixes its verification type, or the whole subsection for a Mapping or Evaluate Assertion.
- infrastructure-form: ALWAYS: the line reads `Infrastructure:`, the Assertion's slug, and the path of each Node whose test infrastructure that Assertion's Evidence needs, each path in a code span and a comma between two paths, or `none` in their place.
- infrastructure-exists: ALWAYS: when the Refiner writes the line, each Node it names exists at the Base, or a blocking Change builds it.
- spec-node-none: NEVER: an Assertion of a spec-malleable Node carries an infrastructure line.
- none-leaf: ALWAYS: a Leaf that declares nothing holds none and its reason.

</declaration_rules>

<form_check>

The form check is one standard-library script, `${SKILL_DIR}/scripts/form_check.py`, that judges a Change Draft against the record this skill states. Its module exposes one function, `check`, that returns for a request the result the script writes for it, so a sibling Change skill's script reaches the check through a `__file__`-relative import of that module.

- form-check: ALWAYS: below Applicable, and on a publish that writes the body of an Applicable record, a program checks the form of a record before the publish, and nothing publishes while the check fails.
- size-limit: ALWAYS: the form check fails a record that exceeds the Change Store's size limit, and names the limit.
- one-home: NEVER: a metadata field stands in the body, or the Change Store holds a field in two places.
- github-limit: ALWAYS: the size limit of a GitHub Change Store is 65,536 characters of issue body.
- check-reads-only: NEVER: the form check writes a file or the Change Store; it reads the Draft and runs only reading git commands at the Base in the checkout root.

The request is one JSON object on stdin with these fields:

| Field             | Value                                                                                                                                                                                                |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `draft_text`      | the Draft's text; the request names exactly one of `draft_text` and `draft_path`                                                                                                                     |
| `draft_path`      | the path of the Draft's file                                                                                                                                                                         |
| `checkout_root`   | the absolute path of the Product's checkout root                                                                                                                                                     |
| `operation`       | `record`, `publish`, `split`, `record-child`, `merge`, `priority-decision`, `audit`, which changes no key, or a Transition: `claim`, `release`, `submit`, `advance`, `lower`, `applied`, `abandoned` |
| `stored_record`   | the record the Change Store holds, as an object with `metadata` and `body`, or null                                                                                                                  |
| `blocker_records` | optional; the record of each Change the Draft names as a blocker, keyed by the blocker's reference in the Draft                                                                                      |
| `size_limit`      | the Change Store's size limit in characters, or `github`                                                                                                                                             |

The result is one JSON object on stdout. Its `status` is `pass`, `fail`, or `invalid-request`, and the script exits 0, 1, or 2 for them. Its `findings` list holds one object for each finding, with `rule`, the slug of the rule it breaks, `where`, the subsection, key, or line it names, and `detail`. A request the script cannot read yields `invalid-request`, no finding, and a `detail` that names the field.

The form check judges each key's presence, the type of its value, and the values a row lists; what a value states stays with the audit. It judges each Statement of Intent part's label, the order of the parts, and the word count, which holds each word that carries a letter or a digit, labels excluded, and each subsection heading's form; the Application order of the subsections and what each + line states stay with the audit.

</form_check>

<success_criteria>

- The skill states the Change record, the Change Draft, and the form check's request and result as the Change record decision states them, and names no rule the decision does not state.
- Each rule appears once, under the slug the decision gives it.
- A consumer reaches the form check through the `check` function of the script, or through the script's stdin and stdout, and publishes only after a result with status `pass`.

</success_criteria>
