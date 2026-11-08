---
id: 01a1b95b-64a1-704a-b1fc-7a44d7ec897e
malleability: verification
---

# Change Standards

PROVIDES the change-standards skill, which states the Change record that the Change skills share, and its form check, one standard-library script that judges a Change Draft against that record
SO THAT the Change skills that record, move, and audit a Change
CAN judge a record's form through one check before each publish

## Assertions

### Test.Mapping: record-keys

The form check passes a Draft only when its metadata holds exactly these keys, each with this value, and, given the record the Change Store holds and the operation, it fails a key whose value changes through an operation its row does not name. A key with no value holds null, and a list with no entry holds []. The form check judges each key's presence, the type of its value, and the values a row lists; what a value states stays with the audit. ([test](tests/test_form_check.mapping.l1.py))

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

The form check passes a Draft only when its body holds exactly these sections, in this order. ([test](tests/test_form_check.mapping.l1.py))

| Case   | Record   | Sections                                                                                      |
| ------ | -------- | --------------------------------------------------------------------------------------------- |
| leaf   | a Leaf   | Statement of Intent, then Declarations; a Proposed Leaf may hold only its Statement of Intent |
| parent | a Parent | Statement of Intent                                                                           |

### Test.Mapping: statement-of-intent

The form check passes a Statement of Intent only when it states these three parts, in this order, in at most 120 words. The form check judges each part's label, the order of the parts, and the word count; what each part states stays with the audit. ([test](tests/test_form_check.mapping.l1.py))

| Case         | Part         | States                                                                                                                                                                                                                                  |
| ------------ | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| output       | Output       | the Output the Change achieves                                                                                                                                                                                                          |
| why          | Why          | the truth the work brings a lower layer up to, what the Operator settled by judgment, the question a prototype answers, or the Output and the condition it moves, with the observed state that gave rise to the Change where one exists |
| verification | Verification | the verification that shows the Output achieved, by its type, and what it finds                                                                                                                                                         |

### Test.Mapping: subsection-headings

The form check passes each Declarations subsection only when it stands in Application order under the heading its row names. The form check judges each heading's form; the Application order stays with the audit. ([test](tests/test_form_check.mapping.l1.py))

| Case     | Subsection for                                                                                                   | Heading                                                                                |
| -------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| existing | an existing Node, Decision Record, or file, a moved one included                                                 | its path from spx/ at the Base                                                         |
| new      | a new Node or Decision Record                                                                                    | its kind, its slug, and the two existing siblings between which the Applier inserts it |
| created  | a contract file, Outcome record, Product spec, or file of a Product with no Product Tree that the Change creates | its path from spx/, or from the repository root for a Product with no Product Tree     |
| no-tree  | an existing file of a Product with no Product Tree                                                               | the file's path from the repository root at the Base                                   |
| in-moved | a file inside a moved Node, other than its spec                                                                  | its path after the move, after the Node's move subsection                              |

### Test.Mapping: payloads

The form check passes a subsection only when, below its heading, it holds the one payload its row names. ([test](tests/test_form_check.mapping.l1.py))

| Case         | Payload                                                                                       | Holds                                                   |
| ------------ | --------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| line-edits   | an optional yaml front-matter block, then one block fenced as diff                            | the lines the Change adds, removes, or keeps as context |
| replacement  | one block fenced with the file's own language, and text for a file whose own language is diff | the whole file after the Change, front matter included  |
| move-rewrite | a diff block of only the two rename headers, then a replacement                               | the move, and the whole file at its new path            |

### Test.Mapping: headers

The form check reads the git extended header that opens a diff block, before any - or + line, as the operation its row names. ([test](tests/test_form_check.mapping.l1.py))

| Case   | Header                                                      | Operation                                                                                                                                                |
| ------ | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| delete | deleted file                                                | deletes the file the heading names; under a Node's directory heading, prunes the Node and its branch under the pruning check; nothing follows the header |
| create | new file                                                    | creates the file the heading names; every line after it is a + line                                                                                      |
| move   | rename from the heading's path, then rename to the new path | moves the file or the Node directory; - and + lines can follow, and under a moved Node's heading they edit its spec                                      |

### Test.Mapping: diff-lines

The form check passes each line of a diff block only when it takes the form its row names and holds what that row states. The form check reads each - line and each context line against the Base, and each + line by its form; what a + line states stays with the audit. ([test](tests/test_form_check.mapping.l1.py))

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

- body-lines-only: ALWAYS: the form check fails a diff block of a Node or Decision Record that holds, below its headers, a line other than a line of its body naming its target by slug, a line of an opening named by its keyword, or a DEFINES line named by its keyword and its term, and fails a diff block of a contract file, Outcome record, or Product spec that holds a line other than a literal line of the file. ([test](tests/test_form_check.compliance.l1.py))
- no-tag: NEVER: the form check passes a Declarations line that adds a tag. ([test](tests/test_form_check.compliance.l1.py))
- plain-slug: ALWAYS: the form check fails a + line that links a slug whose test file, eval rule, or probe protocol is absent at the Base. ([test](tests/test_form_check.compliance.l1.py))
- table-case: ALWAYS: the form check names a table row by its subsection's slug, a slash, and the row's case slug, such as date-phrases/tomorrow-5pm. ([test](tests/test_form_check.compliance.l1.py))
- front-matter-block: ALWAYS: the form check fails line edits that set a Node's front-matter field outside a yaml block before the diff, a replacement that does not hold the whole front matter, a replaced spec whose id differs from its Node's id at the Base, and a moved Node whose id changes. ([test](tests/test_form_check.compliance.l1.py))
- no-index: NEVER: the form check passes a record that names an Index for a new Node or Decision Record. ([test](tests/test_form_check.compliance.l1.py))
- move-reads: ALWAYS: under a move, the form check reads a - line and each context line at the old path at the Base, and fails one the old path does not hold there. ([test](tests/test_form_check.compliance.l1.py))

### Test.Compliance: Declaration operations

- one-payload: NEVER: the form check passes a subsection that holds both payloads, except a move that rewrites its file. ([test](tests/test_form_check.compliance.l1.py))
- fence: ALWAYS: the form check fails a replacement whose outer fence is not longer than every fence inside the file, and a block with no language. ([test](tests/test_form_check.compliance.l1.py))
- no-mode: NEVER: the form check passes a header that carries a file mode, or a git header other than deleted file, new file, rename from, and rename to. ([test](tests/test_form_check.compliance.l1.py))
- operation-kinds: ALWAYS: the form check fails a new file that creates anything other than a contract file, an Outcome record, the Product spec, or a file of a Product with no Product Tree; a deletion, move, or replacement that acts on anything other than a Node or a Decision Record, a spec, a contract file, an Outcome record, the Product spec, or a file of a Product with no Product Tree; a deletion, move, or replacement of a file that is no regular text file at the Base; and a new file whose path exists at the Base. ([test](tests/test_form_check.compliance.l1.py))
- spec-deletion: NEVER: the form check passes a Change that deletes a spec apart from its Node, or deletes the Product spec. ([test](tests/test_form_check.compliance.l1.py))
- one-subsection-per-file: NEVER: the form check passes two subsections that write, move, or delete the same file, except a file inside a moved Node other than its spec, which takes its edits in its own subsection whose reads at the Base resolve through the move, a slug rename included. ([test](tests/test_form_check.compliance.l1.py))
- slug-rename: ALWAYS: the form check fails a move that changes a Node's slug without renaming its spec and its Outcome record to the new slug. ([test](tests/test_form_check.compliance.l1.py))
- path-naming: ALWAYS: the form check names each file at the Base that names, in a link or in any other text, the path of a file or Node the Change deletes or moves, or of a file inside such a Node, and skips every Knowledge root and every file the Product declares as dated history. ([test](tests/test_form_check.compliance.l1.py))

### Test.Compliance: infrastructure lines

- infrastructure-line: ALWAYS: the form check fails a Node subsection that does not end with one infrastructure line for each Assertion it adds or replaces at verification or implementation Malleability after the Change, and a subsection that hardens its Node without one for every Assertion the Node holds after the Change. ([test](tests/test_form_check.compliance.l1.py))
- replaced-assertion: ALWAYS: the form check counts an Assertion as added or replaced when its complete declaration differs from the Base, its complete declaration being its row and the group heading that fixes its verification type, or the whole subsection for a Mapping or Evaluate Assertion. ([test](tests/test_form_check.compliance.l1.py))
- infrastructure-form: ALWAYS: the form check fails an infrastructure line that does not read `Infrastructure:`, the Assertion's slug, and either the path of each Node whose test infrastructure that Assertion's Evidence needs, each path in a code span and a comma between two paths, or `none`. ([test](tests/test_form_check.compliance.l1.py))
- infrastructure-exists: ALWAYS: the form check fails an infrastructure line that names a Node absent at the Base unless the record of a Change the Draft names as a blocker holds a Declarations subsection that creates that Node; a blocker whose record creates no such Node satisfies nothing. ([test](tests/test_form_check.compliance.l1.py))
- spec-node-none: NEVER: the form check passes an infrastructure line on an Assertion of a spec-malleable Node. ([test](tests/test_form_check.compliance.l1.py))
- none-leaf: ALWAYS: the form check fails a Leaf whose Declarations hold no subsection unless they hold none and its reason. ([test](tests/test_form_check.compliance.l1.py))

### Test.Compliance: record size and homes

- size-limit: ALWAYS: the form check fails a record that exceeds the Change Store's size limit, and names the limit. ([test](tests/test_form_check.compliance.l1.py))
- one-home: NEVER: the form check passes a body that holds a metadata field. ([test](tests/test_form_check.compliance.l1.py))
- github-limit: ALWAYS: the form check takes 65,536 characters of issue body as the size limit of a GitHub Change Store. ([test](tests/test_form_check.compliance.l1.py))

### Test.Compliance: form check interface

- check-request: ALWAYS: the form check reads one JSON request on stdin carrying the Draft's text or naming its path, the Product's checkout root, the operation, the record the Change Store holds or null, the record of each Change the Draft names as a blocker, and the Change Store's size limit, and writes one JSON result on stdout holding pass or fail and every finding with the slug of the rule it breaks, the subsection or line it names, and its detail; a request it cannot read yields invalid-request and no finding. ([test](tests/test_form_check.compliance.l1.py))
- check-import: ALWAYS: the form check's module exposes one check function that returns, for a request, the result the script writes for it, so a sibling Change skill's script reaches the check by a `__file__`-relative import. ([test](tests/test_form_check.compliance.l1.py))
- check-reads-only: NEVER: the form check writes a file or the Change Store; it reads the Draft and runs only reading git commands at the Base in the checkout root. ([test](tests/test_form_check.compliance.l1.py))

### Audit: change-standards

- standards-record: The change-standards skill states the Change record, the Change Draft, and the form check's request and result as the Change record decision states them, and names no rule the decision does not state. ([audit:standards-record])
