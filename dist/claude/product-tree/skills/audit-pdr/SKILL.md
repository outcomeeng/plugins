---
name: audit-pdr
description: >-
  PDR audit methodology — judges one PDR against the PDR evidence model,
  covering content classification, property quality, per-rule tag validity,
  atemporal voice, and consistency with ancestor decisions, and records the
  judgment as a root unit with one child unit per property in an SPX
  file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Write, Bash(spx verification run:*), Bash(git merge-base:*), Bash(git diff:*), Skill
---

<objective>

A sealed `spx verification run` on one PDR file, with one root scope unit for the PDR and one child scope unit per evidence-model property (content classification, property quality, tag validity, atemporal voice, consistency), whose verdict records every finding on touched text on its child unit, returned as the run token, the run file, and the rendered projection, whose `terminalStatus` is `approved` or `rejected`, followed by each other finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

</objective>

<constraints>

Read the PDR evidence model's boundary guidance for content classification, property quality, and tag validity before auditing: `${CLAUDE_SKILL_DIR}/references/pdr-evidence-model.md`

**PRODUCT BEHAVIOR, NOT ARCHITECTURE.**

PDRs govern what the product does, behavior that its users experience. "Sessions expire after 1 hour" is product behavior. "Sessions use JWT with 1-hour TTL" is architecture. If the content describes HOW something is built rather than WHAT users observe, it belongs in an ADR.

**ATEMPORAL VOICE.**

PDRs state atemporal product truth without historical context. No references to past behavior or events.

- NEVER modify the PDR under audit or any other product file — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `product-tree:contextualize` or `product-tree:sync-base`, and never fetch, rebase, or otherwise move the checkout — the audit reads the head as it stands, so it changes no checkout state.
- ALWAYS read the PDR evidence model before judging — derive the rule set from it, never from memory.
- ALWAYS name the location, the violated rule, and the evidence in every finding — the author repairs from the finding alone, and an unanchored finding leaves nothing to repair.
- NEVER issue a finding the cited rule does not support — drop an unbacked finding rather than reject the PDR for it.
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

`$ARGUMENTS` is a JSON object with exactly two fields. `path` is the product-relative path of the PDR to audit. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing, extra, or malformed field, or a `path` that names no PDR file, returns `BLOCKED` naming the exact field or path before any command runs.

Use skill `product-tree:product-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that `<persistence_contract>` records in a finding's `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<execution_sequence>

<step name="load_context">

**Step 1: Load context read-only**

When the live `<PRODUCT_TREE_FOUNDATION>` marker is absent or lacks `Template root`: Use skill `product-tree:understand`. Read `decisions/decision-name.pdr.md` beneath that marker's resolved absolute template directory, and derive declaration form and required tags from that canonical template. A foundation or template that cannot load returns `BLOCKED` naming the skill or read and the failure.

Load the PDR's context by reading, in this order, and starting no audit phase before every read completes:

1. the product document at `spx/`;
2. at each directory from `spx/` down to the directory containing the PDR, that directory's spec, then every decision record (`*.adr.md`, `*.pdr.md`) in it, excluding the PDR under audit;
3. every decision a loaded spec or decision cites by full `spx/` path, repeating for each newly read decision until none is unread; a citation to a missing decision file is a `BLOCKED` result naming the citation and the citing file.

The product document read here supplies the declared audience and interaction surfaces that content classification judges against. The committed changeset is resolved in `classify`.

</step>

<step name="read_pdr">

**Step 2: Read the PDR**

Read the PDR under audit completely. Identify its sections: the opening decision statement, Rationale, Product properties, and Verification.

An absent `## Verification` section is a `missing-section` finding on the `tag-validity` unit, naming the expected section and its absence as evidence. Continue the remaining checks so the run covers every property; an unenforceable PDR cannot be approved.

</step>

<step name="open_run">

**Step 3: Open the run**

Start the run before judging anything:

```bash
spx verification run start --verification-type audit --scope-type file --scope <path> --input <path>
```

A file-scoped run takes the audited path as its input, passed by path, so the retained input equals the audited file and no start payload is built. The command prints a JSON locator; take its `runToken` exactly and use it for every later command. Retain the run target the locator reports as the run file; only the start report names it. Never pass the whole locator as `--run`.

</step>

<step name="audit_content">

**Step 4: Content classification**

First, read the product document loaded in Step 1 and name its declared audience and the interaction surfaces through which that audience operates the product. Then read every statement in the PDR and classify it by the evidence model's content classification, judging "observable" against that audience:

| Content type                       | Belongs in     | Finding if in PDR                                      |
| ---------------------------------- | -------------- | ------------------------------------------------------ |
| Observable product behavior        | PDR            | Correct                                                |
| Observable non-functional property | PDR (property) | Correct                                                |
| Technology choice                  | ADR            | `architecture-content`                                 |
| Implementation approach            | ADR or code    | `architecture-content`                                 |
| Data structure or schema           | ADR            | `architecture-content`                                 |
| Performance implementation         | ADR            | `architecture-content` (a guarantee is a PDR property) |

Record each `architecture-content` finding on the `content-classification` unit.

</step>

<step name="audit_properties">

**Step 5: Property quality**

Judge each product property against the evidence model's observable, falsifiable, and stable criteria. Stability covers failure and boundary conditions; never silently limit a guarantee to the successful case.

A non-observable or unfalsifiable property is a `non-observable-property` finding, and an unstable property is an `unstable-property` finding. Record either violation on the `property-quality` unit. Name the property and the context that breaks the guarantee; a stability finding requires evidence, and an unevaluable criterion is a recorded finding naming the missing evidence, never an unjudged unit.

</step>

<step name="audit_verification">

**Step 6: Per-rule verification tag validity**

Rules live under `## Verification`. Keep Step 2's `missing-section` finding when the section is absent; an empty rule loop never clears it. If the section contains no rules, record `missing-verification-rules` on the `tag-validity` unit. An untagged rule directly under the section has the canonical authoring form and may coexist with routed subsections. For every such rule, identify its subject, the observable condition it constrains, and a concrete observation that would violate it. Record a vague, ambiguous, or unfalsifiable rule as `invalid-draft-rule` on the `property-quality` unit, quoting the rule with the missing or ambiguous criterion. For example, `ALWAYS: improve quality` fails because it names no observable condition. Select no evidence type or tag during these checks; an absent draft tag alone causes no finding.

A tagged rule requires its matching routed subsection. When `### Testing` contains rules, use skill `product-tree:test-evidence-standards` and load its assertion-type litmus. Apply that reference and the loaded foundation's assertion-type definitions to the declared claim and tag. If the required reference cannot load, record a `test-standards-unavailable` finding on the `tag-validity` unit. Judge declaration compatibility only; evidence completeness belongs to evidence auditing. Never invoke the mutating `/test` authoring workflow, select a replacement tag, or change the PDR during this audit.

For each routed rule, judge tag validity and assertion-type fit as the evidence model's tag validity states. Under `### Testing`, apply the loaded foundation's assertion-type definitions and the shared litmus to the declared claim and tag: reject a declared type whose required domain or oracle contradicts the claim, citing the claim and the loaded criterion, and do not choose among compatible types or require executable evidence for a declaration.

A routed rule with a missing, unsupported, duplicate, repeated-slug, or subsection-mismatched tag, or one that is unverifiable or vague, is an `invalid-tag` finding on the `tag-validity` unit; quote the rule and identify the missing observable condition or ambiguous criterion. An assertion type that contradicts the claim's shape is an `assertion-type-mismatch` finding.

Apply content classification, property quality, voice, and consistency to draft and routed declarations alike. Approval establishes declaration quality only; it supplies no evidence result, implementation claim, or Passing state for an untagged rule.

</step>

<step name="audit_voice">

**Step 7: Atemporal voice**

Check EVERY section for temporal language:

| Temporal (`temporal-voice`)           | Atemporal (correct)                                |
| ------------------------------------- | -------------------------------------------------- |
| "We discovered that users ask for X"  | "Users value X"                                    |
| "Currently the product does X"        | "The product does X"                               |
| "After customer feedback, we decided" | "The product does X to meet customer expectations" |
| "The existing implementation lacks"   | (omit — PDR doesn't reference code)                |

Any temporal language in any section is a `temporal-voice` finding on the `atemporal-voice` unit.

</step>

<step name="audit_consistency">

**Step 8: Consistency**

Compare the PDR against:

1. **Product document** — Does the PDR contradict the product's scope or assertions?
2. **Ancestor PDRs** — Does the PDR contradict constraints from PDRs higher in the tree?
3. **Sibling ADRs** — Does the PDR overlap with architecture concerns?

A contradiction with the product document or an ancestor PDR is a `consistency-violation` finding on the `consistency` unit. A statement that overlaps a sibling ADR's architecture concern is an `architecture-content` finding on the `content-classification` unit, judged under Step 4.

</step>

<step name="classify">

**Step 9: Classify**

Resolve the base and run the diff commands as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, and sort every finding into touched text or standing text.

</step>

<step name="record">

**Step 10: Record**

Add the root scope unit first, because a run admits one root and every child names it, then one child scope unit per property, then each finding on touched text on its child unit, per `<persistence_contract>`. Every unit is `audited` whether its property holds or carries findings. A standing finding is recorded nowhere in the run.

</step>

<step name="finish">

**Step 11: Finish**

Derive `rejected` when a finding on touched text exists and `approved` otherwise, whatever standing findings exist. Run the finish and render commands:

```bash
spx verification run finish --verification-type audit --scope-type file --scope <path> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type file --scope <path> --run <token>
```

</step>

</execution_sequence>

<persistence_contract>

Add a scope unit with `spx verification run scope add --verification-type audit --scope-type file --scope <path> --run <token> --payload <payload-file> --idempotency-key '<unitId>'`, the payload file written per `<payload_files>`. The root unit's `unitId` is the audited `<path>`, its concern partition is `pdr`, and it omits `parentUnitId`; the run admits one root. Each child unit's `unitId` is `pdr:<designator>:<path>` and its `parentUnitId` is the root's `unitId`. The designator is `content-classification`, `property-quality`, `tag-validity`, `atemporal-voice`, or `consistency`. The class `spec` and kind `pdr` are the pair `spx` accepts for a PDR subject.

The root unit:

```json
{
  "unitId": "<path>",
  "auditClass": "spec",
  "auditKind": "pdr",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "pdr"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-pdr",
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

A child unit carries the same fields with `unitId` `pdr:<designator>:<path>`, `parentUnitId` `<path>`, `coverageStatus` `audited`, and `priorContext.concernPartition` the designator:

```json
{
  "unitId": "pdr:<designator>:<path>",
  "parentUnitId": "<path>",
  "auditClass": "spec",
  "auditKind": "pdr",
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

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>` per `<payload_files>`, and `--idempotency-key '<unitId>:<rule>'`, the finding key `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines. Its payload names an accepted child unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the plugin version `<request_contract>` retained in both version fields, and no `toolVersion`; `rule` is an identifier from `${CLAUDE_SKILL_DIR}/references/rule-catalog.md`, and `location` lists every section, property, or rule text where that rule is violated, separated by `;`.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<product-tree-plugin-version>",
    "skillOwningPluginVersion": "<product-tree-plugin-version>"
  },
  "rule": "<catalog-rule-id>",
  "severity": "<blocking-or-debt>",
  "location": "<section-property-or-rule-text>[; <further-location>...]",
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

**Failure 1: Approved a PDR full of architecture decisions**

Claude saw a well-structured PDR with a clear decision statement and a Verification section, and approved it. The decision statement said "The system uses PostgreSQL with row-level locking for concurrent session management." That is an architecture decision, not a product decision. Users don't care about PostgreSQL or row-level locking — they care that concurrent sessions work.

Why it failed: Claude treated structural completeness as proof of correct content classification.

How to avoid: Step 4 classifies every statement. "Would a user be able to determine this?" is the test.

**Failure 2: Accepted non-observable properties**

Claude saw "Product properties: Database connections are pooled with a maximum of 50 connections." This is an implementation detail observable only by a DBA, not by users. The PDR version would be "The product handles at least 500 concurrent users without degradation."

Why it failed: Claude treated an implementation detail measurable by a specialist as a guarantee observable by the product's users.

How to avoid: Step 5 asks "Is this falsifiable from the user's perspective?"

**Failure 3: Approved a universal claim tagged as a scenario**

Claude saw a `### Testing` rule "ALWAYS: every export conforms to RFC 4180 ([scenario])" and approved it because the prose read like a concrete interaction. `ALWAYS` is a universal claim, and a single scenario cannot establish a claim about every case — the tag should be `mapping`, `conformance`, `property`, or `compliance`. The mismatch is `assertion-type-mismatch`, not `invalid-tag`.

How to avoid: Step 6 reads the quantifier first and separates a quantifier mismatch from a structural tag problem.

**Failure 4: Flagged a tooling product's observable state as architecture**

Claude audited a PDR for a command-line tool whose product document declares its audience operates the product through a CLI and an on-disk layout. The PDR described the repository layout the audience inspects on disk and the version-control state it observes. Claude saw git commands and filesystem paths, applied the end-user-application reflex ("a user does not see git"), and rejected the statements as `architecture-content`. That is a false positive: the declared audience operates exactly that surface, so the layout is observable product behavior.

How to avoid: Step 4 reads the product document's declared audience first and judges "observable" against it.

**Failure 5: Rejected the run on a defect in text the changeset left alone**

Claude found a real violation in an unchanged PDR passage and recorded it on the unit, so the run rejected a changeset that did not cause the defect. Classify each finding by its location, record only findings on touched text, and return every other finding as `filed`.

**Failure 6: Moved the checkout while loading context**

Claude ran the context loader that rebases the audited branch, so the head under audit was replaced by another commit. Load the context by reading files at the head as it stands.

</failure_modes>

<success_criteria>

- The run holds one `audited` root scope unit for the PDR and one child unit under its key for each of content classification, property quality, tag validity, atemporal voice, and consistency, and every unit names the root.
- Every PDR rule was judged with none skipped — content classification, property quality (observability, falsifiability, and stability), per-rule tag validity and assertion-type fit, atemporal voice, and consistency.
- Every recorded finding lies on touched text and sits on an accepted unit, is keyed by a catalog identifier, and names the location, the violated rule, and observed-versus-expected evidence.
- Every standing finding appears as a `filed` line carrying its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- An absent or empty Verification section is recorded on the tag-validity unit and an unmet property-quality criterion on the property-quality unit; neither condition can disappear through an empty iteration or leave the run `approved`.
- The `terminalStatus` is `rejected` exactly when a finding on touched text is recorded and `approved` otherwise, whatever standing findings exist.
- The checkout's head is the same before and after the audit.
- The same PDR, context, and base yield the same units, finding keys, and terminal status.

</success_criteria>
