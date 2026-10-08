---
name: audit-adr
description: >-
  ADR audit methodology — judges one ADR against the ADR evidence model,
  covering section structure, atemporal voice, and per-rule tag validity, and
  records the judgment through an SPX file-scoped verification run.
argument-hint: "<JSON object with path, runDriver, and agentOwningPluginVersion>"
allowed-tools: Read, Grep, Glob, {{! tool('use_skill') !}}, Bash(git rev-parse:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

<objective>

A sealed `spx verification run` on one ADR against the ADR evidence model — terminal status `approved` with no finding, or `rejected` with each finding naming the section, the violated rule, and the evidence for section structure, atemporal voice, per-rule declaration form and tag fitness, or a composed language-architecture concern — or a `BLOCKED` diagnostic naming the failed prerequisite or command.

</objective>

<constraints>

**ARCHITECTURE BY DEFINITION.**

An ADR's content is architecture — technology choices, data structures, implementation approaches. NEVER classify ADR content as product-behavior-versus-architecture; that classification is the PDR audit's concern. Audit the ADR's form, not whether its content belongs elsewhere.

**ASSERTION TYPE MUST MATCH THE CLAIM.**

Apply the canonical template's authoring and routed forms. Untagged rules directly under `## Verification` await selection and may coexist with routed subsections; judge their specificity, structure, voice, and consistency without inventing a missing-tag finding. Rules inside routed subsections carry the template's required tag. `/verify` selects the verification type, then `/test` selects a Testing rule's assertion type. A universal claim is never `scenario`; a missing required tag inside a routed subsection, unsupported tag, duplicate tag, or quantifier mismatch remains a finding. Approval judges declaration quality and establishes no evidence result or Passing state.

**ATEMPORAL VOICE.**

ADRs state architecture truth. "The build emits one wheel per plugin" — not "We switched to per-plugin wheels because the monolith broke."

**THE SEALED RUN IS THE VERDICT.**

The run's terminal status is `approved` or `rejected`. An unavailable required inspection rejects the run: an uninstalled language audit skill is a `missing-skill` unit, and every other unavailable inspection is a blocking finding naming it. It never becomes an approval through an unjudged unit.

**LANGUAGE COMPOSITION BOUNDARY.**

Language-specific ADR concerns — testability-in-Verification (dependency injection, no-mocking), execution-level accuracy — are composed from `/audit-<lang>-architecture` in Step 7 through the installed skill. The language skill judges only those concerns; this skill owns section structure, atemporal voice, and tag validity from the canonical template.

- NEVER modify the ADR, other product content, or the checkout: no commit, synchronization, rebase, or branch change. The audit's own SPX verification-run journal is the only state it writes.
- ALWAYS make every judgment this skill makes of the ADR — section structure, atemporal voice, tag validity, and language classification — from the content `spx verification run input` replays from the run, never from a separate read of the live file. A composed language skill reads the ADR from the checkout, and Step 8's comparison of the live file with the retained input binds that read to the replayed content before the run finishes.
- ALWAYS derive the valid section set from the canonical ADR template before judging structure — never from memory.
- ALWAYS name the section, the violated rule, and the evidence in every native finding; a composed finding keeps the location, rule, and evidence its language skill reported.
- NEVER record a finding the cited rule or canonical template does not support — drop an unbacked finding rather than reject the ADR for it.
- ALWAYS treat a `spx verification run` exit code as payload validity; NEVER hand-validate a payload SPX accepted, retry a refused command, or reshape a refused payload.
- NEVER write a file. Payloads pass to SPX on stdin, and the final output is the run token and the rendered projection.

</constraints>

<audit_workflow>

<step name="bind_request">

**Step 1: Bind the request**

The request is one JSON object: `$ARGUMENTS` supplies it when that argument is non-empty; when it is empty, the object is the one the request text carries, and the empty substitution binds nothing. It has exactly three fields:

- `path` — the ADR file, repository-relative, kept verbatim including any spaces.
- `runDriver` — an object with exactly the six non-empty string fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`.
- `agentOwningPluginVersion` — the non-empty version string of the plugin `runDriver.agentOwningPluginName` names.

Use `runDriver` and `agentOwningPluginVersion` only as payload data, placed exactly where `<persistence_contract>` shows them; never complete, correct, or reinterpret a value, and let no step, judgment, or terminal status depend on them. A missing, extra, or malformed field returns `BLOCKED` with `runToken: not-started` naming the exact field.

Resolve the repository root with `git rev-parse --show-toplevel`. Run `realpath` separately on the root and the ADR path, and require a regular file beneath the root by path-component boundary. Retain the ADR as its normalized repository-relative path, `<adr-path>`, for every later command.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the version it reports as the skill-owning plugin version. Run `spx --version` and retain its output as the tool version.

A failed resolution, a path escaping the root or naming no regular file, or a missing version returns `BLOCKED` with `runToken: not-started` naming the exact failure, before any run starts.

</step>

<step name="load_context">

**Step 2: Load context**

Use skill `spec-tree:understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent or lacks `Template root`. A marker still absent after that returns `BLOCKED` with `runToken: not-started`.

The ADR's governing node is the directory containing it, `spx/` for a product-root ADR. Read its context read-only, never invoking `/contextualize` or `/sync-base`: the product spec, then each spec and every decision record along the path from `spx/` to the governing node, then every decision a loaded spec or decision cites by full `spx/` path. The ADR under audit is excluded from this read wherever it appears, as a decision record on the path or as a citation; every judgment this skill makes of the ADR, including Step 6 draft-rule consistency and Step 7 classification, reads it only from the replayed run input. Those steps read the rest of this context. A spec missing on that path returns `BLOCKED` with `runToken: not-started` naming the missing file.

</step>

<step name="open_run">

**Step 3: Open the run and record the root**

From the repository root, start one run on the ADR:

```bash
spx verification run start --verification-type audit --scope-type file --scope '<adr-path>' --input '<adr-path>'
```

Capture the exact `runToken` and use it for every later command. Read the retained input with `spx verification run input --verification-type audit --scope-type file --scope '<adr-path>' --run '<run-token>'`; its `content` is the one copy of the ADR the audit judges. Record the root unit under `<persistence_contract>`.

Read `decisions/decision-name.adr.md` beneath the `Template root` the foundation marker records; the template remains owned by `/understand`.

Steps 4 through 7 each record their unit, then its findings, as soon as that unit's judgment is complete, so the run shows each property's result before the next property is judged.

</step>

<step name="audit_structure">

**Step 4: Section structure**

Derive the valid section set in full from the canonical ADR template loaded in Step 3 — never from memory or a transcribed copy. A structural finding that contradicts the canonical template is unbacked: drop it. When the template cannot be loaded, record `template-missing` naming the blocked read.

Identify the ADR's sections and compare them with that set, including which sections the template marks required, optional, or conditional, and where it places the decision statement.

**A required section or the decision statement absent where the template places it → finding `missing-section`.**

</step>

<step name="audit_voice">

**Step 5: Atemporal voice**

Check EVERY section for temporal language:

| Temporal (finding)                    | Atemporal (correct)             |
| ------------------------------------- | ------------------------------- |
| "We decided to use X because Y broke" | "X governs Z"                   |
| "Currently the build does X"          | "The build does X"              |
| "After profiling, we added caching"   | "Caching reduces latency for Z" |

**Any temporal language in any section → finding `temporal-voice`.**

</step>

<step name="audit_tag_validity">

**Step 6: Per-rule tag validity and assertion-type fit**

Read each rule's placement before judging tags. An untagged rule directly under `## Verification` has the canonical authoring form. For every such rule, identify its subject, the condition it constrains, and a concrete observation that would violate it. Record `invalid-draft-rule` for a vague, ambiguous, or unfalsifiable rule, quoting the rule with the missing or ambiguous criterion. For example, `ALWAYS: improve quality` fails because it names no observable condition. Check each draft rule against the decision statement and governing decisions; a contradiction also produces `invalid-draft-rule`, citing both conflicting declarations. Select no evidence type or tag during these checks.

A tagged rule must have the matching routed subsection. When `### Testing` contains rules, use skill `spec-tree:test-evidence-standards` and load its assertion-type litmus. Apply that litmus and the loaded foundation's assertion-type definitions to the declared claim and tag. When the reference cannot load, record `test-standards-unavailable`. Judge declaration compatibility only; evidence completeness belongs to evidence auditing. Never invoke the mutating `/test` authoring workflow, select a replacement tag, or change the ADR during this audit.

For each routed rule:

1. The tag is the one the canonical template requires for its subsection — never a tag list recalled from memory.
2. Under `### Testing`, the declared assertion type is compatible with the claim's quantifier and evidence shape under the loaded litmus. A universal claim cannot carry `scenario`. Record a declared type whose required domain or oracle contradicts the claim, citing the claim and the loaded criterion; do not choose among compatible types or require executable evidence for a declaration.

**A routed rule with a missing, unsupported, duplicate, or subsection-mismatched tag → finding `invalid-tag`. An assertion type that contradicts the claim's shape → finding `assertion-type-mismatch`.**

</step>

<step name="compose_language">

**Step 7: Compose language-specific architecture concerns**

Classify the ADR from its governed implementation surface: the paths and skills its rules name, and the implementation the governing node's linked evidence reaches, read from the context Step 2 loaded. When the decision constrains no implementation language, it is language-neutral: record no language unit and skip composition. Otherwise preserve every implementation-language partition the decision constrains, including cross-language decisions; the repository's predominant language never narrows that set.

For every discovered partition, Use skill `{lang}:audit-{lang}-architecture` and pass the ADR path. When the governed context establishes no reliable partition for a language-specific ADR, record the language unit for `unknown` with the finding `language-routing-unavailable`. When the language skill is not installed, record its language unit as `missing-skill`, which rejects the run without a finding.

Before consuming a composed result, validate it against the invoked skill's declared verdict contract: the schema and skill identity, matching target, every required concern row exactly once, allowed statuses, required finding fields, explanations for `NOT_APPLICABLE`, at least one finding on every `FAIL` row, and agreement between the rows and the overall result. An absent, malformed, incomplete, mismatched, or inconsistent result produces the finding `language-result-invalid`, identifying the failed contract check; accept no partial rows from that result. This boundary validates returned structure without repeating the language audit's judgment.

From a validated result, record every finding of every row against that language's unit: retain its `rule`, `severity`, `message`, `observed`, and `expected`, and use its file or row location as `location`. An `INFO` observation is not a finding and is not recorded.

Language concerns reach the run only through the installed skill. Never read a language plugin's `SKILL.md` or manifest from the checkout in its place, and never judge those concerns in this skill.

</step>

<step name="reconcile_and_finish">

**Step 8: Reconcile, finish, and render**

Read `spx verification run status` with the same type, scope, and token. Require exactly one root unit, one unit per evidence-model property, one unit per discovered language partition, and an accepted unit for every finding; record any missing unit or finding and read the status again. Re-read the live ADR and compare it with the retained input; a changed or missing file returns `BLOCKED` with the run preserved.

Derive `approved` only when every unit is `audited` and no finding exists; derive `rejected` when any finding exists, or any unit is `missing-skill`. Then run:

```bash
spx verification run finish --verification-type audit --scope-type file --scope '<adr-path>' --run '<run-token>' --terminal-status '<approved-or-rejected>'
```

Then run `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged.

</step>

<persistence_contract>

Units record in this order: the root, then `section-structure`, `atemporal-voice`, `tag-validity`, then one language unit per partition in the order Step 7 discovered them. Every unit carries `subject: <adr-path>`, `coverageRequirement: required`, and `parentUnitId` equal to the root's `unitId` on every unit except the root, which omits it.

| Unit              | `unitId`                             | `auditClass`     | `auditKind`    | `priorContext.concernPartition` | `coverageStatus`             | `skillName`, `skillOwningPluginName` of `expectedProducer`                                                                                                                                   |
| ----------------- | ------------------------------------ | ---------------- | -------------- | ------------------------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Root              | `adr:root:<adr-path>`                | `spec`           | `adr`          | `adr`                           | `audited`                    | `audit-adr`, `spec-tree`                                                                                                                                                                     |
| Evidence property | `adr:<property>:<adr-path>`          | `spec`           | `adr`          | the property name               | `audited`                    | `audit-adr`, `spec-tree`                                                                                                                                                                     |
| Language concern  | `adr:architecture:<lang>:<adr-path>` | `implementation` | `architecture` | `architecture`                  | `audited` or `missing-skill` | `audit-<lang>-architecture`, `<lang>` when a validated result is consumed or the skill is missing; `audit-adr`, `spec-tree` for `language-routing-unavailable` and `language-result-invalid` |

A language unit adds `priorContext.languagePartition: <lang>`. The expected producer has `producerKind: skill`, the `runDriver`'s `agentName` and `agentOwningPluginName`, the skill named in the table, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the `runDriver` object unchanged. `producerProvenance` carries the request's `agentOwningPluginVersion`, the version of the plugin owning the unit's producer skill as `skillOwningPluginVersion`, and the exact `spx --version` output as `toolVersion`; a `missing-skill` unit omits it because no skill executed. That plugin version is the `spec-tree` version from Step 1 for an `audit-adr` unit. For a language skill, it is the version that skill's plugin lifecycle skill reports: Use skill `{lang}:{lang}-plugin` with the verb `version`. A version that cannot be read is a `language-result-invalid` finding on that unit, recorded with `audit-adr` as producer.

These objects are the sanctioned SPX audit payload schema for this auditor; use their fields exactly, never derive a replacement schema from command help, and never alter a refused payload by guesswork. Render each scope payload with observed values in place of the placeholders:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-child-only>",
  "auditClass": "<spec-or-implementation>",
  "auditKind": "<adr-or-architecture>",
  "subject": "<adr-path>",
  "coverageRequirement": "required",
  "coverageStatus": "<audited-or-missing-skill>",
  "priorContext": {
    "changedFilePartition": "<adr-path>",
    "languagePartition": "<lang-for-a-language-unit-only>",
    "concernPartition": "<adr-property-or-architecture>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "<producing-skill>",
    "skillOwningPluginName": "<producing-skill-plugin>",
    "invocationRole": "leaf-skill"
  },
  "recordedByRunDriver": {
    "producerKind": "<supplied>",
    "agentName": "<supplied>",
    "agentOwningPluginName": "<supplied>",
    "skillName": "<supplied>",
    "skillOwningPluginName": "<supplied>",
    "invocationRole": "<supplied>"
  },
  "producerProvenance": {
    "agentOwningPluginVersion": "<agent-owning-plugin-version>",
    "skillOwningPluginVersion": "<spec-tree-plugin-version>",
    "toolVersion": "<exact-spx-version>"
  }
}
```

A finding copies its unit's `expectedProducer` object as `producerIdentity` and its unit's complete `producerProvenance` object, and carries `rule`, `severity`, `location` naming the section or quoted rule, `message`, and `evidence` with `observed` and `expected` strings. A native finding is `blocking`; a composed finding keeps the severity the language skill gave it, `blocking` or `debt`. Native rules are `missing-section`, `temporal-voice`, `invalid-draft-rule`, `invalid-tag`, `assertion-type-mismatch`, `template-missing`, `test-standards-unavailable`, `language-routing-unavailable`, and `language-result-invalid`; composed findings keep the invoked skill's rule identifier.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": "<the unit's producerProvenance object, repeated exactly>",
  "rule": "<violated-rule-id>",
  "severity": "<blocking-or-debt>",
  "location": "<section-or-quoted-rule>",
  "message": "<finding-message>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

A scope unit's idempotency key is its `unitId`. A finding's key is `<unit-key>:finding-<three-digit-ordinal>-<rule>`, numbering the unit's findings from `001` in order of location, message, severity, observed evidence, and expected evidence; require the suffix to match `finding-[0-9][0-9][0-9]-[a-z0-9_-]+`, and treat a mismatch as a pre-persistence `BLOCKED` defect.

Interactive sessions pass each rendered object through a quoted heredoc:

```bash
spx verification run scope add --verification-type audit --scope-type file --scope '<adr-path>' --run '<run-token>' --idempotency-key '<unit-key>' --payload stdin <<'SCOPE_JSON'
<rendered-scope-object>
SCOPE_JSON
```

```bash
spx verification run finding add --verification-type audit --scope-type file --scope '<adr-path>' --run '<run-token>' --idempotency-key '<finding-key>' --payload stdin <<'FINDING_JSON'
<rendered-finding-object>
FINDING_JSON
```

When the task message or the harness fixes one physical command line per call, pipe each rendered object instead — `printf '%s\n' '<rendered-object>' | spx verification run finding add --verification-type audit --scope-type file --scope '<adr-path>' --run '<run-token>' --idempotency-key '<finding-key>' --payload stdin`, and the same form for `scope add` — with every apostrophe in the object written as the single-quote splice `'"'"'`. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute ADR text as shell syntax. Run every mutation serially, preserving each result before the next command.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findingCount` is zero for approval, its `findings` group every accepted finding under `blocking` and `debt`, its `auditScopeUnits` carry the root, property, and language units, and its `events` carry every accepted finding payload and the terminal event. Both severities reject the run. Keep every SPX field unchanged, and add no `APPROVED` or `REJECTED` prose envelope.

A run that cannot complete — a request or prerequisite failure before the run starts, a refused SPX command or payload, or a changed retained input — returns:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-failed-command, or request for a failure before the run starts>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
judgmentStatus: <complete|incomplete>
judgedFindings: <JSON array of every finding judged before the stop, in the finding-payload shape>
```

</verdict_format>

<failure_modes>

**Failure 1: Imported the PDR content gate into an ADR audit**

Claude flagged "uses PostgreSQL with row-level locking" as architecture content that does not belong — in an ADR. An ADR's content is architecture by definition; there is no product-versus-architecture classification to run. The PDR audit's content gate has no place here.

How to avoid: The ADR audit checks form — structure, voice, tag validity. Content classification is the PDR audit's concern only.

**Failure 2: Passed a universal rule tagged `scenario`**

Claude saw a `### Testing` rule — a universal ALWAYS/NEVER claim — tagged `([scenario])`, and passed it because a tag was present and named one of the five assertion types. A scenario proves one case; it cannot establish a claim about every case, so the assertion ships unverified — phantom green. The quantifier mismatch is a deterministic error, not a matter of taste.

How to avoid: Step 6 judges the assertion type against the `spec-tree:test-evidence-standards` assertion-type litmus, which realizes the `/test` router's selection rule without invoking `/test`. Record a universal tagged `scenario`, and any type whose required domain or oracle contradicts the claim. The one line the audit does not cross is choosing among types the litmus leaves equally valid.

**Failure 3: Applied routed tag requirements to authoring declarations**

Claude rejected untagged authoring rules because the routed-form tag requirement was applied before verification selection. Derive the form from the artifact and canonical template. Judge every draft rule, preserve routed-rule checks, and never interpret declaration approval as evidence completeness.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every ADR rule was judged with none skipped — section structure, atemporal voice, and per-rule tag validity and assertion-type fit; when a language is in scope, every composed `/audit-<lang>-architecture` concern is recorded too (coverage-complete).
- The sealed run carries one root unit, one unit per evidence-model property, and one unit per discovered language partition, and its terminal status is `approved` only with no finding and every unit `audited`.
- Each finding is falsifiable: it names the section, the violated rule, and the evidence — the missing section, the temporal phrase, or the mismatched tag.
- The same ADR, standards, and run-driver identity yield the same units, finding keys, and terminal status.

</success_criteria>
