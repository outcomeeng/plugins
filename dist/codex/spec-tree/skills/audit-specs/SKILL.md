---
name: audit-specs
description: >-
  Spec-node audit methodology — judges one output or variant spec against the
  node-spec form, covering section structure, atemporal voice, and per-assertion
  tag fitness, and records the judgment as one root unit and one child unit per
  property in an SPX file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Write, Bash(spx verification run:*), Bash(git merge-base:*), Bash(git diff:*)
---

<objective>

A sealed `spx verification run` judging one output or variant spec, including prior enabler/outcome forms, against the node-spec form, with one root unit for the spec and one child unit per declaration-quality property (`section-structure`, `atemporal-voice`, `tag-fitness`), every finding on touched text recorded on its unit, returned as the run token, the run file, and the rendered projection, whose `terminalStatus` is `approved` or `rejected`, followed by each other finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

</objective>

<constraints>

**VERIFICATION TYPE MUST FIT THE CLAIM.**

The canonical template distinguishes untagged authoring declarations directly under `## Assertions` from routed assertions. Drafts may coexist with routed subsections and receive all applicable declaration-quality checks without missing-tag or missing-heading findings. For routed assertions, apply the foundation's tag and malleability rules. `/verify` selects the verification type; after test is selected, `/test` selects the test assertion type. Two checks decide selected-tag fitness:

- Under a `[test]` tag, the assertion type (scenario, mapping, conformance, property, compliance) fits the claim's quantifier. A universal claim (ALWAYS / NEVER / "for all" / "for every" / "no input") is never `scenario`, because a scenario proves one case and cannot establish a claim about every case; `scenario` fits only a single existential interaction.
- The tag is reachable for the claim's subject. A claim whose subject is the content of an authored prose or documentation artifact — text the product authors and maintains in a document, not executable behavior — is never `[test]`. Behavioral evidence cannot verify it: the only evidence available reads the authored text and asserts on it, which proves the prose was authored, not that code behaves — whether the read is direct or laundered through test infrastructure. Such a claim's tag is `[eval]` or `[audit]`.

A required tag missing from a routed assertion, an unsupported bare mechanism tag, a duplicate tag, an assertion type the `/test` router would not produce, or `[test]` on a prose-content claim is a finding. Declaration approval establishes no evidence completeness, implementation correctness, or Passing state for untagged claims.

**HEADINGS DESCRIBE CLAIM SHAPE.**

The headings under `## Assertions` group claims by shape independently of verification type. `### Scenarios` holds specific existential interactions. `### Mappings`, `### Conformance`, `### Properties`, and `### Compliance` hold their corresponding universal claim shapes. Classify the assertion text before considering its tag: a `Given … when … then …` assertion is an existential scenario under every verification type and is mismatched under `### Compliance`; an `ALWAYS:` or `NEVER:` assertion is universal and belongs under `### Compliance` unless its content establishes a mapping, conformance rule, or property. A universal ALWAYS/NEVER rule remains under `### Compliance` when its verification type is `[audit]` or `[eval]`; the heading does not assign the test-only compliance assertion type. A verification-type heading such as `### Test`, `### Eval`, or `### Audit` is outside the node-template shape and is a `heading-mismatch` finding.

**ATEMPORAL VOICE.**

A node states product truth. "The status rollup reports failing when any child fails" — not "We changed the rollup to propagate failures."

**BINARY OUTCOME.**

The run finishes `approved` or `rejected`. An unavailable required inspection is a finding on the unit it blocks, so the run finishes `rejected`; it never becomes an approval through an unevaluated unit.

**ARTIFACT BOUNDARY.**

Decision-record form (ADR/PDR) is audited by `/audit-adr` and `/audit-pdr`; test-evidence quality is audited by `/audit-tests`. This audit checks the node spec's own form, not its tests or its decisions.

- NEVER modify the node spec under audit or any other product file — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `/contextualize` or `/sync-base`: both can move the checkout, and this audit leaves the checkout unmoved. Step 1 loads the node spec's context read-only.
- ALWAYS judge each assertion's verification type against `/verify` and each test assertion type against `/test` — never accept a present tag as valid by its mere presence.
- ALWAYS name the section or assertion, the violated rule, and the evidence in every finding.
- NEVER issue a finding the cited rule does not support — drop an unbacked finding rather than reject the node for it.
- NEVER reject on text the changeset leaves unchanged and does not invalidate — return that finding as `filed`, and NEVER raise a recorded finding's severity or let a `filed` finding start to reject unless the run names a changed basis. `${SKILL_DIR}/references/touched-text.md` defines touched text, the finding key, and the `filed` line.
- ALWAYS persist audit state through `spx verification run`, started before any judgment; NEVER use markdown comments, tracked files, or a hand-formatted verdict as audit state.
- ALWAYS write each payload as one rendered JSON object to its own file and pass the file by path as `<payload_files>` states; NEVER send a payload through a heredoc, a pipe, or an inline argument, build one with an interpreter or `printf` stage, or repair one through command substitution or post-hoc text substitution.
- ALWAYS issue each `spx verification run` mutation as its own command and wait for its exit before the next one — parallel writes race sequence assignment and corrupt the sealed journal.
- NEVER retry a rejected command with a rewritten payload; the first command that exits nonzero ends the audit with `BLOCKED`.

</constraints>

<audit_workflow>

<request_contract>

`$ARGUMENTS` is a JSON object with exactly two fields. `path` is the product-relative path of the node spec to audit, spaces preserved. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing, extra, or malformed field, or an empty `path`, returns `BLOCKED` with run token `not-started` naming the exact field before any command runs.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that `<persistence_contract>` records in `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<step name="load_context">

**Step 1: Load context read-only**

When the live `<SPEC_TREE_FOUNDATION>` marker is absent or lacks `Template root`: Use skill `spec-tree:understand`. Read the kind's canonical template beneath that marker's resolved absolute template directory; derive current openings, front matter, and tag forms from it. For a prior enabler/outcome artifact, apply the prior grammar the foundation admits.

Load the node spec's context with `Read`, `Glob`, and `Grep` alone, in this order:

1. The product spec.
2. Each spec and every decision record in each directory on the path from `spx/` to the directory containing the node spec, root first, the node spec under audit excluded.
3. Every decision that a loaded spec or decision cites by full `spx/` path, each read once.

A decision that a loaded record cites and that cannot be read is a `context-unavailable` finding on the root unit, recorded in Step 5. An unavailable canonical template is a `template-missing` finding on the `section-structure` unit, naming the blocked read. Do not proceed without the live `<SPEC_TREE_FOUNDATION>` marker.

</step>

<step name="open_run">

**Step 2: Open the run**

Start the run before judging anything:

```bash
spx verification run start --verification-type audit --scope-type file --scope <path> --input <path>
```

A file-scoped run takes the audited path as its input, passed by path, so the retained input equals the audited file and no start payload is built.

The command prints a JSON locator; take its `runToken` exactly and use it for every later command. Retain the run target the locator reports as the run file; only the start report names it. Never pass the whole locator as `--run`.

</step>

<step name="read_node">

**Step 3: Read the node**

Read the node spec. An absent or unreadable target returns `BLOCKED` with the exact failure. Identify its kind, opening, required front matter, `## Assertions` section, and each assertion's placement and optional tag. Current output kinds use their canonical template's opening; a variant uses its parent's kind. Prior enabler/outcome openings retain their admitted three-clause forms. A product target is an `unsupported-target` finding on the root unit, because product specs carry no assertions and belong to review; record it in Step 5 with no child unit, and finish `rejected`.

Resolve the touched text of the node spec as `${SKILL_DIR}/references/touched-text.md` states, so Steps 4 to 6 can classify each finding.

</step>

<step name="audit_structure">

**Step 4: Judge section structure, atemporal voice, and tag fitness, in that order**

<property name="section-structure">

Verify three structural properties:

1. The opening and required front matter match the canonical kind template. Prior enablers retain `PROVIDES … SO THAT … CAN …`; prior outcomes retain `WE BELIEVE THAT … WILL … CONTRIBUTING TO …`. A missing required opening clause is `malformed-kind-statement`; missing required front matter is `missing-frontmatter`.
2. An `## Assertions` section contains at least one assertion. Specific untagged declarations may appear directly under it without a heading. Tagged assertions require the template's routed grouping. An empty assertion section is `missing-assertions`.
3. Each claim-shape heading (`### Scenarios`, `### Mappings`, `### Conformance`, `### Properties`, `### Compliance`) holds at least one assertion, and every assertion under it has the heading's claim shape independently of its verification-type tag. Classify explicit forms first: `Given … when … then …` is a scenario and belongs only under `### Scenarios`; `ALWAYS:` and `NEVER:` are universal and belong under `### Compliance` unless their content establishes a mapping, conformance rule, or property. A `### Scenarios` heading whose assertions are universal is mismatched; a `### Compliance` heading whose assertions are universal remains valid with `[test]`, `[eval]`, or `[audit]`; a `### Compliance` heading containing a `Given … when … then …` assertion is mismatched; and a verification-type heading such as `### Audit` is unsupported.

**No kind statement or no `## Assertions` section → finding rule `missing-section`. A kind statement that differs from its template → finding rule `malformed-kind-statement`. An empty, unsupported, or claim-mismatched heading → finding rule `heading-mismatch`. A draft assertion's absent heading is valid.**

</property>

<property name="atemporal-voice">

Check EVERY section for temporal language:

| Temporal (finding)                    | Atemporal (correct)                |
| ------------------------------------- | ---------------------------------- |
| "We added a rollup so failures show"  | "The rollup propagates failures"   |
| "Currently the parser accepts X"      | "The parser accepts X"             |
| "After the rewrite, status derives Y" | "Status derives from test results" |

**Any temporal language in any section → finding rule `temporal-voice`.**

</property>

<property name="tag-fitness">

For each assertion under `## Assertions`:

1. An untagged assertion directly under `## Assertions` is an authoring declaration; check its specificity and falsifiability without selecting evidence. For routed assertions, apply the foundation's malleability rule and canonical tag forms: test, eval, and probe carry paths; audit carries its rule slug, or the admitted pathless form for a toolchain without slug support. Missing required tags, duplicate or unsupported tags, and path-bearing mechanisms without a path are `invalid-tag`.
2. Under `[test]`, the assertion type fits the claim's quantifier — apply the quantifier rule from `<constraints>` (a universal is never `scenario`). Reject a type the `/test` router would not produce; do not relitigate a choice the router leaves open between equally valid types.
3. The tag is reachable for the claim's subject. When the claim's subject is the content of an authored prose or documentation artifact rather than executable behavior, `[test]` is unreachable — its only evidence reads the authored text and asserts on it (directly or through a fixture or harness that exposes or reads the artifact), proving the prose was authored rather than that code behaves. The tag belongs in `[eval]` (a graded judgment over the producer's structured verdict) or `[audit]` (a semantic constraint).

**A required tag missing from a routed assertion, a duplicate tag, or an unsupported bare mechanism tag → finding rule `invalid-tag`. A `[test]` assertion type that contradicts the claim's quantifier → finding rule `evidence-type-mismatch`. `[test]` on an authored-prose claim → finding rule `prose-coupling`. An unfalsifiable draft → finding rule `unfalsifiable-assertion`.**

</property>

</step>

<step name="classify">

**Step 5: Classify and record**

Classify every finding per `${SKILL_DIR}/references/touched-text.md`: a finding on touched text is recorded on its unit with the severity its catalog row declares; every other finding is standing, returned as a `filed` line, and recorded nowhere in the run.

Once judgment is complete, add the root unit first, because a run admits one root and every child names it, then one child unit per property, then each finding on touched text on the unit of the concern it names; a finding that names no child unit sits on the root. Every unit is `audited`, whether it holds or carries findings. Record per `<persistence_contract>`.

</step>

<step name="finish">

**Step 6: Finish and render**

Derive `rejected` when a finding on touched text exists and `approved` otherwise, whatever standing findings exist. Run the finish and render commands:

```bash
spx verification run finish --verification-type audit --scope-type file --scope <path> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type file --scope <path> --run <token>
```

</step>

<persistence_contract>

Every unit carries `auditClass: spec` and `auditKind: spec`, and its `subject` and `priorContext.changedFilePartition` are the node spec `<path>`. The root unit's `unitId` is `spec:root:<path>`, it omits `parentUnitId`, and its concern partition is `spec`. A property unit's `unitId` is `spec:property:<property>:<path>` with `<property>` one of `section-structure`, `atemporal-voice`, or `tag-fitness`. Each child's `parentUnitId` is the root's `unitId`, and its concern partition is its property name.

A scope unit:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-child-only>",
  "auditClass": "spec",
  "auditKind": "spec",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "<spec-or-property>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-specs",
    "skillOwningPluginName": "spec-tree",
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

Add a unit with `spx verification run scope add --verification-type audit --scope-type file --scope <path> --run <token> --payload <payload-file> --idempotency-key '<unitId>'`. The root unit omits the `parentUnitId` field.

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>`, and `--idempotency-key '<finding-key>'`, the finding key `${SKILL_DIR}/references/touched-text.md` defines as `<unitId>:<rule>`. Its payload names an accepted unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the plugin version `<request_contract>` retained in both version fields, and no `toolVersion`; `rule` is one identifier from `<rule_catalog>` in `${SKILL_DIR}/references/spec-evidence-model.md`, and `severity` is the severity that row declares; name no identifier outside that catalog.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<spec-tree-plugin-version>",
    "skillOwningPluginVersion": "<spec-tree-plugin-version>"
  },
  "rule": "<finding-identifier>",
  "severity": "<catalog-row-severity>",
  "location": "<section-or-assertion-text>",
  "message": "<finding-message-naming-section-rule-and-evidence>",
  "evidence": {
    "observed": "<observed-state>",
    "expected": "<state the rule or template requires>"
  }
}
```

These objects are the sanctioned payload schema for this audit; never derive a replacement from command help or CLI source.

</persistence_contract>

<payload_files>

Quote every idempotency key as one single-quoted argument; encode a literal apostrophe with the splice `'"'"'`.

- ALWAYS write each scope and finding payload with the file-write tool to its own file in the scratch directory the harness names for the session, under a name unique to this run and payload, such as `<run-token>-scope-<n>.json` and `<run-token>-finding-<n>.json`. Where the harness names no scratch directory, use the one the hosting environment designates, such as `$RUNNER_TEMP` on a hosted runner.
- ALWAYS write only payload files with the file-write tool.
- ALWAYS pass `--payload` the path exactly as the file-write tool's result reports it, copied from that result, never retyped.
- ALWAYS add each unit and each finding with its own literal command and its own payload file, one at a time, and stop the audit at the first command that exits nonzero, returning the `BLOCKED` diagnostic.
- NEVER remove a payload file; the harness clears its scratch directory.

</payload_files>

</audit_workflow>

<verdict_format>

Return the run token, the run file, and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `APPROVED` or `REJECTED` envelope and no restated findings. After the projection, return each standing finding as a `filed` line in the form `${SKILL_DIR}/references/touched-text.md` gives, or `filed: none`.

When a command exits nonzero or a prerequisite is absent, return:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-command-attempted>
payloadSource: <payload-file-path|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
```

</verdict_format>

<failure_modes>

**Failure 1: Passed a `[test]` claim about a document's prose**

Claude read an assertion — "the skill body states the three-gate vocabulary ([test])" — and passed it because a `[test]` tag was present and pointed at a file. The only evidence such a claim admits reads the authored body and asserts a substring of it, so it proves the prose was typed, not that code behaves. The tag belongs in `[eval]` or `[audit]`. The coupling is identical whether the test reads the body directly or through a harness constant or reader helper — full-chain, the claim still verifies prose.

How to avoid: Step 4 `tag-fitness` check 3 — when the claim's subject is the content of an authored prose or documentation artifact, `[test]` is unreachable. Record it as `prose-coupling` and remediate to `[eval]` or `[audit]`.

**Failure 2: Passed a universal claim tagged `scenario`**

Claude saw a `### Compliance` assertion — a universal ALWAYS/NEVER claim — tagged `([test](… scenario …))` and passed it because the assertion type named one of the five. A scenario proves one case; it cannot establish a claim about every case, so the assertion ships unverified.

How to avoid: Step 4 `tag-fitness` check 2 verifies the assertion type fits the quantifier. Record a universal tagged `scenario`, and any type the router would not produce, as `evidence-type-mismatch` — without relitigating a choice the router leaves open between equally valid types.

**Failure 3: Rejected universal audit rules under `### Compliance`**

Claude read the evidence node's universal `[audit]` rules under `### Compliance` and rejected them as `heading-mismatch` because audit assertions carry no assertion type. That conflated the heading's claim-shape grouping with the test-only compliance assertion type and contradicted the canonical node templates.

How to avoid: Step 4 `section-structure` judges the heading from the claim's quantifier and form independently of its verification-type tag. Keep universal ALWAYS/NEVER rules under `### Compliance` with `[test]`, `[eval]`, or `[audit]`; record verification-type headings such as `### Audit` instead.

**Failure 4: Passed an existential scenario under `### Compliance`**

Claude read a `Given … when … then …` assertion under `### Compliance` and approved the node because the assertion carried `[eval]`. The tag described how the verdict was established; it did not change the assertion from a specific existential interaction into a universal rule.

How to avoid: Step 4 `section-structure` classifies explicit assertion form before verification type. Treat every `Given … when … then …` assertion as a scenario and record it under any heading other than `### Scenarios` as `heading-mismatch`.

**Failure 5: Loaded context through the synchronizing skills**

Claude invoked `/contextualize` to load the node spec's context, and its `/sync-base` step rebased or advanced the checkout under the audit, so the head the audit judged differed from the head it started on.

How to avoid: Load context with the read-only steps of Step 1 and never invoke either skill.

</failure_modes>

<success_criteria>

- Every spec-node rule was judged with none skipped — claim-shape heading structure independent of verification type, atemporal voice, and per-assertion tag fitness — and every unit the run holds is `audited`.
- Every recorded finding lies on touched text and sits on an accepted unit, naming the section or assertion, the violated rule, and the evidence — the malformed kind statement, the empty or mismatched heading, the temporal phrase, the invalid tag, the quantifier-mismatched assertion type, or the prose-coupled `[test]`.
- Every standing finding appears as a `filed` line carrying its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- The terminal status is `rejected` exactly when a finding on touched text is recorded, so no standing finding and no unevaluated unit decides it.
- The checkout the audit judged is the checkout it started on and left, so the verdict describes one head.
- The same node spec, context, and base yield the same units, finding keys, and terminal status.
- The reported terminal status is the run's own, unaltered, and each standing finding is reported outside the run, so the verdict neither hides nor inflates a finding.

</success_criteria>
