<!-- Generated from the complete producer set:
dist/claude/product-tree/skills/audit-pdr/SKILL.md
dist/claude/product-tree/skills/audit-pdr/references/pdr-evidence-model.md
dist/claude/product-tree/skills/audit-pdr/references/rule-catalog.md
dist/claude/product-tree/skills/audit-pdr/references/touched-text.md
-->

Apply the complete producer below to the supplied PDR as the file-scoped audit its request contract describes: the input's `target` is the PDR path, `pdr_markdown` is the PDR's complete committed content, and `context` (when present) holds the product document and ancestor decisions the context-loading step reads. Treat the PDR as absent at the base, so every location in it is touched text and no finding is returned as `filed`. Do not inspect a repository, run a command, write a payload file, or persist an SPX verification run for this eval case, and skip the producer's request-contract, plugin-version, and run-command steps: the run identity `<path>` is the input's `target`.

Return only one JSON object that reports the sealed run the producer would record, with these members:

- `terminalStatus`: `approved` or `rejected`, derived by the producer's verdict rules.
- `units`: the root unit first, then the five child units. Each unit carries `unitId`, `parentUnitId` (omitted on the root), `auditKind`, `subject`, and `coverageStatus`.
- `findings`: every finding the producer records, each with `key`, `unitId`, `rule`, `severity`, `location`, and `evidence` holding `observed` and `expected`. The array is empty when the run records no finding.

<pre><code>
<!-- Producer: dist/claude/product-tree/skills/audit-pdr/SKILL.md -->

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

A sealed `spx verification run` on one PDR file judged against the PDR evidence model, whose `terminalStatus` is `approved` or `rejected` and whose findings on touched text sit under their catalog rule on one of five child units (content classification, property quality, tag validity, atemporal voice, consistency), returned as the run token, the run file, and the rendered projection followed by each standing finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

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

Why it failed: Claude judged the rule's prose as one concrete interaction and never read its quantifier.

How to avoid: Step 6 reads the quantifier first and separates a quantifier mismatch from a structural tag problem.

**Failure 4: Flagged a tooling product's observable state as architecture**

Claude audited a PDR for a command-line tool whose product document declares its audience operates the product through a CLI and an on-disk layout. The PDR described the repository layout the audience inspects on disk and the version-control state it observes. Claude saw git commands and filesystem paths, applied the end-user-application reflex ("a user does not see git"), and rejected the statements as `architecture-content`. That is a false positive: the declared audience operates exactly that surface, so the layout is observable product behavior.

Why it failed: Claude judged "observable" against a generic end user instead of the audience the product document declares.

How to avoid: Step 4 reads the product document's declared audience first and judges "observable" against it.

**Failure 5: Rejected the run on a defect in text the changeset left alone**

Claude found a real violation in an unchanged PDR passage and recorded it on the unit, so the run rejected a changeset that did not cause the defect.

Why it failed: Claude treated every defect found in the PDR as caused by the changeset, without sorting findings by location.

How to avoid: Classify each finding by its location, record only findings on touched text, and return every other finding as `filed`.

**Failure 6: Moved the checkout while loading context**

Claude ran the context loader that rebases the audited branch, so the head under audit was replaced by another commit.

Why it failed: Claude assumed the context loader only reads, though it rebases a behind-base branch.

How to avoid: Load the context by reading files at the head as it stands.

</failure_modes>

<success_criteria>

- Every unit is `audited` and no PDR statement, property, or rule was skipped, whether its unit holds or carries findings; property quality covers observability, falsifiability, and stability, and tag validity covers per-rule assertion-type fit.
- Every recorded finding lies on touched text and sits on an accepted unit, is keyed by a catalog identifier, and names the location, the violated rule, and observed-versus-expected evidence.
- Every standing finding appears as a `filed` line carrying its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- An absent or empty Verification section is recorded on the tag-validity unit and an unmet property-quality criterion on the property-quality unit; neither condition can disappear through an empty iteration or leave the run `approved`.
- The `terminalStatus` is `rejected` exactly when a finding on touched text is recorded and `approved` otherwise, whatever standing findings exist.
- The checkout's head is the same before and after the audit.
- The same PDR, context, and base yield the same units, finding keys, and terminal status.

</success_criteria>


<!-- Producer: dist/claude/product-tree/skills/audit-pdr/references/pdr-evidence-model.md -->

<overview>

Detailed boundary guidance for PDR content classification, property quality, and tag validity. Read this before auditing any PDR.

The audit skill owns the complete five-property workflow, including atemporal voice and consistency. This reference defines the three properties whose classification boundaries require extended examples.

</overview>

<contents>

- `<content_classification>` — observable product behavior versus architecture, grounded in the product document's declared audience and interaction surfaces, with tooling-product examples
- `<property_quality>` — observable, falsifiable, stable product properties
- `<tag_validity>` — per-rule verification tag and assertion-type fit

</contents>

<content_classification>

PDRs govern observable product behavior. Every statement must pass the user test: "Would the product document's declared audience observe or operate this?" The product document the audit loads names the audience and the interaction surfaces through which it operates the product; "observable" is judged against that declaration, never a fixed end-user-application assumption.

**Product behavior (belongs in PDR):**

- "Sessions expire after 1 hour of inactivity" — user observes expiry
- "Search results appear within 500ms" — user observes latency
- "The product supports 4 theme variants" — user selects themes
- "Uploaded files are limited to 10MB" — user hits the limit
- "Export produces valid CSV" — user opens the file

**Architecture (belongs in ADR):**

- "Sessions use JWT with 1-hour TTL" — user doesn't know about JWT
- "Search uses Elasticsearch" — user doesn't know the engine
- "Themes are implemented via CSS custom properties" — user doesn't see CSS
- "File validation uses multer middleware" — user doesn't see middleware
- "CSV generation uses fast-csv library" — user doesn't see the library

**Boundary cases:**

| Statement                                         | Verdict                                 | Reasoning                           |
| ------------------------------------------------- | --------------------------------------- | ----------------------------------- |
| "The API returns JSON responses"                  | PDR if user-facing API, ADR if internal | Depends on who the "user" is        |
| "Pages load in under 2 seconds"                   | PDR                                     | User observes load time             |
| "Response time is O(n log n)"                     | ADR                                     | User observes speed, not complexity |
| "The system handles 500 concurrent users"         | PDR                                     | User experiences the capacity       |
| "The database handles 500 concurrent connections" | ADR                                     | User doesn't see connections        |
| "Dark mode is the default theme"                  | PDR                                     | User sees the default               |
| "Dark mode uses L=0.03 OKLCH background"          | ADR                                     | User sees dark, not the color math  |

**Tooling and infrastructure products.** When the product document declares an audience that operates the product through a command-line, filesystem, version-control, or other infrastructure surface — engineers, agents, operators — the surface that audience runs and inspects is the product's observable behavior. Naming a command, a path, or a version-control concept is not by itself architecture; the audience operates exactly those things.

**Tooling product behavior (belongs in PDR):**

- "The tool recognizes two on-disk layouts: a single working tree and a worktree pool" — the audience inspects the layout on disk
- "Running the build command in a clean checkout produces a `dist/` directory" — the audience runs the command and sees the output
- "A shared state directory resolves to the same path from every worktree in a pool" — the audience relies on the resolved path
- "An unknown subcommand exits non-zero with a usage message" — the audience observes the exit code and message

**Tooling architecture (belongs in ADR), even though the product is tooling:**

- "The layout detector caches results in an in-memory map keyed by path" — the audience never sees the cache
- "The classifier reads metadata in a single pass and skips re-validating unchanged entries" — internal algorithm of the tool
- "State is persisted as newline-delimited JSON records" — a serialization schema the audience does not operate
- "The CLI is built on the Cobra command framework" — a library choice invisible to the audience

| Statement                                            | Verdict | Reasoning                                       |
| ---------------------------------------------------- | ------- | ----------------------------------------------- |
| "The repository uses a bare-repo worktree pool"      | PDR     | The audience inspects the layout on disk        |
| "Layout detection queries a version-control config"  | ADR     | The detection mechanism is internal to the tool |
| "A new worktree is created detached at the base tip" | PDR     | The audience observes the worktree state        |
| "Worktree records are held in a linked list"         | ADR     | The data structure is invisible to the audience |

**The escalation test:** When a statement is ambiguous, ask: "If this changed, would the declared audience file a bug report or a feature request?" If yes → PDR. If only an implementer of the tool — never the audience — would notice → ADR.

</content_classification>

<property_quality>

Product properties are guarantees users can rely on. They must be:

1. **Observable** — a user can perceive whether the property holds
2. **Falsifiable** — a scenario exists where it's violated
3. **Stable** — the property holds across all contexts, not just happy paths

**Good properties:**

| Property                                   | Observable                    | Falsifiable                         | Stable                 |
| ------------------------------------------ | ----------------------------- | ----------------------------------- | ---------------------- |
| "All pages load in under 2 seconds"        | User times page load          | Load a page, measure > 2s           | Applies to all pages   |
| "Theme selection persists across sessions" | User returns, sees same theme | Change theme, close browser, reopen | Applies always         |
| "Uploaded files never exceed stated limit" | User gets rejection           | Upload 11MB to 10MB limit           | Applies to all uploads |

**Bad properties:**

| Property                          | Problem                                  |
| --------------------------------- | ---------------------------------------- |
| "Good user experience"            | Not falsifiable — what counts as "good"? |
| "Database connections are pooled" | Not user-observable                      |
| "Code follows best practices"     | Not falsifiable — whose practices?       |
| "The system is scalable"          | Not falsifiable without a threshold      |
| "Fast response times"             | Not falsifiable — how fast is "fast"?    |

**Fixing bad properties:**

- "Good user experience" → "Core user flows complete in under 3 clicks"
- "The system is scalable" → "The system handles 500 concurrent users without degradation"
- "Fast response times" → "API responses return within 200ms at p95"

</property_quality>

<tag_validity>

Derive authoring and routed forms from the canonical PDR template. Specific untagged rules directly under `## Verification` await selection and receive the same clarity and falsifiability checks. The following tag checks apply to rules in routed subsections; authoring approval supplies no evidence result:

1. **Tag matching its subsection** — under `### Testing`, a `/test`-routed assertion type (`scenario`/`mapping`/`conformance`/`property`/`compliance`); under `### Eval`, `([eval])`; under `### Audit`, `([audit:{rule-slug}])` with a slug unique within the PDR, or the pathless `([audit])` that the foundation admits for a toolchain without slug support. An unsupported bare mechanism tag, a missing tag, more than one tag, a repeated `### Audit` slug, or a tag that disagrees with its subsection is `invalid-tag`.
2. **Assertion-type fit** — a `### Testing` rule's assertion type fits the claim's quantifier per the `/test` router; a universal `ALWAYS`/`NEVER` claim tagged `scenario` is `assertion-type-mismatch`, since a single case cannot establish a universal.

A rule earns a sound tag only when it is verifiable (a test, eval, or audit skill can determine pass/fail) and specific (two independent reviewers would agree on the verdict); an unverifiable or vague rule cannot carry a meaningful evidence tag.

**Well-formed verification rules:**

```markdown
## Verification

### Testing

- ALWAYS: all text/background color pairs maintain ΔL ≥ 0.80 contrast in all themes ([property])
- ALWAYS: export files conform to RFC 4180 CSV format ([conformance])
- NEVER: expose internal database IDs in user-facing URLs ([property])
- NEVER: display raw error messages from backend services to users ([compliance])

### Audit

- ALWAYS: every theme variant is selectable from the settings surface ([audit:theme-variants-selectable])
```

**Ill-formed verification rules:**

```markdown
### MUST

- Provide an intuitive interface ← unverifiable
- Follow accessibility best practices ← vague (which practices? what level?)
- Be fast ← no threshold

### NEVER

- Have bugs ← not actionable
- Break ← not specific
```

**Fixing bad rules:**

- "Follow accessibility best practices" → "Meet WCAG 2.1 Level AA for all interactive components ([compliance])"
- "Be fast" → "API responses return within 200ms at p95 under normal load ([property])"

</tag_validity>


<!-- Producer: dist/claude/product-tree/skills/audit-pdr/references/rule-catalog.md -->

<objective>

The rule catalog of the PDR audit: every rule identifier a finding may carry, the unit it is recorded on, its severity, and the clause it states. A finding is keyed `<unit>:<rule-id>` over these identifiers, and no finding names an identifier outside this catalog.

</objective>

<contents>
- `key_form`
- `form_rules`
- `blocked_inspection_rules`

</contents>

<key_form>

The unit of a finding is the child unit key `pdr:<designator>:<pdr-file-path>` of the property it concerns. The key is `<unit>:<rule-id>`, for example `pdr:atemporal-voice:spx/55-example.enabler/15-y.pdr.md:temporal-voice`. One key covers every location in the PDR where that rule is violated on that unit, and the finding lists each such location by the section, property, or rule text, never a line number, separated by `;`.

Severity in the tables below labels the defect on touched text. A finding whose locations all lie outside touched text is returned as `filed` with its recorded severity.

</key_form>

<form_rules>

| Identifier                   | Unit                     | Severity | Rule                                                                                                                                            | Stated in                                                       |
| ---------------------------- | ------------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `architecture-content`       | `content-classification` | blocking | Every statement is product behavior the declared audience observes or operates, and none states architecture or implementation.                 | `audit_workflow` Step 4                                         |
| `non-observable-property`    | `property-quality`       | blocking | Every product property is observable and falsifiable from the declared audience's perspective.                                                  | `audit_workflow` Step 5                                         |
| `unstable-property`          | `property-quality`       | blocking | Every product property holds across all applicable contexts, including failure and boundary conditions.                                         | `audit_workflow` Step 5                                         |
| `invalid-draft-rule`         | `property-quality`       | blocking | An untagged rule directly under `## Verification` names a subject, a constrained condition, and an observation that would violate it.           | `audit_workflow` Step 6                                         |
| `missing-section`            | `tag-validity`           | blocking | The PDR carries a `## Verification` section.                                                                                                    | `audit_workflow` Step 2                                         |
| `missing-verification-rules` | `tag-validity`           | blocking | The `## Verification` section contains rules.                                                                                                   | `audit_workflow` Step 6                                         |
| `invalid-tag`                | `tag-validity`           | blocking | A routed rule is verifiable and specific, carries exactly one tag valid for its subsection, and an `### Audit` slug repeats nowhere in the PDR. | `audit_workflow` Step 6                                         |
| `assertion-type-mismatch`    | `tag-validity`           | blocking | A `### Testing` rule's declared assertion type is compatible with the claim's quantifier and evidence shape.                                    | `audit_workflow` Step 6; `product-tree:test-evidence-standards` |
| `temporal-voice`             | `atemporal-voice`        | blocking | Every section states product truth atemporally.                                                                                                 | `audit_workflow` Step 7                                         |
| `consistency-violation`      | `consistency`            | blocking | The PDR contradicts neither the product document nor an ancestor PDR.                                                                           | `audit_workflow` Step 8                                         |

</form_rules>

<blocked_inspection_rules>

Each rule below fires when a required inspection cannot run, and the finding names the blocked inspection. A request that carries no PDR path starts no run and returns `BLOCKED`, so it has no rule here.

| Identifier                   | Unit           | Severity | Rule                                                                                                      | Stated in               |
| ---------------------------- | -------------- | -------- | --------------------------------------------------------------------------------------------------------- | ----------------------- |
| `test-standards-unavailable` | `tag-validity` | blocking | The assertion-type litmus of `product-tree:test-evidence-standards` loads when `### Testing` holds rules. | `audit_workflow` Step 6 |

</blocked_inspection_rules>


<!-- Producer: dist/claude/product-tree/skills/audit-pdr/references/touched-text.md -->

<objective>

The classification that sorts each PDR-audit finding into a finding on touched text, which is recorded and rejects, or a standing finding, which is returned as `filed` with its key, `baseRefEvidence`, and `issuesEntry`.

</objective>

<contents>
- `touched_text`
- `classification`
- `finding_key`
- `severity_and_disposition`
- `filed_line`

</contents>

<touched_text>

Touched text is a line of the PDR that the diff between the base and the audited tree adds or changes, extended to its enclosing unit, plus the text the change invalidates. The base is the merge-base of `HEAD` and `origin/HEAD`. The audited tree is the live working tree, which holds the retained input of the run:

```text
git merge-base HEAD origin/HEAD
git diff --unified=0 <base> -- <pdr-file-path>
```

The diff compares the base with the working tree, staged and unstaged changes included; a `<base>..HEAD` range is no endpoint, because it leaves those changes out.

The enclosing unit is the sentence in prose, the whole property for a line under Product properties, the whole rule (its text, tag, and subsection placement) for a rule line under `## Verification`, and the opening decision statement for a line within it. A PDR absent at the base is touched in full. A diff that cannot be resolved makes the whole PDR touched, and the run names the failed command.

Invalidated text is:

- text that cites, quotes, restates, or depends on changed text and now disagrees with it;
- a rule a changed line newly violates elsewhere in the PDR, such as a tag left under a subsection the edit moved its rule away from;
- generated output whose source changed.

A touched sentence that only cites an already-defective passage leaves the finding standing, against the passage. A finding that the PDR contradicts the product document or an ancestor PDR lies on touched text when the changed PDR text is one side of the contradiction. A finding that names a blocked inspection lies on touched text, because the defect is the audit's inability to judge the PDR, not a passage of it.

</touched_text>

<classification>

Classify each finding by its `location`: a finding on touched text is recorded on its unit and rejects; a finding on any other text is standing and is returned as `filed`, recorded nowhere in the run. A finding's severity labels its defect and never decides the verdict: the run approves when no finding on touched text exists, whatever standing findings it reports.

</classification>

<finding_key>

A finding is identified by its key, `<unitId>:<rule-id>`, whose `unitId` is the child unit key `pdr:<designator>:<pdr-file-path>` and whose rule is the catalogued identifier of the violated rule. The key names the unit and rule and never a line number, so the same finding carries the same key in every run and on every head. One key covers every location in the PDR where that rule is violated on that unit, listed by section, property, or rule text.

A rule violated both on touched text and elsewhere yields two findings under one key: the one on touched text is recorded on its unit, and the other is returned as `filed`.

</finding_key>

<severity_and_disposition>

A finding keeps the severity and disposition recorded for its key in the governing node's `ISSUES.md`, found in the PDR's directory or its nearest ancestor holding one, across runs. Its severity is `blocking` for a merge-safety defect and `debt` for a real defect that does not jeopardize merge safety. Its severity rises, or a `filed` finding starts to reject, only when the run names one changed basis in the finding's `evidence`: the text now lies in the diff, the change invalidates it, or the standard's catalog changed the rule or its severity. A run that names no basis returns the finding with its recorded severity and disposition.

</severity_and_disposition>

<filed_line>

After the projection, return each `filed` finding on its own line, or `filed: none`:

```text
filed: <finding-key> | rule: <rule> | severity: <blocking|debt> | run: <run-token> | baseRefEvidence: <base-commit>; <diff-command> | issuesEntry: <path>#<heading>
```

`baseRefEvidence` names the base as a full commit identity and the `git diff --unified=0 <base> -- <pdr-file-path>` command, and states that the diff leaves every location untouched in the audited tree. `issuesEntry` gives the `ISSUES.md` of the nearest node that governs the audited artifact, found by the Product Tree foundation's governing-node search for product content, or the product root's `spx/ISSUES.md` when no node governs it, and the heading of the entry that records the finding.

</filed_line>

</code></pre>

The PDR input (JSON-encoded):

```json
{input_json}
```
