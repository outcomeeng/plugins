---
name: audit-adr
description: >-
  ADR audit methodology — judges one ADR against the ADR evidence model,
  covering section structure, atemporal voice, and per-rule tag validity, and
  records the judgment as a root unit with one child unit per property and
  composed language concern in an SPX file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Write, Bash(spx verification run:*), Bash(git merge-base:*), Bash(git diff:*), {{! tool('use_skill') !}}
---

<objective>

A sealed `spx verification run` on one ADR file, with one root scope unit for the ADR and one child scope unit per evidence-model property (section structure, atemporal voice, tag validity) and per composed language concern, whose verdict records every finding on touched text on its child unit, returned as the run token, the run file, and the rendered projection, whose `terminalStatus` is `approved` or `rejected`, followed by each other finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

</objective>

<constraints>

**ARCHITECTURE BY DEFINITION.**

An ADR's content is architecture — technology choices, data structures, implementation approaches. NEVER classify ADR content as product-behavior-versus-architecture; that classification is the PDR audit's concern. Audit the ADR's form, not whether its content belongs elsewhere.

**ASSERTION TYPE MUST MATCH THE CLAIM.**

Apply the canonical template's authoring and routed forms. Untagged rules directly under `## Verification` await selection and may coexist with routed subsections; judge their specificity, structure, voice, and consistency without inventing a missing-tag finding. Rules inside routed subsections carry the template's required tag. `/verify` selects the verification type, then `/test` selects a Testing rule's assertion type. A universal claim is never `scenario`; a missing required tag inside a routed subsection, unsupported tag, duplicate tag, or quantifier mismatch remains a finding. Approval judges declaration quality and establishes no evidence result or Passing state.

**ATEMPORAL VOICE.**

ADRs state architecture truth. "The build emits one wheel per plugin" — not "We switched to per-plugin wheels because the monolith broke."

**LANGUAGE COMPOSITION BOUNDARY.**

Language-specific ADR concerns — testability-in-Verification (dependency injection, no-mocking), execution-level accuracy — are composed from `/audit-<lang>-architecture` in `compose_language`. The language skill judges only those concerns; this skill owns section structure, atemporal voice, and tag validity from the canonical template.

- NEVER modify the ADR under audit or any other product file — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `product-tree:contextualize` or `product-tree:sync-base`, and never fetch, rebase, or otherwise move the checkout — the audit reads the head as it stands, so it changes no checkout state.
- ALWAYS derive the valid section set from the canonical ADR template before judging structure — never from memory.
- ALWAYS name the section, the violated rule, and the evidence in every finding — the author repairs from the finding alone, and an unanchored finding leaves nothing to repair.
- NEVER issue a finding the cited rule or canonical template does not support — drop an unbacked finding rather than reject the ADR for it.
- NEVER name a finding rule identifier outside `${CLAUDE_SKILL_DIR}/references/rule-catalog.md` or the catalog of a validated composed skill.
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

`$ARGUMENTS` is a JSON object with exactly two fields. `path` is the product-relative path of the ADR to audit. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing, extra, or malformed field, or a `path` that names no ADR file, returns `BLOCKED` naming the exact field or path before any command runs.

Use skill `product-tree:product-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that `<persistence_contract>` records in a finding's `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<execution_sequence>

<step name="load_context">

**Step 1: Load context read-only**

When the live `<PRODUCT_TREE_FOUNDATION>` marker is absent or lacks `Template root`: Use skill `product-tree:understand`. Read `decisions/decision-name.adr.md` beneath that marker's resolved absolute template directory. The template remains owned by `/understand`.

Load the ADR's context by reading, in this order, and starting no audit phase before every read completes:

1. the product document at `spx/`;
2. at each directory from `spx/` down to the directory containing the ADR, that directory's spec, then every decision record (`*.adr.md`, `*.pdr.md`) in it, excluding the ADR under audit;
3. every decision a loaded spec or decision cites by full `spx/` path, repeating for each newly read decision until none is unread; a citation to a missing decision file is a `BLOCKED` result naming the citation and the citing file.

Derive the ADR's governing node from its containing directory, using `spx/` for a product-root ADR. The committed changeset is resolved in `compose_language` and classified in `classify`. The input is the ADR path alone; no supplied language classification is required.

Do not proceed without the canonical ADR template content and the loaded context.

</step>

<step name="read_adr">

**Step 2: Read the ADR**

Read the ADR under audit completely. Identify its sections: the opening decision statement, Rationale (optional), Invariants (optional), and Verification.

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

Use the canonical ADR template guidance loaded in Step 1 to derive the valid section set in full — never from memory or a transcribed copy. A structural finding that contradicts the canonical template is unbacked: drop it. If the template guidance cannot be loaded, finding `template-missing` names the blocked read.

Verify the decision is stated in the opening (no "Purpose" preamble) and a `## Verification` section is present. Rationale and Invariants are optional — Invariants appears only when the decision establishes algebraic properties.

No decision statement, or no Verification section → finding `missing-section`.

</step>

<step name="audit_voice">

**Step 5: Atemporal voice**

Check EVERY section for temporal language:

| Temporal                              | Atemporal (correct)             |
| ------------------------------------- | ------------------------------- |
| "We decided to use X because Y broke" | "X governs Z"                   |
| "Currently the build does X"          | "The build does X"              |
| "After profiling, we added caching"   | "Caching reduces latency for Z" |

Any temporal language in any section → finding `temporal-voice`.

</step>

<step name="audit_tag_validity">

**Step 6: Per-rule tag validity and assertion-type fit**

Read each rule's placement before judging tags. An untagged rule directly under `## Verification` has the canonical authoring form. For every such rule, identify its subject, the condition it constrains, and a concrete observation that would violate it. A vague, ambiguous, or unfalsifiable rule is finding `invalid-draft-rule`, quoting the rule with the missing or ambiguous criterion. For example, `ALWAYS: improve quality` fails because it names no observable condition. Check each draft rule against the decision statement and governing decisions; a contradiction is also `invalid-draft-rule`, citing both conflicting declarations. Select no evidence type or tag during these checks.

A tagged rule must have the matching routed subsection. When `### Testing` contains rules: Use skill `product-tree:test-evidence-standards`. Load its assertion-type litmus. Apply that reference and the loaded foundation's assertion-type definitions to the declared claim and tag. If the required reference cannot load, finding `test-standards-unavailable` names the blocked load. Judge declaration compatibility only; evidence completeness belongs to evidence auditing. Never invoke the mutating `/test` authoring workflow, select a replacement tag, or change the ADR during this audit.

For each routed rule:

1. The tag is valid for its subsection:
   - under `### Testing` → one of `scenario`, `mapping`, `conformance`, `property`, `compliance`;
   - under `### Eval` → `([eval])`;
   - under `### Audit` → `([audit:{rule-slug}])` whose slug no other `### Audit` rule in the ADR repeats, or the pathless `([audit])` that the loaded foundation admits for a toolchain without slug support.
2. Under `### Testing`, the declared assertion type is compatible with the claim's quantifier and evidence shape under the loaded foundation and the litmus. A universal claim cannot carry `scenario`. Reject a declared type whose required domain or oracle contradicts the claim, citing the claim and the loaded criterion; do not choose among compatible types or require executable evidence for a declaration.

A missing tag inside a routed subsection, an unsupported bare mechanism tag, a tag disagreeing with its subsection, more than one tag, or an `### Audit` slug that repeats within the ADR → finding `invalid-tag`. An assertion type that contradicts the claim's shape → finding `assertion-type-mismatch`.

</step>

<step name="compose_language">

**Step 7: Compose language-specific architecture concerns**

Classify the ADR from its governed implementation surface and the committed changeset: run `git merge-base HEAD origin/HEAD` for the base, then `git diff --name-only <base>` for the changed paths. When the decision constrains no implementation language, classify it as language-neutral and skip composition. Otherwise preserve every implementation-language partition the decision constrains, including cross-language decisions; the repository's predominant language never narrows that set.

For every discovered partition: Use skill `{lang}:audit-{lang}-architecture`. Pass the ADR path. When a language-specific ADR has no reliable partition, finding `language-routing-unavailable` is recorded; when the required skill cannot load, finding `language-skill-unavailable` is recorded for that partition.

Before consuming a composed result, validate it against the invoked skill's declared verdict contract: the schema and skill identity, matching target, every required concern row exactly once, allowed statuses, required finding fields, explanations for `NOT_APPLICABLE`, and agreement between the rows and overall result. An absent, malformed, incomplete, mismatched, or inconsistent result is finding `language-result-invalid`, identifying the failed contract check; accept no partial rows from that result. This boundary validates returned structure without repeating the language audit's judgment.

Each validated row becomes one child unit qualified by its language, `<lang>:<row-name>`. Map its findings to this run's fields: retain the rule, message, observed, and expected evidence, and use the child location or file as a `;`-separated `location`. A composed `FAIL` row carries its findings, and a composed `blocking` finding rejects the ADR only on touched text, like any native finding.

One case is not a composition failure. When the governed context establishes that the changeset itself ships the ADR's language plugin, unpublished and uninstalled in this session, no `audit-<lang>-architecture` skill can exist yet. Judge the decision directly against the skill files its rules name and the cross-language decisions, and record a unit `language-skill-unpublished` as `not-applicable` with the evidence establishing that case in the `not-applicable` line `<verdict_format>` gives. An absent installed skill alone never establishes unpublished status.

</step>

<step name="classify">

**Step 8: Classify**

Resolve the base and run the diff commands as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, and sort every finding, native or composed, into touched text or standing text.

</step>

<step name="record">

**Step 9: Record**

Add the root scope unit first, because a run admits one root and every child names it, then one child scope unit per property and per composed language concern, then each finding on touched text on its child unit, per `<persistence_contract>`. Every unit for a concern that applies is `audited` whether it holds or carries findings; a composed row the language skill marked `NOT_APPLICABLE` is `not-applicable`. A standing finding is recorded nowhere in the run.

</step>

<step name="finish">

**Step 10: Finish**

Derive `rejected` when a finding on touched text exists and `approved` otherwise, whatever standing findings exist. Run the finish and render commands:

```bash
spx verification run finish --verification-type audit --scope-type file --scope <path> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type file --scope <path> --run <token>
```

</step>

</execution_sequence>

<persistence_contract>

Add a scope unit with `spx verification run scope add --verification-type audit --scope-type file --scope <path> --run <token> --payload <payload-file> --idempotency-key '<unitId>'`, the payload file written per `<payload_files>`. The root unit's `unitId` is the audited `<path>`, its concern partition is `adr`, and it omits `parentUnitId`; the run admits one root. Each child unit's `unitId` is `adr:<designator>:<path>` and its `parentUnitId` is the root's `unitId`. The designator is `section-structure`, `atemporal-voice`, or `tag-validity` for a property, and the qualified row name `<lang>:<row-name>` for a composed language concern. A recorded language-routing, skill, or result failure takes the designator `language-routing` for the first, and `<lang>:language-skill` or `<lang>:language-result` for the others. The class `spec` and kind `adr` are the pair `spx` accepts for an ADR subject.

The root unit:

```json
{
  "unitId": "<path>",
  "auditClass": "spec",
  "auditKind": "adr",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "adr"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-adr",
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

A child unit carries the same fields with `unitId` `adr:<designator>:<path>`, `parentUnitId` `<path>`, `coverageStatus` `audited` or `not-applicable`, and `priorContext.concernPartition` the designator:

```json
{
  "unitId": "adr:<designator>:<path>",
  "parentUnitId": "<path>",
  "auditClass": "spec",
  "auditKind": "adr",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "<audited-or-not-applicable>",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "<designator>"
  },
  "expectedProducer": "<the root unit's expectedProducer object, repeated exactly>",
  "recordedByRunDriver": "<the root unit's recordedByRunDriver object, repeated exactly>"
}
```

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>` per `<payload_files>`, and `--idempotency-key '<unitId>:<rule>'`, the finding key `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines. Its payload names an accepted child unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the plugin version `<request_contract>` retained in both version fields, and no `toolVersion`; `rule` is an identifier from `${CLAUDE_SKILL_DIR}/references/rule-catalog.md` or a validated composed catalog, and `location` lists every section or rule text where that rule is violated, separated by `;`.

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
  "location": "<section-or-rule-text>[; <further-location>...]",
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

Return the run token, the run file, and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `APPROVED` or `REJECTED` envelope and no restated findings. After the projection, return one line per `not-applicable` unit as `not-applicable: <unitId> | explanation: <why the concern does not apply>`, then each standing finding on its own line in the form `${CLAUDE_SKILL_DIR}/references/touched-text.md` gives, or `filed: none`.

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

**Failure 1: Claude imported the PDR content gate into an ADR audit.** Claude flagged "uses PostgreSQL with row-level locking" as architecture content that does not belong — in an ADR. An ADR's content is architecture by definition; there is no product-versus-architecture classification to run. The ADR audit checks form — structure, voice, tag validity — and content classification is the PDR audit's concern only.

**Failure 2: Claude passed a universal rule tagged `scenario`.** Claude saw a `### Testing` rule — a universal ALWAYS/NEVER claim — tagged `([scenario])`, and passed it because a tag was present and named one of the five assertion types. A scenario proves one case; it cannot establish a claim about every case, so the assertion ships unverified. Step 6 applies the `product-tree:test-evidence-standards` litmus and the loaded foundation's definitions: a universal tagged `scenario`, and any type those definitions would not admit for the claim, is a finding. Choosing between equally valid types belongs to `/test`, and this audit never relitigates it.

**Failure 3: Claude applied routed tag requirements to authoring declarations.** Claude rejected untagged authoring rules because the routed-form tag requirement was applied before verification selection. Derive the form from the artifact and canonical template. Judge every draft rule, preserve routed-rule checks, and never interpret declaration approval as evidence completeness.

**Failure 4: Claude rejected the run on a defect in text the changeset left alone.** Claude found a real violation in an unchanged ADR passage and recorded it on the unit, so the run rejected a changeset that did not cause the defect. Classify each finding by its location, record only findings on touched text, and return every other finding as `filed`.

**Failure 5: Claude moved the checkout while loading context.** Claude ran the context loader that rebases the audited branch, so the head under audit was replaced by another commit. Load the context by reading files at the head as it stands.

</failure_modes>

<success_criteria>

- The run holds one `audited` root scope unit for the ADR and one child unit under its key for each of section structure, atemporal voice, and tag validity, plus one per composed language concern, and every unit names the root.
- Every ADR rule was judged with none skipped — section structure, atemporal voice, and per-rule tag validity and assertion-type fit; when a language is in scope, the composed `/audit-<lang>-architecture` rows are judged too.
- Every recorded finding lies on touched text and sits on an accepted unit, is keyed by an identifier from a catalog, names the section, the violated rule, and observed-versus-expected evidence.
- Every standing finding appears as a `filed` line carrying its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- The `terminalStatus` is `rejected` exactly when a finding on touched text is recorded and `approved` otherwise, whatever standing findings exist.
- The checkout's head is the same before and after the audit.
- The same ADR, context, and base yield the same units, finding keys, and terminal status.

</success_criteria>
