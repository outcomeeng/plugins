---
name: audit-adr
description: >-
  ADR audit methodology — judges one ADR against the ADR evidence model,
  covering section structure, atemporal voice, and per-rule tag validity, and
  records the judgment as one root unit and one child unit per property and
  composed language concern in an SPX file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Write, Bash(spx verification run:*), Bash(git merge-base:*), Bash(git diff:*)
---

<objective>

A sealed `spx verification run` judging one ADR against the ADR evidence model, with one root unit for the ADR and one child unit per evidence-model property (`section-structure`, `atemporal-voice`, `tag-validity`) and per composed language concern, every finding on touched text recorded on its unit, returned as the run token, the run file, and the rendered projection, whose `terminalStatus` is `approved` or `rejected`, followed by each other finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

</objective>

<constraints>

**ARCHITECTURE BY DEFINITION.**

An ADR's content is architecture — technology choices, data structures, implementation approaches. NEVER classify ADR content as product-behavior-versus-architecture; that classification is the PDR audit's concern. Audit the ADR's form, not whether its content belongs elsewhere.

**ASSERTION TYPE MUST MATCH THE CLAIM.**

Apply the canonical template's authoring and routed forms. Untagged rules directly under `## Verification` await selection and may coexist with routed subsections; judge their specificity, structure, voice, and consistency without inventing a missing-tag finding. Rules inside routed subsections carry the template's required tag. `/verify` selects the verification type, then `/test` selects a Testing rule's assertion type. A universal claim is never `scenario`; a missing required tag inside a routed subsection, unsupported tag, duplicate tag, or quantifier mismatch remains a finding. Approval judges declaration quality and establishes no evidence result, no Passing state, and no compliance of the governed implementation.

**ATEMPORAL VOICE.**

ADRs state architecture truth. "The build emits one wheel per plugin" — not "We switched to per-plugin wheels because the monolith broke."

**BINARY OUTCOME.**

The run finishes `approved` or `rejected`. An unavailable required inspection is a finding on the unit it blocks, so the run finishes `rejected`; it never becomes an approval through an unevaluated unit.

**LANGUAGE COMPOSITION BOUNDARY.**

Language-specific ADR concerns — testability-in-Verification (dependency injection, no-mocking), execution-level accuracy — are composed from `/audit-<lang>-architecture` in Step 5. The language skill judges only those concerns; this skill owns section structure, atemporal voice, and tag validity from the canonical template.

- NEVER modify the ADR under audit or any other product file — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `/contextualize` or `/sync-base`: both can move the checkout, and this audit leaves the checkout unmoved. Step 1 loads the ADR's context read-only.
- ALWAYS derive the valid section set from the canonical ADR template before judging structure — never from memory.
- ALWAYS name the section, the violated rule, and the evidence in every finding.
- NEVER issue a finding the cited rule or canonical template does not support — drop an unbacked finding rather than reject the ADR for it.
- NEVER reject on text the changeset leaves unchanged and does not invalidate — return that finding as `filed`, and NEVER raise a recorded finding's severity or let a `filed` finding start to reject unless the run names a changed basis. `${SKILL_DIR}/references/touched-text.md` defines touched text, the finding key, and the `filed` line.
- ALWAYS persist audit state through `spx verification run`, started before any judgment; NEVER use markdown comments, tracked files, or a hand-formatted verdict as audit state.
- ALWAYS write each payload as one rendered JSON object to its own file and pass the file by path as `<payload_files>` states; NEVER send a payload through a heredoc, a pipe, or an inline argument, build one with an interpreter or `printf` stage, or repair one through command substitution or post-hoc text substitution.
- ALWAYS issue each `spx verification run` mutation as its own command and wait for its exit before the next one — parallel writes race sequence assignment and corrupt the sealed journal.
- NEVER retry a rejected command with a rewritten payload; the first command that exits nonzero ends the audit with `BLOCKED`.

</constraints>

<audit_workflow>

<request_contract>

`$ARGUMENTS` is a JSON object with exactly two fields. `path` is the product-relative path of the ADR to audit, spaces preserved. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing, extra, or malformed field, or an empty `path`, returns `BLOCKED` with run token `not-started` naming the exact field before any command runs.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that `<persistence_contract>` records in `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<step name="load_context">

**Step 1: Load context read-only**

Invoke `/understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent or lacks `Template root`. Read `decisions/decision-name.adr.md` beneath that marker's resolved absolute template directory. The template remains owned by `/understand`.

Load the ADR's context with `Read`, `Glob`, and `Grep` alone, in this order:

1. The product spec.
2. Each spec and every decision record in each directory on the path from `spx/` to the directory containing the ADR, root first. A product-root ADR has `spx/` alone on that path. The ADR under audit is excluded.
3. Every decision that a loaded spec or decision cites by full `spx/` path, each read once.

Derive the ADR's governing node from its containing directory, using canonical `spx/` for a product-root ADR. Resolve the base as `${SKILL_DIR}/references/touched-text.md` states; the base and the working tree supply the changeset paths Step 5 reads.

A decision that a loaded record cites and that cannot be read is a `context-unavailable` finding on the root unit, recorded in Step 6. Do not proceed without the canonical ADR template content and the live `<SPEC_TREE_FOUNDATION>` marker.

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

<step name="read_adr">

**Step 3: Read the ADR**

Read the ADR under audit. Identify its sections: the opening decision statement, Rationale (optional), Invariants (optional), and Verification. An absent or unreadable target returns `BLOCKED` with the exact failure.

Resolve the touched text of the ADR as `${SKILL_DIR}/references/touched-text.md` states, so Steps 4 and 5 can classify each finding.

</step>

<step name="audit_structure">

**Step 4: Judge section structure, atemporal voice, and tag validity, in that order**

<property name="section-structure">

Use the canonical ADR template guidance loaded in Step 1 to derive the valid section set in full — never from memory or a transcribed copy. A structural finding that contradicts the canonical template is unbacked: drop it rather than rejecting the ADR. If the template guidance cannot be loaded, record `template-missing` on the `section-structure` unit and name the blocked read.

Verify the decision is stated in the opening (no "Purpose" preamble) and a `## Verification` section is present. Rationale and Invariants are optional — Invariants appears only when the decision establishes algebraic properties.

**No decision statement, or no Verification section → finding rule `missing-section`.**

</property>

<property name="atemporal-voice">

Check EVERY section for temporal language:

| Temporal (finding)                    | Atemporal (correct)             |
| ------------------------------------- | ------------------------------- |
| "We decided to use X because Y broke" | "X governs Z"                   |
| "Currently the build does X"          | "The build does X"              |
| "After profiling, we added caching"   | "Caching reduces latency for Z" |

**Any temporal language in any section → finding rule `temporal-voice`.**

</property>

<property name="tag-validity">

Read each rule's placement before judging tags. An untagged rule directly under `## Verification` has the canonical authoring form. For every such rule, identify its subject, the condition it constrains, and a concrete observation that would violate it. A vague, ambiguous, or unfalsifiable rule is a finding with rule `invalid-draft-rule`: quote the rule with the missing or ambiguous criterion. For example, `ALWAYS: improve quality` fails because it names no observable condition. Check each draft rule against the decision statement and governing decisions; a contradiction also produces `invalid-draft-rule`, citing both conflicting declarations. Select no evidence type or tag during these checks.

A tagged rule must have the matching routed subsection. When `### Testing` contains rules, invoke `spec-tree:test-evidence-standards` and load its assertion-type litmus. Apply that reference and the loaded foundation's assertion-type definitions to the declared claim and tag. If the required reference cannot load, record a blocking `test-standards-unavailable` finding on the `tag-validity` unit. Judge declaration compatibility only; evidence completeness belongs to evidence auditing. Never invoke the mutating `/test` authoring workflow, select a replacement tag, or change the ADR during this audit.

For each routed rule:

1. The tag is valid for its subsection:
   - under `### Testing` → one of `scenario`, `mapping`, `conformance`, `property`, `compliance`;
   - under `### Eval` → `([eval])`;
   - under `### Audit` → `([audit])`.
2. Under `### Testing`, the declared assertion type is compatible with the claim's quantifier and evidence shape under the loaded foundation and shared assertion-type litmus. A universal claim cannot carry `scenario`. Reject a declared type whose required domain or oracle contradicts the claim, citing the claim and the loaded criterion; do not choose among compatible types or require executable evidence for a declaration.

An unsupported bare mechanism tag, a tag disagreeing with its subsection, a missing tag inside a routed subsection, more than one tag, or an assertion type that contradicts the claim's shape is invalid.

**A routed rule with a missing, unsupported, duplicate, or subsection-mismatched tag → finding rule `invalid-tag`. An assertion type that contradicts the claim's shape → finding rule `assertion-type-mismatch`.**

</property>

</step>

<step name="compose_language">

**Step 5: Compose language-specific architecture concerns**

This skill owns section structure, atemporal voice, and tag validity from the canonical template. Language-specific architecture concerns — dependency injection, no-mocking, execution-level accuracy — are owned by the language audit skill, not by this one.

Classify the ADR from its governed implementation surface and the changeset paths Step 1 resolved. When the decision constrains no implementation language, classify it as language-neutral and skip composition. Otherwise preserve every implementation-language partition the decision constrains, including cross-language decisions; the repository's predominant language never narrows that set.

For every discovered partition: Use skill `{lang}:audit-{lang}-architecture`. Pass the ADR path. The language skill judges only language-specific concerns and never re-judges section structure, voice, or tags. When a language-specific ADR has no reliable partition or the required skill cannot load, record a blocking `language-routing-unavailable` or `language-skill-unavailable` finding on that partition's unit, or on the root unit when no partition is reliable.

Before consuming a composed result, validate it against the invoked skill's declared verdict contract: the schema and skill identity, matching target, every required concern row exactly once, allowed statuses, required finding fields, explanations for `NOT_APPLICABLE`, and agreement between the rows and overall result. An absent, malformed, incomplete, mismatched, or inconsistent result produces a blocking `language-result-invalid` finding on that partition's unit, identifying the failed contract check; accept no partial concern coverage from that result. This boundary validates returned structure without repeating the language audit's judgment.

Consume only validated results. Each composed finding keeps the rule, message, observed, and expected evidence of the composed result and takes the child location or file as `location`. A composed finding is classified as Step 6 states, so a composed `FAIL` rejects the ADR only through a finding on touched text; no omitted row or empty result counts as passing coverage.

One case is not a composition failure. When the governed context establishes that the changeset itself ships the ADR's language plugin, unpublished and uninstalled in this session, no `audit-<lang>-architecture` skill can exist yet. Judge the decision directly against the skill files its rules name and the cross-language decisions, record the partition's unit `audited` with no finding, and return the evidence establishing that case as a `not-applicable` line named `language-skill-unpublished`. An absent installed skill alone never establishes unpublished status.

</step>

<step name="classify">

**Step 6: Classify and record**

Classify every finding, native or composed, per `${SKILL_DIR}/references/touched-text.md`: a finding on touched text is recorded on its unit with severity `blocking`; every other finding is standing, returned as a `filed` line, and recorded nowhere in the run.

Once judgment is complete, add the root unit first, because a run admits one root and every child names it, then one child unit per property and per composed language partition, then each finding on touched text on the unit of the concern it names; a finding that names no child unit sits on the root. Every unit is `audited`, whether it holds or carries findings, and a concern judged `NOT_APPLICABLE` is returned as a `not-applicable` line. Record per `<persistence_contract>`.

</step>

<step name="finish">

**Step 7: Finish and render**

Derive `rejected` when a finding on touched text exists and `approved` otherwise, whatever standing findings exist. Run the finish and render commands:

```bash
spx verification run finish --verification-type audit --scope-type file --scope <path> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type file --scope <path> --run <token>
```

</step>

<persistence_contract>

Every unit carries `auditClass: spec` and `auditKind: adr`, and its `subject` and `priorContext.changedFilePartition` are the ADR `<path>`. The root unit's `unitId` is `adr:root:<path>`, it omits `parentUnitId`, and its concern partition is `adr`. A property unit's `unitId` is `adr:property:<property>:<path>` with `<property>` one of `section-structure`, `atemporal-voice`, or `tag-validity`; a composed language unit's `unitId` is `adr:language:<lang>:<path>`. Each child's `parentUnitId` is the root's `unitId`, and its concern partition is its property name or `language-<lang>`.

A scope unit:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-child-only>",
  "auditClass": "spec",
  "auditKind": "adr",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "<adr-or-property-or-language-lang>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-adr",
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

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>`, and `--idempotency-key '<finding-key>'`, the finding key `${SKILL_DIR}/references/touched-text.md` defines as `<unitId>:<rule>`. Its payload names an accepted unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the plugin version `<request_contract>` retained in both version fields, and no `toolVersion`; `rule` is the finding identifier. The native identifiers are `missing-section`, `temporal-voice`, `invalid-draft-rule`, `invalid-tag`, `assertion-type-mismatch`, `template-missing`, `test-standards-unavailable`, `context-unavailable`, `language-routing-unavailable`, `language-skill-unavailable`, and `language-result-invalid`; a validated composed finding retains the invoked skill's identifier.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<spec-tree-plugin-version>",
    "skillOwningPluginVersion": "<spec-tree-plugin-version>"
  },
  "rule": "<finding-identifier>",
  "severity": "blocking",
  "location": "<section-or-rule-text>",
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

Return the run token, the run file, and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `APPROVED` or `REJECTED` envelope and no restated findings. After the projection, return each standing finding as a `filed` line in the form `${SKILL_DIR}/references/touched-text.md` gives, or `filed: none`, then each `not-applicable` line in the form `not-applicable: <unit-key> | rule: <name> | evidence: <why the concern does not apply>`.

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

**Failure 1: Imported the PDR content gate into an ADR audit**

Claude flagged "uses PostgreSQL with row-level locking" as architecture content that does not belong — in an ADR. An ADR's content is architecture by definition; there is no product-versus-architecture classification to run. The PDR audit's content gate has no place here.

How to avoid: The ADR audit checks form — structure, voice, tag validity. Content classification is the PDR audit's concern only.

**Failure 2: Passed a universal rule tagged `scenario`**

Claude saw a `### Testing` rule — a universal ALWAYS/NEVER claim — tagged `([scenario])`, and passed it because a tag was present and named one of the five assertion types. A scenario proves one case; it cannot establish a claim about every case, so the assertion ships unverified — phantom green. The quantifier mismatch is a deterministic error, not a matter of taste.

How to avoid: Step 4 verifies the assertion type fits the claim's shape per the `/test` router. Reject a universal tagged `scenario` (and any type the router would not produce for the claim). The one line the audit does not cross is relitigating a choice the router leaves open between equally-valid types — that, and only that, is `/test`'s to decide.

**Failure 3: Applied routed tag requirements to authoring declarations**

Claude rejected untagged authoring rules because the routed-form tag requirement was applied before verification selection. Derive the form from the artifact and canonical template. Judge every draft rule, preserve routed-rule checks, and never interpret declaration approval as evidence completeness.

**Failure 4: Loaded context through the synchronizing skills**

Claude invoked `/contextualize` to load the ADR's context, and its `/sync-base` step rebased or advanced the checkout under the audit, so the head the audit judged differed from the head it started on. Load context with the read-only steps of Step 1 and never invoke either skill.

</failure_modes>

<success_criteria>

- Every ADR rule was judged with none skipped, and every unit the run holds is `audited`.
- Every recorded finding lies on touched text and sits on an accepted unit, names the section, the violated rule, and the evidence — the missing section, the temporal phrase, or the mismatched tag.
- Every standing finding appears as a `filed` line carrying its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- The terminal status is `rejected` exactly when a finding on touched text is recorded, so no standing finding and no unevaluated unit decides it.
- The checkout the audit judged is the checkout it started on and left, so the verdict describes one head.
- The same ADR, context, and base yield the same units, finding keys, and terminal status.
- The reported terminal status is the run's own, unaltered, and each standing finding and each inapplicable concern is reported outside the run, so the verdict neither hides nor inflates a finding.

</success_criteria>
