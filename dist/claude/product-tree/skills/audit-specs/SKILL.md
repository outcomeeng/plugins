---
name: audit-specs
description: >-
  Spec-node audit methodology — judges one output or variant spec against the
  node-spec form, covering section structure, atemporal voice, and per-assertion
  tag fitness, and records the judgment as a root unit with one child unit per
  property in an SPX file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Write, Bash(spx verification run:*), Bash(git merge-base:*), Bash(git diff:*), Skill
---

<objective>

A sealed `spx verification run` on one node spec file, including a prior enabler/outcome form, against the node-spec form and `${CLAUDE_SKILL_DIR}/references/rule-catalog.md`, whose verdict is a `terminalStatus` of `approved` or `rejected` with each finding on touched text recorded under its category (section structure, atemporal voice, tag fitness), returned as the run token, the run file, and the rendered projection, followed by each other finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

</objective>

<constraints>

**VERIFICATION TYPE MUST FIT THE CLAIM.**

The canonical template distinguishes untagged authoring declarations directly under `## Assertions` from routed assertions. Drafts may coexist with routed subsections and receive all applicable declaration-quality checks without missing-tag or missing-heading findings. For routed assertions, apply the foundation's tag and malleability rules. The verification-type standard selects the verification type; after test is selected, the test assertion-type standard selects the test assertion type; Step 1 loads both. Two checks decide selected-tag fitness:

- Under a `[test]` tag, the assertion type (scenario, mapping, conformance, property, compliance) fits the claim's quantifier. A universal claim (ALWAYS / NEVER / "for all" / "for every" / "no input") is never `scenario`, because a scenario proves one case and cannot establish a claim about every case; `scenario` fits only a single existential interaction.
- The tag is reachable for the claim's subject. A claim whose subject is the content of an authored prose or documentation artifact — text the product authors and maintains in a document, not executable behavior — is never `[test]`. Behavioral evidence cannot verify it: the only evidence available reads the authored text and asserts on it, which proves the prose was authored, not that code behaves — whether the read is direct or laundered through test infrastructure. Such a claim's tag is `[eval]` or `[audit]`.

A required tag missing from a routed assertion, an unsupported bare mechanism tag, a duplicate tag, an assertion type the test assertion-type standard would not produce, or `[test]` on a prose-content claim is a finding. Declaration approval establishes no evidence completeness, implementation correctness, or Passing state for untagged claims.

**HEADINGS DESCRIBE CLAIM SHAPE.**

The headings under `## Assertions` group claims by shape independently of verification type. `### Scenarios` holds specific existential interactions. `### Mappings`, `### Conformance`, `### Properties`, and `### Compliance` hold their corresponding universal claim shapes. Classify the assertion text before considering its tag: a `Given … when … then …` assertion is an existential scenario under every verification type and is mismatched under `### Compliance`; an `ALWAYS:` or `NEVER:` assertion is universal and belongs under `### Compliance` unless its content establishes a mapping, conformance rule, or property. A universal ALWAYS/NEVER rule remains under `### Compliance` when its verification type is `[audit]` or `[eval]`; the heading does not assign the test-only compliance assertion type. A verification-type heading such as `### Test`, `### Eval`, or `### Audit` is outside the node-template shape and is a `heading-mismatch` finding.

**ATEMPORAL VOICE.**

A node states product truth. "The status rollup reports failing when any child fails" — not "We changed the rollup to propagate failures."

**ARTIFACT BOUNDARY.**

Decision-record form (ADR/PDR) is audited by `/audit-adr` and `/audit-pdr`; test-evidence quality is audited by `/audit-tests`. This audit checks the node spec's own form, not its tests or its decisions.

- NEVER modify the node spec under audit or any other product file — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `product-tree:contextualize` or `product-tree:sync-base`, and never fetch, rebase, or otherwise move the checkout — the audit reads the head as it stands, so it changes no checkout state.
- ALWAYS judge each assertion's verification type and each test assertion type against the standards Step 1 loads — never accept a present tag as valid by its mere presence.
- ALWAYS name the section or assertion, the violated rule, and the evidence in every finding — the author repairs from the finding alone, and an unanchored finding leaves nothing to repair.
- NEVER issue a finding the cited rule does not support — drop an unbacked finding rather than reject the node for it.
- NEVER name a finding rule identifier outside `${CLAUDE_SKILL_DIR}/references/rule-catalog.md`.
- NEVER reject, or record on a unit, a finding that lies outside touched text; classify every finding as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, return each standing finding as `filed`, and never raise its severity or let it reject unless the run names a changed basis.
- ALWAYS persist audit state through `spx verification run`, started before any judgment; NEVER use markdown comments, tracked files, or a hand-formatted verdict as audit state.
- ALWAYS write each payload as one rendered JSON object to its own file and pass the file by path as `<payload_files>` states; NEVER send a payload through a heredoc, a pipe, or an inline argument, build one with an interpreter or `printf` stage, or repair one through command substitution or post-hoc text substitution.
- ALWAYS issue each `spx verification run` mutation as its own command and wait for its exit before the next one — parallel writes race sequence assignment and corrupt the sealed journal.
- NEVER run deterministic verification, delegate the audit to another session, or finish a run whose inspection is incomplete because of elapsed time, context pressure, or unfinished reading; an unavailable required inspection is a recorded finding, never an unevaluated unit.
- NEVER write the run journal or its context anywhere but the locations `spx verification run` resolves. When the native permission policy refuses a run-recording write — a payload file, a run-recording command, or the journal — stop at that write, retry it no more, write to no other location, and return `BLOCKED` with `diagnostic: configuration error` naming the refused path; the host grants the paths, and this skill never widens its own access.
- NEVER retry a rejected command with a rewritten payload; the first command that exits nonzero ends the audit with `BLOCKED`, except the one rerun `<payload_files>` allows for a payload file named absent.

</constraints>

<audit_workflow>

<request_contract>

`$ARGUMENTS` is a JSON object with exactly two fields. `path` is the product-relative path of the node spec to audit. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing, extra, or malformed field, a `path` that names no spec file, or a `path` that names a product document, which carries no assertions and belongs to review, returns `BLOCKED` naming the exact field or path before any command runs.

Use skill `product-tree:product-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that `<persistence_contract>` records in a finding's `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<execution_sequence>

<step name="load_context">

**Step 1: Load context read-only**

When the live `<PRODUCT_TREE_FOUNDATION>` marker is absent or lacks `Template root`: Use skill `product-tree:understand`. Use skill `product-tree:verify` for the verification-type standard and use skill `product-tree:test` for the test assertion-type standard that Step 6 applies. Read the kind's canonical template beneath that marker's resolved absolute template directory; derive current openings, front matter, and tag forms from it. For a prior enabler/outcome artifact, apply the prior grammar the foundation admits.

Load the node spec's context by reading, in this order, and starting no audit phase before every read completes:

1. the product document at `spx/`;
2. at each directory from `spx/` down to the directory containing the node spec, that directory's spec, then every decision record (`*.adr.md`, `*.pdr.md`) in it; in the node's own directory, read its decision records and leave its spec to Step 2;
3. every decision a loaded spec or decision cites by full `spx/` path, repeating for each newly read decision until none is unread; a citation to a missing decision file is a `BLOCKED` result naming the citation and the citing file.

The committed changeset is resolved in `classify`. A foundation, context, or standards skill that cannot load returns `BLOCKED` naming the skill and the failure; an unavailable canonical kind template is the finding `template-missing`, recorded in `audit_structure`.

</step>

<step name="read_node">

**Step 2: Read the node**

Read the node spec. Identify its kind, opening, required front matter, `## Assertions` section, and each assertion's placement and optional tag. Current output kinds use their canonical template's opening; a variant uses its parent's kind. Prior enabler/outcome openings retain their admitted three-clause forms.

</step>

<step name="open_run">

**Step 3: Open the run**

Start the run before judging anything:

```bash
spx verification run start --verification-type audit --scope-type file --scope <path> --input <path>
```

A file-scoped run takes the audited path as its input, passed by path, so the retained input equals the audited file and no start payload is built. The command prints a JSON locator; take its `runToken` exactly and use it for every later command. Retain the run target the locator reports as the run file; only the start report names it. Never pass the whole locator as `--run`.

</step>

<step name="audit_structure">

**Step 4: Section structure**

Verify three structural properties:

1. The opening and required front matter match the canonical kind template. Prior enablers retain `PROVIDES … SO THAT … CAN …`; prior outcomes retain `WE BELIEVE THAT … WILL … CONTRIBUTING TO …`. A missing required opening clause is `malformed-kind-statement`; missing required front matter is `missing-frontmatter`. If the template could not load, finding `template-missing` names the blocked read, and the template-dependent checks are not made.
2. An `## Assertions` section contains at least one assertion. Specific untagged declarations may appear directly under it without a heading. Tagged assertions require the template's routed grouping. An empty assertion section is `missing-assertions`.
3. Each claim-shape heading (`### Scenarios`, `### Mappings`, `### Conformance`, `### Properties`, `### Compliance`) holds at least one assertion, and every assertion under it has the heading's claim shape independently of its verification-type tag; classify each assertion by the claim-shape rule in `<constraints>`. A `### Scenarios` heading whose assertions are universal is mismatched.

No kind statement or no `## Assertions` section → finding `missing-section`. A kind statement that differs from its template → finding `malformed-kind-statement`. An empty, unsupported, or claim-mismatched heading → finding `heading-mismatch`. A draft assertion's absent heading is valid.

</step>

<step name="audit_voice">

**Step 5: Atemporal voice**

Check EVERY section for temporal language:

| Temporal                              | Atemporal (correct)                |
| ------------------------------------- | ---------------------------------- |
| "We added a rollup so failures show"  | "The rollup propagates failures"   |
| "Currently the parser accepts X"      | "The parser accepts X"             |
| "After the rewrite, status derives Y" | "Status derives from test results" |

Any temporal language in any section → finding `temporal-voice`.

</step>

<step name="audit_tag_fitness">

**Step 6: Per-assertion tag fitness**

For each assertion under `## Assertions`:

1. An untagged assertion directly under `## Assertions` is an authoring declaration; check its specificity and falsifiability without selecting evidence. For routed assertions, apply the foundation's malleability rule and canonical tag forms: test, eval, and probe carry paths; audit carries its rule slug, or the admitted pathless form for a toolchain without slug support. Missing required tags, duplicate or unsupported tags, and path-bearing mechanisms without a path are `invalid-tag`.
2. Under `[test]`, the assertion type fits the claim's quantifier — apply the quantifier rule from `<constraints>` (a universal is never `scenario`). Reject a type the test assertion-type standard would not produce; do not relitigate a choice it leaves open between equally valid types.
3. The tag is reachable for the claim's subject — apply the reachability rule from `<constraints>`.

A required tag missing from a routed assertion, a duplicate tag, or an unsupported bare mechanism tag → finding `invalid-tag`. A `[test]` assertion type that contradicts the claim's quantifier → finding `evidence-type-mismatch`. `[test]` on an authored-prose claim → finding `prose-coupling`, remediated to `[eval]` or `[audit]`. An unfalsifiable draft → finding `unfalsifiable-assertion`.

</step>

<step name="classify">

**Step 7: Classify**

Resolve the base and run the diff commands as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, and sort every finding into touched text or standing text.

</step>

<step name="record">

**Step 8: Record**

Add the root scope unit first, because a run admits one root and every child names it, then one child scope unit per property, then each finding on touched text on its child unit, per `<persistence_contract>`. Every unit is `audited` whether its property holds or carries findings. A standing finding is recorded nowhere in the run.

</step>

<step name="finish">

**Step 9: Finish**

Derive `rejected` when a finding on touched text exists and `approved` otherwise, whatever standing findings exist. Run the finish and render commands:

```bash
spx verification run finish --verification-type audit --scope-type file --scope <path> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type file --scope <path> --run <token>
```

</step>

</execution_sequence>

<persistence_contract>

Add a scope unit with `spx verification run scope add --verification-type audit --scope-type file --scope <path> --run <token> --payload <payload-file> --idempotency-key '<unitId>'`, the payload file written per `<payload_files>`. The root unit's `unitId` is the audited `<path>`, its concern partition is `spec`, and it omits `parentUnitId`; the run admits one root. Each child unit's `unitId` is `spec:<designator>:<path>` and its `parentUnitId` is the root's `unitId`. The designator is `section-structure`, `atemporal-voice`, or `tag-fitness`. The class `spec` and kind `spec` are the pair `spx` accepts for a node spec subject.

The root unit:

```json
{
  "unitId": "<path>",
  "auditClass": "spec",
  "auditKind": "spec",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "spec"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-specs",
    "skillOwningPluginName": "product-tree",
    "invocationRole": "leaf-skill"
  },
  "recordedByRunDriver": {
    "producerKind": "<runDriver.producerKind>",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "<runDriver.skillName>",
    "skillOwningPluginName": "<runDriver.skillOwningPluginName>",
    "invocationRole": "<runDriver.invocationRole>"
  }
}
```

A child unit carries the same fields with `unitId` `spec:<designator>:<path>`, `parentUnitId` `<path>`, `coverageStatus` `audited`, and `priorContext.concernPartition` the designator:

```json
{
  "unitId": "spec:<designator>:<path>",
  "parentUnitId": "<path>",
  "auditClass": "spec",
  "auditKind": "spec",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "<designator>"
  },
  "expectedProducer": "<the root unit's expectedProducer object, repeated exactly>",
  "recordedByRunDriver": "<the root unit's recordedByRunDriver object, repeated exactly>"
}
```

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>` per `<payload_files>`, and `--idempotency-key '<unitId>:<rule>'`, the finding key `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines. Its payload names an accepted child unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the plugin version `<request_contract>` retained in both version fields, and no `toolVersion`; `rule` is an identifier from `${CLAUDE_SKILL_DIR}/references/rule-catalog.md`, and `location` lists every section or assertion text where that rule is violated, separated by `;`.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<product-tree-plugin-version>",
    "skillOwningPluginVersion": "<product-tree-plugin-version>"
  },
  "rule": "<catalog-rule-id>",
  "severity": "blocking",
  "location": "<section-or-assertion-text>[; <further-location>...]",
  "message": "<designator>: <finding-message>",
  "evidence": {
    "observed": "<observed-state>",
    "expected": "<state the rule requires>"
  }
}
```

These objects are the sanctioned payload schema for this audit; never derive a replacement from command help or CLI source.

</persistence_contract>

<payload_files>

Quote every idempotency key as one single-quoted argument; encode a literal apostrophe with the splice `'"'"'`.

- ALWAYS copy the scratch directory the harness names for the session into each payload path character for character, and write each scope and finding payload with the file-write tool to its own file there, under a name unique to this run and payload, such as `<run-token>-scope-<n>.json` and `<run-token>-finding-<n>.json`. Where the harness names no scratch directory, use the one the hosting environment designates, such as `$RUNNER_TEMP` on a hosted runner.
- ALWAYS write only payload files with the file-write tool.
- ALWAYS stop before the command that reads a payload file when the file-write result reports a path that the scratch directory does not contain by whole path components, returning the `<verdict_format>` diagnostic naming the reported path.
- ALWAYS pass `--payload` the path exactly as the file-write tool's result reports it, copied from that result, never retyped from memory.
- ALWAYS pass the file as the value of `--payload`, its path written out literally:

  ```bash
  spx verification run scope add --verification-type audit --scope-type file --scope <path> --run <token> --payload <scope-file> --idempotency-key '<unitId>'
  ```

- ALWAYS add each scope unit and each finding with its own literal command and its own payload file, one at a time, and stop the audit at the first command that exits nonzero, other than the one rerun on an absent-payload diagnostic that the next bullet allows, returning the `<verdict_format>` diagnostic.
- A permission refusal is no absent payload file and takes no rerun.
- ALWAYS, when a command exits nonzero with a diagnostic that names its payload file as absent, run that command once more with the path copied from the file-write result; on a second failure, stop with the `<verdict_format>` diagnostic naming the run token.
- NEVER remove a payload file; the harness clears its scratch directory.

</payload_files>

</audit_workflow>

<verdict_format>

Return the run token, the run file, and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `APPROVED` or `REJECTED` envelope and no restated findings. After the projection, return each standing finding on its own line in the form `${CLAUDE_SKILL_DIR}/references/touched-text.md` gives, or `filed: none`.

When a command exits nonzero or a prerequisite is absent, return:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-command-attempted>
payloadSource: <payload-file-path|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
diagnostic: <configuration error naming the refused path, or none>
```

</verdict_format>

<failure_modes>

**Failure 1: Passed a `[test]` claim about a document's prose**

Claude read an assertion — "the skill body states the three-gate vocabulary ([test])" — and passed it because a `[test]` tag was present and pointed at a file. The only evidence such a claim admits reads the authored body and asserts a substring of it, so it proves the prose was typed, not that code behaves. The tag belongs in `[eval]` or `[audit]`. The coupling is identical whether the test reads the body directly or through a harness constant or reader helper — full-chain, the claim still verifies prose.

How to avoid: Step 6 check 3 applies the reachability rule from `<constraints>`; record the claim as `prose-coupling`.

**Failure 2: Passed a universal claim tagged `scenario`**

Claude saw a `### Compliance` assertion — a universal ALWAYS/NEVER claim — tagged `([test](… scenario …))` and passed it because the assertion type named one of the five. A scenario proves one case; it cannot establish a claim about every case, so the assertion ships unverified.

How to avoid: Step 6 check 2 verifies the assertion type fits the quantifier. Record a universal tagged `scenario`, and any type the test assertion-type standard would not produce — without relitigating a choice it leaves open between equally valid types.

**Failure 3: Rejected universal audit rules under `### Compliance`**

Claude read the evidence node's universal `[audit]` rules under `### Compliance` and rejected them as `heading-mismatch` because audit assertions carry no assertion type. That conflated the heading's claim-shape grouping with the test-only compliance assertion type and contradicted the canonical node templates.

How to avoid: Step 4 judges the heading from the claim's quantifier and form independently of its verification-type tag. Keep universal ALWAYS/NEVER rules under `### Compliance` with `[test]`, `[eval]`, or `[audit]`; reject verification-type headings such as `### Audit` instead.

**Failure 4: Passed an existential scenario under `### Compliance`**

Claude read a `Given … when … then …` assertion under `### Compliance` and approved the node because the assertion carried `[eval]`. The tag described how the verdict was established; it did not change the assertion from a specific existential interaction into a universal rule.

How to avoid: Step 4 classifies explicit assertion form before verification type. Treat every `Given … when … then …` assertion as a scenario and record it under any heading other than `### Scenarios` as `heading-mismatch`.

**Failure 5: Rejected the run on a defect in text the changeset left alone**

Claude found a real violation in an unchanged spec passage and recorded it on the unit, so the run rejected a changeset that did not cause the defect. Classify each finding by its location, record only findings on touched text, and return every other finding as `filed`.

**Failure 6: Moved the checkout while loading context**

Claude ran the context loader that rebases the audited branch, so the head under audit was replaced by another commit. Load the context by reading files at the head as it stands.

</failure_modes>

<success_criteria>

- Every unit is `audited` and every child unit names the root, with no unit left unevaluated.
- Every spec-node rule was judged with none skipped — claim-shape heading structure independent of verification type, atemporal voice, and per-assertion tag fitness (coverage-complete).
- Every recorded finding lies on touched text, sits on an accepted unit, is keyed by an identifier from the rule catalog, and names the section or assertion, the violated rule, and observed-versus-expected evidence.
- Every standing finding carries its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- The `terminalStatus` derives from findings on touched text alone, whatever standing findings exist.
- The checkout's head is the same before and after the audit.
- The same node spec, context, and base yield the same units, finding keys, and terminal status.

</success_criteria>
