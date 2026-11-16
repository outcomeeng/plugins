---
id: 01a0ebba-5f5a-7087-83a1-d6243fe349c7
malleability: spec
---

# Product Tree

PROVIDES the Product Tree methodology — context loading, spec authoring, testing, implementation, and commit workflows
SO THAT all language-specific and craft plugins
CAN operate within a structured framework with deterministic context, where specs declare product truth and evidence verifies it

## Assertions

### Audit: foundation model

- truth-hierarchy: The `/understand` skill declares the truth hierarchy as root product document → decision records (PDR, ADR) → specs → evidence (tests, evals, audits, probes) → code and generated artifacts, with evidence derived from specs and code complying with evidence.
- node-model: The `/understand` skill's node model declares the seven kinds — `.product` as scope and `.substrate`, `.capability`, `.domain`, `.interface`, `.surface`, and `.variant` as outputs — with the kind order substrate ≺ capability ≺ domain ≺ interface ≺ surface, the containment table, the per-kind openings, the `{slug}.spec.md` spec file, front matter carrying `id`, `kind` at the root, and `malleability` on output nodes, and decision records placed in the node whose subtree they govern with the root holding only root-scope records.
- ordering-model: The `/understand` skill's ordering model declares that prerequisites precede consumers, that independent siblings may occupy different indices, that numeric separation alone establishes no dependency, and that the context walk reads every sibling's published contract while only a named lower-index provider constrains.
- verification-model: The `/understand` skill's verification model declares the six types — validate, test, evaluate, probe, audit, review — over the Deterministic, Agentic, and Attested verdict modes; that a decision record or spec rule's group heading names its verification type, its leading slug is its one name, and it carries no tag, its slug linking its evidence once that evidence exists; the three malleability levels with the state each derives from the status claim `spx.status.json`; and the merge composition by the least malleable node touched.
- untagged-declarations-distinct: The foundation distinguishes a row whose slug links no evidence yet from the evidence required for Passing at each malleability, preserving verification selection as a separate step.
- grammar-assertion-form: The foundation's grammar reference states that a spec row outside a Mapping or Evaluate subsection opens with its slug and a colon, a Scenario row continuing on indented Given, When, Then and And lines, and stands under a group heading that names its verification type, `### Audit` heading an audit group; that a Mapping or Evaluate subsection carries its slug in its `Test.Mapping:` or `Evaluate:` heading, with one sentence and one table whose first cell in each row holds the slug of its case; and that no row carries a tag, its slug linking its evidence once that evidence exists.
- closed-taxonomy: The `/understand` skill's artifact-placement foundation declares the artifact taxonomy closed — `spx/` admits no artifact outside the placement table (whose rows include the root product document, the decision records, the output-kind and variant specs, the outcome record, the status claim, the verification artifacts under `tests/`, `evals/`, and `probes/`, `ISSUES.md` as the only node-local note, and the optional knowledge root); operational files under `spx/local/` are configuration; the note raises no placement question; placement decides only between the governing layer (ADR or PDR) and the declaring layer (spec); and verification and implementation artifacts are never placed by classification because the verification type each group heading names and the artifact each slug links derive evidence locations, and verification reachability with the language's declared infrastructure home derives implementation locations.
- change-model: The foundation's change model declares the Change as the record that carries work ordering outside the durable map, with its Maturity; its Lifecycle values `Available`, `Submitted`, `Applied`, and `Abandoned`; its Leaf and Parent types; a Leaf's Statement of Intent and Declarations; a Handoff naming the branch or Changeset, its head commit, the completed Declarations subsections, and the next subsection; and Application only on a held, Applicable Leaf whose blockers are resolved, and `ISSUES.md` as the only node-local note, and names the roles that hold and serve a Change — Refiner, Applier, Author, Fixer, and Verifier, capitalized; the Applier produces no artifact other than a mechanical repair, which it makes with no Fixer round, and the Author and the Fixer use separate agent sessions.
- product-content: The `/understand` skill defines product content as every product artifact a spec node governs or must govern — source, tests, evals, probes, generated output, specs, decisions, outcome records, status claims, notes, and spec-declared configuration, implementation being its code layer — with governance derived from node placement, the node whose linked test, eval, or probe reaches the path, or an Audit Assertion naming the path, as a search under the live foundation marker, an ungoverned artifact recorded as a coverage gap and left unread and unmodified, and operational configuration under `spx/local/` — read by its declaring skill without the marker — together with the agent harness's own instruction and settings files, tool output, session store, and scratch space excluded.
- eval-lane-file-set: The `/understand` skill's canonical node shape declares the eval lane's file set as following `eval.toml` — the co-located `evals/{rule-slug}/` directory holds `eval.toml` plus the case, prompt, and template artifacts it declares by eval-relative path, canonically `cases.jsonl`, `prompt.md`, and `prompt.template.md`; a declared case or prompt path may reach a sibling eval's shared artifact while a declared template stays inside the eval directory; a declared producer source is a repository path outside the eval directory, never a co-located artifact; and the harness-generated `history.jsonl` and ignored `runs/` transcripts are never declared.

### Audit: foundation workflow

- template-directory-in-marker: The foundation exposes the resolved absolute template directory in its live marker so authoring and auditing can read the same canonical templates independently.
- contextualized-before-access: The `/understand` skill declares that no product content is read or modified before its governing spec node has been contextualized in the conversation since the last compaction, that `/contextualize` on a node precedes any discussion of that node, that a compaction empties the set of contextualized nodes, and that an operational continuation — PR inspection, check wait, merge, deploy, release, `spx session` operations, occupancy proof — touches no product content and triggers neither `/understand` nor `/contextualize`.
- higher-level-leads: The `/understand` skill's references declare that a higher-level declaration — product document, PDR, ADR, or ancestor spec — may lead implementation, and that a change to a higher-level declaration aligns the first affected lower specs in the same change, recording any remaining downstream work in a Change, never in a node-local note.
- delivered-value: For default-branch work, the `/understand` skill declares delivered value as value merged to the default branch on origin through `/merge`; passing deterministic verification and any required local review or audit gates are progress, a committed branch ahead of its resolved base remains unfinished even with a clean working tree, and the agent continues through `/merge` until the change reaches the default branch on origin or no independent local action remains without operator input or an external-state change.
- expense-ceiling: The `/understand` skill's imperfection protocol declares that command defaults are authority for cost-bearing and quota-bearing runs, and that raising an explicit or implicit spend, quota, token, worker, retry, timeout, hosted-runner, or paid-provider ceiling requires operator approval in the same turn.
- repair-and-override: The `/understand` skill's verification model declares that a mechanical repair adds no Verifier pass of its own — Validate runs, every Test and Evaluate result it invalidates runs again, and the next Verifier pass judges it — and that an override is a verification run in which the operator sets aside an Audit verdict, a Review rejection, or an audit that reached no verdict, and never a Deterministic result.
- infrastructure-placement: The `/understand` skill's references declare that test harnesses, generators, and inert fixtures are governed by naturally placed spec nodes rather than by a mandatory top-level category subtree, per [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md).
- infrastructure-term: The methodology — skill prose, references, templates, audit findings, examples — uses "infrastructure" as the category term for test harnesses, generators, and inert fixtures, per [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md).
- no-support-terms: The methodology uses none of "support", "helpers", "utilities", and "tools" as a governing category in the testing context; these are anti-terms under [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md).

### Audit: context and subagents

- complete-context: The product-tree skills load complete product-tree context before any implementation work.
- no-partial-context: Context loading never proceeds with partial context; it aborts when any required document is missing.
- atemporal-voice: Every spec states atemporal product truth, because specs are permanent truth.
- standing-authorization: Root guides retain explicit standing authorization for every subagent supplied by a plugin in their complete authorized plugin list, requiring an active skill's explicit request before launch.
- skills-own-selection: Calling skills own subagent selection and target-only prompts; invoked skills discover the target's context. The invocation policy preserves audit result contracts and repair workflows, and root guides may carry necessary agent-specific mechanical examples.
- target-from-task-message: An invoked skill takes its target from the configured subagent's task message, never from a skill argument the harness substituted at preload.
- payload-through-file: Methodology skills that instruct Claude to call `spx`, `gh`, or another CLI pass every payload through a file Claude writes in the scratch directory the harness names for the session, under a file name unique to the agent, through the tool's own file argument or an input redirect and never through a heredoc, a pipe, or an inline form.

### Test.Compliance: subagent policy

- [subagent-policy-inheritance](tests/test_subagent_policy_inheritance.compliance.l1.py): ALWAYS: each product-tree subagent definition that declares a tools allowlist and no native permission field in a harness rendering — `adr-auditor`, `assertion-auditor`, `change-auditor`, `changes-reviewer`, `changeset-coherence-auditor`, `eval-evidence-auditor`, `implementation-auditor`, `instruction-block-updater`, `pdr-auditor`, `spec-auditor`, and `test-evidence-auditor` — inherits the invoking session's execution policy in that rendering; a native permission field a rendering declares governs that rendering instead

### Test.Scenario: tree structure

- [spec-file-named-slug](tests/test_product_tree.scenario.l1.py):
  - Given a product-tree enabler directory
  - When its contents are listed
  - Then a spec file named `{slug}.md` exists
- [prefix-integer-range](tests/test_product_tree.scenario.l1.py):
  - Given a node directory with a numeric prefix
  - When it is validated
  - Then the prefix is an integer between 10 and 99
- [marketplace-root-detected](tests/test_product_tree.scenario.l1.py):
  - Given a test file nested under a consumer `pyproject.toml`
  - When the marketplace root is detected
  - Then the detector returns the root that also contains the marketplace plugin marker
- [marketplace-root-missing](tests/test_product_tree.scenario.l1.py):
  - Given a test file outside the marketplace tree
  - When marketplace root detection exhausts the path
  - Then the detector reports a configuration error

### Test.Mapping: [node-name-parse](tests/test_product_tree.mapping.l1.py)

Each node directory name maps to its parsed index, slug, and kind, or to an absent parse when it falls outside the node grammar `{index}-{slug}.{kind}`.

| Case            | Directory name                                                | Parse                                     |
| --------------- | ------------------------------------------------------------- | ----------------------------------------- |
| valid           | `10-product-tree.enabler`                                     | index 10, slug product-tree, kind enabler |
| upper-case      | `10-PRODUCT-TREE.ENABLER`                                     | absent                                    |
| trailing-hyphen | `10-product-tree-.enabler`                                    | absent                                    |
| no-separator    | `10product-tree.enabler`                                      | absent                                    |
| spec-suffix     | the valid name with its kind replaced by the spec-file suffix | absent                                    |
| leading-zero    | `010-product-tree.enabler`                                    | absent                                    |
| index-below-ten | `09-product-tree.enabler`                                     | absent                                    |

### Test.Mapping: [index-validity](tests/test_product_tree.mapping.l1.py)

Each node index maps to valid when it lies between 10 and 99 inclusive, and formatting a directory name with an invalid index is rejected.

| Case        | Index | Validity | Formatting |
| ----------- | ----- | -------- | ---------- |
| below-range | 9     | invalid  | rejected   |
| lower-bound | 10    | valid    | formatted  |
| upper-bound | 99    | valid    | formatted  |
| above-range | 100   | invalid  | rejected   |

### Test.Mapping: [node-paths](tests/test_product_tree.mapping.l1.py)

Each node directory maps to the file path its spec occupies, and a prepared tree's traversal maps each node directory to one yielded path.

| Case                | Input                                                   | Result                                    |
| ------------------- | ------------------------------------------------------- | ----------------------------------------- |
| spec-file-path      | the directory `10-product-tree.enabler`                 | `10-product-tree.enabler/product-tree.md` |
| symlinked-duplicate | a node directory and a second directory symlinked to it | the node directory, yielded once          |

### Test.Conformance: tree shape

- [one-spec-per-node](tests/test_product_tree.conformance.l1.py): Every node directory in the tree contains exactly one spec file matching `{slug}.md` — no orphan directories exist
