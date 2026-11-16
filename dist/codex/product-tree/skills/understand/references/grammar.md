<overview>

The structural grammar of the durable map — the shapes a loader accepts — in EBNF, with the front matter fields, the index form, the evidence filenames, and the link forms. Read it when authoring a node, a record, or a verification artifact, or when validating a path.

</overview>

<contents>

1. `<lexical>`: slugs, indices, ids
2. `<nodes_and_files>`: directory names, decision files, and the files inside a node
3. `<front_matter>`: the spec's YAML fields
4. `<assertion_rows>`: the row form, group headings, Mapping and Evaluate subsections, and slug links
5. `<verification_artifacts>`: test, eval, and probe directories
6. `<containment>`: the per-kind productions
7. `<links>`: the two anchored link shapes

</contents>

<lexical>

```ebnf
digit   = "0" | ... | "9" ;
lower   = "a" | ... | "z" ;
nonzero = "1" | ... | "9" ;
integer = nonzero , digit ;                   (* exactly two digits: 10-99 *)
frac    = digit , digit ;                     (* two digits, zero-padded *)
index   = integer , { "." , frac } ;          (* 20   20.54   20.54.54 *)
word    = lower , { lower | digit } ;
slug    = word , { "-" , word } ;             (* kebab-case *)
uuid    = UUIDv7 in canonical lowercase hyphenated form ;
```

A fractional insert places a node between two indices without renumbering; a hyphen sorts before a dot, so an integer directory precedes its inserts, and comparison is numeric per segment. A node's `id` is a UUIDv7 minted at creation; a duplicate fails validation.

</lexical>

<nodes_and_files>

```ebnf
decision-ext = "adr" | "pdr" ;
decision     = index , "-" , slug , "." , decision-ext , ".md" ;

spec-file      = slug , ".spec.md" ;           (* the node's own slug; the product's name at the root *)
note-file      = "ISSUES.md" ;                 (* the one node-local note *)
outcome-file   = slug , ".outcome.md" ;        (* the node's own slug *)
status-file    = "spx.status.json" ;           (* machine-written; every output node *)
knowledge-root = "knowledge/" , "index.md" , "log.md" ;
```

`spec-file` repeats the enclosing directory's slug, so `45-pool.domain/` holds `pool.spec.md` and no other spec; a loader enforces the equality beside the grammar. Every node-local file named after its node takes this shape.

</nodes_and_files>

<front_matter>

```yaml
---
id: 01890a5d-ac96-774b-bcce-b302099a8057   # UUIDv7, unique across the tree
kind: product                               # tree root only
malleability: spec                          # output nodes only; spec | verification | implementation; absent = implementation
---
```

</front_matter>

<assertion_rows>

```ebnf
line-slug     = slug ;                                 (* unique within its file *)
line-text     = ? prose that holds no "[" outside a contract, row, or knowledge link ? ;
nl            = ? line break ? ;
heading-mark  = ? Markdown heading marker at the level the heading takes in its file ? ;
subject       = ? the subject the rules of the group share ? ;
sentence      = line-text ;
test-path     = "tests/" , test-file ;
eval-path     = "evals/" , slug , "/" , "eval.toml" ;
probe-path    = "probes/" , slug , "/" , "probe.md" ;
slug-link     = "[" , line-slug , "](" , ( test-path | eval-path | probe-path ) , ")" ;
step-line     = "  - " , ( "Given" | "When" | "Then" | "And" ) , " " , line-text ;
row           = "- " , ( line-slug | slug-link ) ,
                ( ": " , line-text | ":" , nl , step-line , { nl , step-line } ) ;  (* step lines in a Scenario only *)
group-type    = "Test.Scenario" | "Test.Conformance" | "Test.Property" | "Test.Compliance" | "Probe" | "Audit" ;
group-heading = heading-mark , group-type , [ ": " , subject ] ;
rule-group    = group-heading , nl , row , { nl , row } ;
case-table    = ? Markdown table whose first cell in each row holds the slug of its case ? ;
mapping       = heading-mark , "Test.Mapping: " , ( line-slug | slug-link ) , nl , sentence , nl , case-table ;
evaluate      = heading-mark , "Evaluate: " , ( line-slug | slug-link ) , nl , sentence , nl , case-table ;
```

A spec row outside a Mapping or Evaluate subsection opens with its slug and a colon, and so does a rule of a decision record. A Scenario row holds only its slug and a colon on its first line, and continues on indented Given, When, Then, and And lines. A row stands under a group heading that names its verification type: `### Test.Scenario`, `### Test.Conformance`, `### Test.Property`, or `### Test.Compliance` heads a test group, `### Probe` a probe group, and `### Audit` an audit group; a shared subject follows the type after a colon.

A Mapping or Evaluate subsection carries its slug in its heading, `### Test.Mapping: {slug}` or `### Evaluate: {slug}`, and holds one sentence and one table whose first cell in each row holds the slug of its case; a case slug is unique within its table. The sentence of a Mapping states the set and every condition its outcomes depend on; the sentence of an Evaluate names the producer, the context it receives, and how the eval compares an output with its expectation. An Evaluate states no threshold.

No row carries a tag. The group heading names the verification type, and the row's slug is its one name. Once its test file, eval rule, or probe protocol exists, the slug links that artifact by a node-relative path into the directory of its heading's type; before then the slug stands plain, and a dangling link derives Declared. An Audit row links no artifact, and its slug keys the claim entry. A slug is unique within its file.

</assertion_rows>

<verification_artifacts>

```ebnf
assertion-type = "scenario" | "mapping" | "conformance" | "property" | "compliance" ;
level          = "l1" | "l2" | "l3" ;
test-core      = slug , "." , assertion-type , "." , level , [ "." , slug ] ;
test-file      = test-core , ".test." , ext         (* parsing.scenario.l1.test.ts *)
               | "test_" , test-core , "." , ext    (* test_parsing.scenario.l1.py *)
               | test-core , "_test." , ext ;       (* parsing.scenario.l1_test.go *)

eval-rule  = slug , "/" , "eval.toml" , [ "cases.jsonl" ] , [ "prompt.md" ] , [ "prompt.template.md" ] ;
             (* history.jsonl and runs/ are harness-generated; eval.toml never declares them *)
probe-rule = slug , "/" , "probe.md" , { slug , "." , ext } ;
```

`tests/` commits no evidence because a test re-runs for free. An eval rule commits its run summary. A probe directory commits the attested run's inspectable artifacts; working runs stay in an ignored `runs/`. People and agents write TOML; machines write JSON.

</verification_artifacts>

<containment>

```ebnf
output-body  = spec-file , status-file , { decision } , [ note-file ] , [ outcome-file ] ,
               [ knowledge-root ] , [ tests-dir ] , [ evals-dir ] , [ probes-dir ] ;
variant-body = spec-file , status-file , { decision } , [ note-file ] ,
               [ knowledge-root ] , [ tests-dir ] , [ evals-dir ] , [ probes-dir ] ;
product-body = spec-file , { decision } , [ note-file ] , [ knowledge-root ] ;

substrate-node  = index "-" slug ".substrate/"  , output-body , { substrate-node | variant-node } ;
capability-node = index "-" slug ".capability/" , output-body , { substrate-node | capability-node | variant-node } ;
domain-node     = index "-" slug ".domain/"     , output-body , { substrate-node | capability-node | domain-node | variant-node } ;
interface-node  = index "-" slug ".interface/"  , output-body , { substrate-node | capability-node | domain-node | interface-node | variant-node } ;
surface-node    = index "-" slug ".surface/"    , output-body , { any ordered output node | variant-node } ;
variant-node    = index "-" slug ".variant/"    , variant-body , { what its parent admits, except variant-node } ;
product-node    = index "-" slug ".product/"    , product-body , { any ordered output node | product-node } ;

product-tree = "spx/" , product-body , { any ordered output node | product-node } ;
```

A product body carries no status file or verification directory because a scope has no state. A variant body carries no outcome file because its outcomes belong to its parent. The grammar names only the methodology's own artifacts; a loader walks past a harness guide, an editor directory, or a generated index.

</containment>

<links>

- **Node-local**: a relative path whose target lives inside the node and prunes with it — every assertion link.
- **Tree-absolute**: the full path from the tree root, written literally beginning `spx/` — every cross-subtree decision citation, for example `[decision](spx/55-example.substrate/15-storage.adr.md)`.

A leading-slash anchor or a `../` climb fails validation as ambiguous. Metric-source and selection-source links are external and verified by delivery; links inside a knowledge root follow the bundle's format. Implementation never links into the tree.

</links>
