---
name: audit-pdr
description: >-
  PDR audit methodology — judges one PDR against the PDR evidence model,
  covering content classification, property quality, per-rule tag validity,
  atemporal voice, and consistency with ancestor decisions, and records the
  judgment as one root unit and one child unit per property in an SPX
  file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Write, Bash(spx verification run:*), Bash(git merge-base:*), Bash(git diff:*), {{! tool('use_skill') !}}
---

<objective>

A sealed `spx verification run` judging one PDR against the PDR evidence model, with one root unit for the PDR and one child unit per evidence-model property (`content-classification`, `property-quality`, `tag-validity`, `atemporal-voice`, `consistency`), every finding on touched text recorded on its unit, returned as the run token, the run file, and the rendered projection, whose `terminalStatus` is `approved` or `rejected`, followed by each other finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

</objective>

<constraints>

Read the PDR evidence model's boundary guidance for content classification, property quality, and tag validity before auditing: `${CLAUDE_SKILL_DIR}/references/pdr-evidence-model.md`

**PRODUCT BEHAVIOR, NOT ARCHITECTURE.**

PDRs govern what the product does, behavior that its users experience. "Sessions expire after 1 hour" is product behavior. "Sessions use JWT with 1-hour TTL" is architecture. If the content describes HOW something is built rather than WHAT users observe, it belongs in an ADR.

"Users" means the audience the product document declares, and "observe" means observe through the interaction surfaces that document names — not a fixed end-user-application assumption. When the product document declares an audience that operates the product through a command-line, filesystem, version-control, or other infrastructure surface, the CLI, filesystem, and version-control state that audience operates is product behavior; the internal algorithm, in-memory data structure, persisted schema, and library choices that audience never touches stay architecture.

**ATEMPORAL VOICE.**

PDRs state atemporal product truth without historical context. No references to past behavior or events.

**BINARY OUTCOME.**

The run finishes `approved` or `rejected`. An unavailable required inspection is a finding on the unit it blocks, so the run finishes `rejected`; it never becomes an approval through an unevaluated unit.

- NEVER modify the PDR under audit or any other product file — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `/contextualize` or `/sync-base`: both can move the checkout, and this audit leaves the checkout unmoved. Step 1 loads the PDR's context read-only.
- ALWAYS read the PDR evidence model before judging — derive the rule set from it, never from memory.
- ALWAYS name the section, the violated rule, and the evidence in every finding.
- NEVER issue a finding the cited rule does not support — drop an unbacked finding rather than reject the PDR for it.
- NEVER reject on text the changeset leaves unchanged and does not invalidate — return that finding as `filed`, and NEVER raise a recorded finding's severity or let a `filed` finding start to reject unless the run names a changed basis. `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines touched text, the finding key, and the `filed` line.
- ALWAYS persist audit state through `spx verification run`, started before any judgment; NEVER use markdown comments, tracked files, or a hand-formatted verdict as audit state.
- ALWAYS write each payload as one rendered JSON object to its own file and pass the file by path as `<payload_files>` states; NEVER send a payload through a heredoc, a pipe, or an inline argument, build one with an interpreter or `printf` stage, or repair one through command substitution or post-hoc text substitution.
- ALWAYS issue each `spx verification run` mutation as its own command and wait for its exit before the next one — parallel writes race sequence assignment and corrupt the sealed journal.
- NEVER retry a rejected command with a rewritten payload; the first command that exits nonzero ends the audit with `BLOCKED`.

</constraints>

<audit_workflow>

<request_contract>

`$ARGUMENTS` is a JSON object with exactly two fields. `path` is the product-relative path of the PDR to audit, spaces preserved. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing, extra, or malformed field, or an empty `path`, returns `BLOCKED` with run token `not-started` naming the exact field before any command runs.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that `<persistence_contract>` records in `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<step name="load_context">

**Step 1: Load context read-only**

When the live `<SPEC_TREE_FOUNDATION>` marker is absent or lacks `Template root`: Use skill `spec-tree:understand`. Read `decisions/decision-name.pdr.md` beneath that marker's resolved absolute template directory, and derive declaration form and required tags from that canonical template. The template remains owned by that skill.

Load the PDR's context with `Read`, `Glob`, and `Grep` alone, in this order:

1. The product spec.
2. Each spec and every decision record in each directory on the path from `spx/` to the directory containing the PDR, root first. A product-root PDR has `spx/` alone on that path. The PDR under audit is excluded.
3. Every decision that a loaded spec or decision cites by full `spx/` path, each read once.

The product document used below is the product spec loaded first. Use that spec's declared audience and interaction surfaces for content classification. Resolve the base as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states.

A decision that a loaded record cites and that cannot be read is a `context-unavailable` finding on the root unit, recorded in Step 6. Do not proceed without the canonical PDR template content and the live `<SPEC_TREE_FOUNDATION>` marker.

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

<step name="read_pdr">

**Step 3: Read the PDR**

Read the PDR under audit. Identify its sections: the opening decision statement, Rationale, Product properties, and Verification. An absent or unreadable target returns `BLOCKED` with the exact failure.

Resolve the touched text of the PDR as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, so Step 4 can classify each finding.

Record an absent `## Verification` section as a finding with rule `missing-section` on the `tag-validity` unit, naming the expected section and identifying its absence as evidence. Continue the remaining checks so the run covers every evaluable property; an unenforceable PDR cannot finish `approved`.

</step>

<step name="audit_properties">

**Step 4: Judge the five properties, in order**

<property name="content-classification">

First, name the product document's declared audience and the interaction surfaces through which that audience operates the product. "Observable" is judged against that audience: a statement is product behavior when the declared audience observes or operates it. For a product whose audience operates a command-line, filesystem, version-control, or other infrastructure surface, the CLI commands, on-disk layout, and version-control state that audience runs and inspects are observable product behavior — not architecture. The architecture line falls at what the audience never operates: the internal algorithm by which a tool reaches an observable result, the in-memory data structures it holds, the schema it persists, and the libraries it depends on.

Then read every statement in the PDR. Classify each:

| Content type                       | Belongs in     | Finding if in PDR              |
| ---------------------------------- | -------------- | ------------------------------ |
| Observable product behavior        | PDR            | Correct                        |
| Observable non-functional property | PDR (property) | Correct                        |
| Technology choice                  | ADR            | Architecture                   |
| Implementation approach            | ADR or code    | Implementation                 |
| Data structure or schema           | ADR            | Architecture                   |
| Performance implementation         | ADR            | Architecture (guarantee = PDR) |

**Any architecture or implementation content → finding rule `architecture-content`.**

The test: "Would the product document's declared audience observe or operate this?" If yes, it is product behavior. If only an implementer of the tool — never the audience — would know it, it belongs in an ADR. Do not flag a tooling product's CLI, filesystem, or version-control state as architecture merely because it names git, a path, or a command; that state is what its audience operates. Reserve the architecture finding for the tool's internal algorithm, data structures, schema, and library choices.

</property>

<property name="property-quality">

For each product property:

1. Is it observable from the user's perspective?
   - "Pages load in under 2 seconds" → observable ✓
   - "Database uses row-level locking" → not user-observable ✗
2. Is it falsifiable — is there a scenario where it's violated?
   - "Good user experience" → unfalsifiable ✗
   - "Search returns results in under 500ms" → falsifiable ✓
3. Is it stable — does its guarantee hold across all applicable contexts, including failure and boundary conditions, as the evidence model requires?
   - "Theme selection persists across sessions" → assess persistence across session boundaries and failure conditions, without silently limiting the guarantee to successful sessions.

**Non-observable or unfalsifiable property → finding rule `non-observable-property`. An unstable property → finding rule `unstable-property`.** Name the property and the context that breaks the guarantee; a stability finding requires evidence, and a criterion that cannot be evaluated is a finding on this unit naming the missing evidence.

</property>

<property name="tag-validity">

Preserve Step 3's `missing-section` finding when the `## Verification` section is absent; an empty rule loop never clears it. If the section contains no rules, record `missing-verification-rules` on this unit. An untagged rule directly under the section has the canonical authoring form and may coexist with routed subsections. For every such rule, identify its subject, the observable condition it constrains, and a concrete observation that would violate it. A vague, ambiguous, or unfalsifiable rule is a finding with rule `invalid-draft-rule`: quote the rule with the missing or ambiguous criterion. For example, `ALWAYS: improve quality` fails because it names no observable condition. Select no evidence type or tag during these checks; an absent draft tag alone causes no finding.

A tagged rule requires its matching routed subsection. When `### Testing` contains rules: Use skill `spec-tree:test-evidence-standards` and load its assertion-type litmus. Apply that reference and the loaded foundation's assertion-type definitions to the declared claim and tag. If the required reference cannot load, record a blocking `test-standards-unavailable` finding on this unit. Judge declaration compatibility only; evidence completeness belongs to evidence auditing. Never invoke the mutating `/test` authoring workflow, select a replacement tag, or change the PDR during this audit.

For each routed rule:

1. The rule carries exactly one tag, and the tag is valid for its subsection:
   - under `### Testing` → one of `scenario`, `mapping`, `conformance`, `property`, `compliance`;
   - under `### Eval` → `([eval])` — the rule governs a skill, agent, or classifier whose output has a parseable contract;
   - under `### Audit` → `([audit])` — the rule governs a Spec Tree decision, spec, skill, or agent that admits no deterministic test or graded eval.
2. Under `### Testing`, the declared assertion type is compatible with the claim's quantifier and evidence shape under the loaded foundation and shared assertion-type litmus. A universal claim cannot carry `scenario`. Reject a declared type whose required domain or oracle contradicts the claim, citing the claim and the loaded criterion; do not choose among compatible types or require executable evidence for a declaration.

A rule earns a sound tag only when it is verifiable (a test, eval, or audit skill can determine pass/fail) and specific (two independent reviewers would agree on the verdict). An unverifiable or vague routed rule is a finding with rule `invalid-tag` even when the tag's syntax is valid; quote the rule and identify the missing observable condition or ambiguous criterion.

**A routed rule with a missing, unsupported, duplicate, or subsection-mismatched tag → finding rule `invalid-tag`. An assertion type that contradicts the claim's shape → finding rule `assertion-type-mismatch`.**

Apply content classification, property quality, voice, and consistency to draft and routed declarations alike. Approval establishes declaration quality only; it supplies no evidence result, implementation claim, or Passing state for an untagged rule.

</property>

<property name="atemporal-voice">

Check EVERY section for temporal language:

| Temporal (finding)                    | Atemporal (correct)                                |
| ------------------------------------- | -------------------------------------------------- |
| "We discovered that users ask for X"  | "Users value X"                                    |
| "Currently the product does X"        | "The product does X"                               |
| "After customer feedback, we decided" | "The product does X to meet customer expectations" |
| "The existing implementation lacks"   | (omit — PDR doesn't reference code)                |

**Any temporal language in any section → finding rule `temporal-language`.**

</property>

<property name="consistency">

Compare the PDR against the context Step 1 loaded:

1. **Product spec** — Does the PDR contradict the product's scope or assertions?
2. **Ancestor PDRs** — Does the PDR contradict constraints from PDRs higher in the tree?
3. **Sibling ADRs** — Does the PDR overlap with architecture concerns?

**Contradiction with the product spec or an ancestor PDR → finding rule `consistency-violation`.** Overlap with an ADR is a `content-misplacement` finding with severity `debt`, which rejects no run.

</property>

</step>

<step name="classify">

**Step 5: Classify and record**

Classify every finding per `${CLAUDE_SKILL_DIR}/references/touched-text.md`: a finding on touched text is recorded on its unit with the severity its catalog row declares; every other finding is standing, returned as a `filed` line, and recorded nowhere in the run.

Once judgment is complete, add the root unit first, because a run admits one root and every child names it, then one child unit per property, then each finding on touched text on the unit of the concern it names; a finding that names no child unit, such as `context-unavailable`, sits on the root. Every unit is `audited`, whether it holds or carries findings. Record per `<persistence_contract>`.

</step>

<step name="finish">

**Step 6: Finish and render**

Derive `rejected` when a `blocking` finding on touched text exists and `approved` otherwise, whatever standing findings exist. Run the finish and render commands:

```bash
spx verification run finish --verification-type audit --scope-type file --scope <path> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type file --scope <path> --run <token>
```

</step>

<persistence_contract>

Every unit carries `auditClass: spec` and `auditKind: pdr`, and its `subject` and `priorContext.changedFilePartition` are the PDR `<path>`. The root unit's `unitId` is `pdr:root:<path>`, it omits `parentUnitId`, and its concern partition is `pdr`. A property unit's `unitId` is `pdr:property:<property>:<path>` with `<property>` one of `content-classification`, `property-quality`, `tag-validity`, `atemporal-voice`, or `consistency`. Each child's `parentUnitId` is the root's `unitId`, and its concern partition is its property name.

A scope unit:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-child-only>",
  "auditClass": "spec",
  "auditKind": "pdr",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "<pdr-or-property>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-pdr",
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

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>`, and `--idempotency-key '<finding-key>'`, the finding key `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines as `<unitId>:<rule>`. Its payload names an accepted unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the plugin version `<request_contract>` retained in both version fields, and no `toolVersion`; `rule` is one identifier from `<rule_catalog>` in `${CLAUDE_SKILL_DIR}/references/pdr-evidence-model.md`, and `severity` is the severity that row declares; name no identifier outside that catalog.

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
  "location": "<section-or-property-text>",
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

Return the run token, the run file, and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `APPROVED` or `REJECTED` envelope and no restated findings. After the projection, return each standing finding as a `filed` line in the form `${CLAUDE_SKILL_DIR}/references/touched-text.md` gives, or `filed: none`.

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

**Failure 1: Approved a PDR full of architecture decisions**

Claude saw a well-structured PDR with a clear decision statement and a Verification section, and approved it. The decision statement said "The system uses PostgreSQL with row-level locking for concurrent session management." That is an architecture decision, not a product decision. Users don't care about PostgreSQL or row-level locking — they care that concurrent sessions work.

Why it failed: Claude treated structural completeness as proof of correct content classification.

How to avoid: Step 4 classifies every statement. "Would a user be able to determine this?" is the test.

**Failure 2: Accepted non-observable properties**

Claude saw "Product properties: Database connections are pooled with a maximum of 50 connections." This is an implementation detail observable only by a DBA, not by users. The PDR version would be "The product handles at least 500 concurrent users without degradation."

Why it failed: Claude treated an implementation detail measurable by a specialist as a guarantee observable by the product's users.

How to avoid: Step 4 asks "Is this falsifiable from the user's perspective?"

**Failure 3: Approved a universal claim tagged as a scenario**

Claude saw a `### Testing` rule "ALWAYS: every export conforms to RFC 4180 ([scenario])" and approved it because the prose read like a concrete interaction. `ALWAYS` is a universal claim, and a single scenario cannot establish a claim about every case — the tag should be `mapping`, `conformance`, `property`, or `compliance`. The mismatch is `assertion-type-mismatch`, not `invalid-tag`.

How to avoid: Step 4 reads the quantifier first. A universal (ALWAYS / NEVER / "for all" / "no input") tagged `scenario` is `assertion-type-mismatch`; a structural tag problem — bare mechanism tag, wrong subsection, missing tag, more than one tag — is `invalid-tag`.

**Failure 4: Flagged a tooling product's observable state as architecture**

Claude audited a PDR for a command-line tool whose product document declares its audience operates the product through a CLI and an on-disk layout. The PDR described the repository layout the audience inspects on disk and the version-control state it observes. Claude saw git commands and filesystem paths, applied the end-user-application reflex ("a user does not see git"), and rejected the statements as `architecture-content`. That is a false positive: the declared audience operates exactly that surface, so the layout is observable product behavior.

How to avoid: Step 4 reads the product document's declared audience first and judges "observable" against it. A git topology, a path layout, or a CLI behavior the audience operates is product behavior. Reserve `architecture-content` for what the audience never operates — the tool's internal algorithm, in-memory data structures, persisted schema, and library choices — which stays an ADR concern even for a tooling product.

**Failure 5: Loaded context through the synchronizing skills**

Claude invoked `/contextualize` to load the PDR's context, and its `/sync-base` step rebased or advanced the checkout under the audit, so the head the audit judged differed from the head it started on. Load context with the read-only steps of Step 1 and never invoke either skill.

</failure_modes>

<success_criteria>

- The run holds one `audited` root unit for the PDR and one `audited` child unit for each of `content-classification`, `property-quality`, `tag-validity`, `atemporal-voice`, and `consistency`, with every PDR rule judged and none skipped.
- Every recorded finding lies on touched text and sits on an accepted unit, and names the section, the violated rule, and the evidence — the architecture content wrongly placed, the non-observable, unfalsifiable, or unstable property, the absent verification section or rules, the unverifiable rule or mismatched tag, the temporal phrase, or the contradicted product spec or ancestor PDR.
- Every standing finding appears as a `filed` line carrying its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- An absent or empty Verification section yields a finding on `tag-validity` and an unmet property-quality criterion a finding on `property-quality`; neither condition can disappear through an empty iteration or finish `approved`.
- The checkout the audit judged is the checkout it started on and left, so the verdict describes one head.
- The same PDR, context, and base yield the same units, finding keys, and terminal status.
- The reported terminal status is the run's own, unaltered, and each standing finding is reported outside the run, so the verdict neither hides nor inflates a finding.

</success_criteria>
