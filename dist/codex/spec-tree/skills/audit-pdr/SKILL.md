---
name: audit-pdr
description: >-
  PDR audit methodology — judges one PDR against the PDR evidence model,
  covering content classification, property quality, per-rule tag validity,
  atemporal voice, and consistency with ancestor decisions, and records the
  judgment through an SPX file-scoped verification run.
argument-hint: "<JSON object with path, runDriver, and agentOwningPluginVersion>"
allowed-tools: Read, Grep, Glob, Bash(git rev-parse:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

<objective>

A sealed `spx verification run` on one PDR against the PDR evidence model — terminal status `approved` with no finding, or `rejected` with each finding naming the section, the violated rule, and the evidence for content classification, property quality, declaration form and tag fitness, atemporal voice, or consistency with the product spec and ancestor PDRs — or a `BLOCKED` diagnostic naming the failed prerequisite or command.

</objective>

<constraints>

Read the PDR evidence model's boundary guidance for content classification, property quality, and tag validity before auditing: `${SKILL_DIR}/references/pdr-evidence-model.md`

**PRODUCT BEHAVIOR, NOT ARCHITECTURE.**

PDRs govern what the product does, behavior that its users experience. "Sessions expire after 1 hour" is product behavior. "Sessions use JWT with 1-hour TTL" is architecture. If the content describes HOW something is built rather than WHAT users observe, it belongs in an ADR.

"Users" means the audience the product document declares, and "observe" means observe through the interaction surfaces that document names — not a fixed end-user-application assumption. When the product document declares an audience that operates the product through a command-line, filesystem, version-control, or other infrastructure surface, the CLI, filesystem, and version-control state that audience operates is product behavior; the internal algorithm, in-memory data structure, persisted schema, and library choices that audience never touches stay architecture.

**ATEMPORAL VOICE.**

PDRs state atemporal product truth without historical context. No references to past behavior or events.

**THE SEALED RUN IS THE VERDICT.**

The run's terminal status is `approved` or `rejected`. A property this audit cannot evaluate rejects the run through a blocking finding naming the missing evidence; it never becomes an approval through an unjudged unit.

- NEVER edit the PDR or other product content, and NEVER commit, stash, or create a branch. `/contextualize`'s base synchronization is the only checkout change the audit admits, and the audit's own SPX verification-run journal is the only state it writes.
- ALWAYS make every judgment of the PDR from the content `spx verification run input` replays from the run, never from the copy `/contextualize` loaded or a separate read of the live file. Step 8 compares the live file with the retained input before the run finishes.
- ALWAYS read the PDR evidence model and the canonical PDR template before judging — derive the rule set and the section set from them, never from memory.
- ALWAYS name the section, the violated rule, and the evidence in every finding.
- NEVER record a finding the cited rule does not support — drop an unbacked finding rather than reject the PDR for it.
- ALWAYS treat a `spx verification run` exit code as payload validity; NEVER hand-validate a payload SPX accepted, retry a refused command, or reshape a refused payload.
- NEVER write a file. Payloads pass to SPX on stdin, and the final output is the run token and the rendered projection.

</constraints>

<audit_workflow>

<step name="bind_request">

**Step 1: Bind the request**

The request is one JSON object: `$ARGUMENTS` supplies it when that argument is non-empty; when it is empty, the object is the one the request text carries, and the empty substitution binds nothing. It has exactly three fields:

- `path` — the PDR file, repository-relative, kept verbatim including any spaces.
- `runDriver` — an object with exactly the six non-empty string fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`.
- `agentOwningPluginVersion` — the non-empty version string of the plugin `runDriver.agentOwningPluginName` names.

Use `runDriver` and `agentOwningPluginVersion` only as payload data, placed exactly where `<persistence_contract>` shows them; never complete, correct, or reinterpret a value, and let no step, judgment, or terminal status depend on them. A missing, extra, or malformed field returns `BLOCKED` with `runToken: not-started` naming the exact field.

Resolve the repository root with `git rev-parse --show-toplevel`. Run `realpath` separately on the root and the PDR path, and require a regular file beneath the root by path-component boundary. Retain the PDR as its normalized repository-relative path, `<pdr-path>`, for every later command.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the version it reports as the skill-owning plugin version. Run `spx --version` and retain its output as the tool version.

A failed resolution, a path escaping the root or naming no regular file, or a missing version returns `BLOCKED` with `runToken: not-started` naming the exact failure, before any run starts.

</step>

<step name="load_context">

**Step 2: Load context**

Use skill `spec-tree:understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent or lacks `Template root`. A marker still absent after that returns `BLOCKED` with `runToken: not-started`.

Use skill `spec-tree:contextualize` on the directory containing the PDR — its canonical `spx/...` node path, or `spx/` for a product-root PDR. The audit authorizes no checkpoint commit: a `/contextualize` abort, or a base-synchronization result other than `already_current` or `rebased`, returns `BLOCKED` with `runToken: not-started` carrying that result's exact status and detail.

The product document is the product spec `/contextualize` loads. Steps 4 and 8 read its declared audience, interaction surfaces, and scope, and the ancestor PDRs and sibling ADRs it loads; they read the PDR under audit only from the replayed input.

</step>

<step name="open_run">

**Step 3: Open the run and record the root**

From the repository root, start one run on the PDR:

```bash
spx verification run start --verification-type audit --scope-type file --scope '<pdr-path>' --input '<pdr-path>'
```

Capture the exact `runToken` and use it for every later command. Read the retained input with `spx verification run input --verification-type audit --scope-type file --scope '<pdr-path>' --run '<run-token>'`; its `content` is the one copy of the PDR the audit judges. Record the root unit under `<persistence_contract>`.

Read `decisions/decision-name.pdr.md` beneath the `Template root` the foundation marker records; the template remains owned by `/understand`. When the template cannot be loaded, Step 6 records `template-missing` naming the blocked read.

Identify the PDR's sections against that template: the opening decision statement, Rationale, Product properties, and Verification.

Steps 4 through 8 each record their unit, then its findings, as soon as that unit's judgment is complete, so the run shows each property's result before the next property is judged.

</step>

<step name="audit_content">

**Step 4: Content classification**

Name the declared audience and the interaction surfaces through which that audience operates the product, from the product document. "Observable" is judged against that audience: a statement is product behavior when the declared audience observes or operates it. For a product whose audience operates a command-line, filesystem, version-control, or other infrastructure surface, the CLI commands, on-disk layout, and version-control state that audience runs and inspects are observable product behavior — not architecture. The architecture line falls at what the audience never operates: the internal algorithm by which a tool reaches an observable result, the in-memory data structures it holds, the schema it persists, and the libraries it depends on.

Then classify every statement in the PDR:

| Content type                       | Belongs in     | Finding if in PDR                         |
| ---------------------------------- | -------------- | ----------------------------------------- |
| Observable product behavior        | PDR            | None                                      |
| Observable non-functional property | PDR (property) | None                                      |
| Technology choice                  | ADR            | `architecture-content`                    |
| Implementation approach            | ADR or code    | `architecture-content`                    |
| Data structure or schema           | ADR            | `architecture-content`                    |
| Performance implementation         | ADR            | `architecture-content` (guarantee is PDR) |

The test: "Would the product document's declared audience observe or operate this?" If yes, it is product behavior. If only an implementer of the tool — never the audience — would know it, it belongs in an ADR. Do not flag a tooling product's CLI, filesystem, or version-control state as architecture merely because it names git, a path, or a command; that state is what its audience operates. Reserve `architecture-content` for the tool's internal algorithm, data structures, schema, and library choices.

**Any architecture or implementation content → finding `architecture-content`.**

</step>

<step name="audit_properties">

**Step 5: Property quality**

For each product property:

1. Is it observable from the user's perspective?
   - "Pages load in under 2 seconds" → observable ✓
   - "Database uses row-level locking" → not user-observable ✗
2. Is it falsifiable — is there a scenario where it's violated?
   - "Good user experience" → unfalsifiable ✗
   - "Search returns results in under 500ms" → falsifiable ✓
3. Is it stable — does its guarantee hold across all applicable contexts, including failure and boundary conditions, as the evidence model requires?
   - "Theme selection persists across sessions" → assess persistence across session boundaries and failure conditions, without silently limiting the guarantee to successful sessions.

**A non-observable or unfalsifiable property → finding `non-observable-property`. An unstable property → finding `unstable-property`.** Name the property and the context that breaks the guarantee. A criterion the PDR gives no evidence to evaluate → finding `evidence-unavailable` naming the missing evidence.

Untagged rules directly under `## Verification` have the canonical authoring form and are judged here. For every such rule, identify its subject, the observable condition it constrains, and a concrete observation that would violate it. **A vague, ambiguous, or unfalsifiable draft rule → finding `invalid-draft-rule`**, quoting the rule with the missing or ambiguous criterion. For example, `ALWAYS: improve quality` fails because it names no observable condition. Select no evidence type or tag during these checks; an absent draft tag alone causes no finding.

</step>

<step name="audit_verification">

**Step 6: Per-rule verification tag validity**

**An absent `## Verification` section → finding `missing-section`, naming the expected section. A section with no rules → finding `missing-verification-rules`.** Either finding stands even though no rule remains to iterate.

A tagged rule requires its matching routed subsection. When `### Testing` contains rules, use skill `spec-tree:test-evidence-standards` and load its assertion-type litmus. Apply that litmus and the loaded foundation's assertion-type definitions to the declared claim and tag. When the reference cannot load, record `test-standards-unavailable`. Judge declaration compatibility only; evidence completeness belongs to evidence auditing. Never invoke the mutating `/test` authoring workflow, select a replacement tag, or change the PDR during this audit.

For each routed rule:

1. The rule carries exactly one tag, and the tag is the one the canonical template requires for its subsection — never a tag list recalled from memory.
2. Under `### Testing`, the declared assertion type is compatible with the claim's quantifier and evidence shape under the loaded litmus. A universal claim cannot carry `scenario`. Record a declared type whose required domain or oracle contradicts the claim, citing the claim and the loaded criterion; do not choose among compatible types or require executable evidence for a declaration.

A rule earns a sound tag only when it is verifiable (a test, eval, or audit skill can determine pass/fail) and specific (two independent reviewers would agree on the verdict). An unverifiable or vague routed rule is `invalid-tag` even when the tag's syntax is valid; quote the rule and identify the missing observable condition or ambiguous criterion.

**A routed rule that is unverifiable, vague, or carries a missing, unsupported, duplicate, or subsection-mismatched tag → finding `invalid-tag`. An assertion type that contradicts the claim's shape → finding `assertion-type-mismatch`.**

Apply content classification, property quality, voice, and consistency to draft and routed declarations alike. Approval establishes declaration quality only; it supplies no evidence result, implementation claim, or Passing state for an untagged rule.

</step>

<step name="audit_voice">

**Step 7: Atemporal voice**

Check EVERY section for temporal language:

| Temporal (finding)                    | Atemporal (correct)                                |
| ------------------------------------- | -------------------------------------------------- |
| "We discovered that users ask for X"  | "Users value X"                                    |
| "Currently the product does X"        | "The product does X"                               |
| "After customer feedback, we decided" | "The product does X to meet customer expectations" |
| "The existing implementation lacks"   | (omit — PDR doesn't reference code)                |

**Any temporal language in any section → finding `temporal-language`.**

</step>

<step name="audit_consistency">

**Step 8: Consistency**

Compare the PDR against:

1. **Product spec** — Does the PDR contradict the product's scope or assertions?
2. **Ancestor PDRs** — Does the PDR contradict constraints from PDRs higher in the tree?
3. **Sibling ADRs** — Does the PDR restate a concern a sibling ADR governs?

**A contradiction with the product spec or an ancestor PDR → finding `consistency-violation`**, quoting both conflicting declarations. **A statement restating a sibling ADR's architecture concern → finding `content-misplacement`** with severity `debt`, quoting the statement and the ADR rule it restates.

</step>

<step name="reconcile_and_finish">

**Step 9: Reconcile, finish, and render**

Read `spx verification run status` with the same type, scope, and token. Require exactly one root unit, one unit per evidence-model property, and an accepted unit for every finding; record any missing unit or finding and read the status again. Re-read the live PDR and compare it with the retained input; a changed or missing file returns `BLOCKED` with the run preserved.

Derive `approved` only when every unit is `audited` and no finding exists; derive `rejected` when any finding exists. Then run:

```bash
spx verification run finish --verification-type audit --scope-type file --scope '<pdr-path>' --run '<run-token>' --terminal-status '<approved-or-rejected>'
```

Then run `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged.

</step>

<persistence_contract>

Units record in this order: the root, then `content-classification`, `property-quality`, `tag-validity`, `atemporal-voice`, and `consistency`. Every unit carries `subject: <pdr-path>`, `coverageRequirement: required`, `coverageStatus: audited`, and `parentUnitId` equal to the root's `unitId` on every unit except the root, which omits it.

| Unit              | `unitId`                    | `auditClass` | `auditKind` | `priorContext.concernPartition` |
| ----------------- | --------------------------- | ------------ | ----------- | ------------------------------- |
| Root              | `pdr:root:<pdr-path>`       | `spec`       | `pdr`       | `pdr`                           |
| Evidence property | `pdr:<property>:<pdr-path>` | `spec`       | `pdr`       | the property name               |

Every unit's expected producer has `producerKind: skill`, the `runDriver`'s `agentName` and `agentOwningPluginName`, `skillName: audit-pdr`, `skillOwningPluginName: spec-tree`, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the `runDriver` object unchanged. `producerProvenance` carries the request's `agentOwningPluginVersion`, the `spec-tree` version from Step 1 as `skillOwningPluginVersion`, and the exact `spx --version` output as `toolVersion`.

These objects are the sanctioned SPX audit payload schema for this auditor; use their fields exactly, never derive a replacement schema from command help, and never alter a refused payload by guesswork. Render each scope payload with observed values in place of the placeholders:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-child-only>",
  "auditClass": "spec",
  "auditKind": "pdr",
  "subject": "<pdr-path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<pdr-path>",
    "concernPartition": "<pdr-or-property-name>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "audit-pdr",
    "skillOwningPluginName": "spec-tree",
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

A finding copies its unit's `expectedProducer` object as `producerIdentity` and its unit's complete `producerProvenance` object, and carries `rule`, `severity`, `location` naming the section or quoted statement, `message`, and `evidence` with `observed` and `expected` strings. Each rule records against one unit:

| Unit                     | Rules                                                                                                                                       |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `content-classification` | `architecture-content`                                                                                                                      |
| `property-quality`       | `non-observable-property`, `unstable-property`, `evidence-unavailable`, `invalid-draft-rule`                                                |
| `tag-validity`           | `missing-section`, `missing-verification-rules`, `invalid-tag`, `assertion-type-mismatch`, `template-missing`, `test-standards-unavailable` |
| `atemporal-voice`        | `temporal-language`                                                                                                                         |
| `consistency`            | `consistency-violation`, `content-misplacement`                                                                                             |

Every finding is `blocking` except `content-misplacement`, which is `debt`; both severities reject the run. An observation that names no defect is not a finding and is not recorded.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": "<the unit's producerProvenance object, repeated exactly>",
  "rule": "<violated-rule-id>",
  "severity": "<blocking-or-debt>",
  "location": "<section-or-quoted-statement>",
  "message": "<finding-message>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

A scope unit's idempotency key is its `unitId`. A finding's key is `<unit-key>:finding-<three-digit-ordinal>-<rule>`, numbering the unit's findings from `001` in order of location, message, severity, observed evidence, and expected evidence; require the suffix to match `finding-[0-9][0-9][0-9]-[a-z0-9_-]+`, and treat a mismatch as a pre-persistence `BLOCKED` defect.

Interactive sessions pass each rendered object through a quoted heredoc:

```bash
spx verification run scope add --verification-type audit --scope-type file --scope '<pdr-path>' --run '<run-token>' --idempotency-key '<unit-key>' --payload stdin <<'SCOPE_JSON'
<rendered-scope-object>
SCOPE_JSON
```

```bash
spx verification run finding add --verification-type audit --scope-type file --scope '<pdr-path>' --run '<run-token>' --idempotency-key '<finding-key>' --payload stdin <<'FINDING_JSON'
<rendered-finding-object>
FINDING_JSON
```

When the task message or the harness fixes one physical command line per call, pipe each rendered object instead — `printf '%s\n' '<rendered-object>' | spx verification run finding add --verification-type audit --scope-type file --scope '<pdr-path>' --run '<run-token>' --idempotency-key '<finding-key>' --payload stdin`, and the same form for `scope add` — with every apostrophe in the object written as the single-quote splice `'"'"'`. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute PDR text as shell syntax. Run every mutation serially, preserving each result before the next command.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findingCount` is zero for approval, its `findings` group every accepted finding under `blocking` and `debt`, its `auditScopeUnits` carry the root and the five property units, and its `events` carry every accepted finding payload and the terminal event. Keep every SPX field unchanged, and add no `APPROVED` or `REJECTED` prose envelope.

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

How to avoid: Step 6 judges the assertion type against the `spec-tree:test-evidence-standards` assertion-type litmus. A universal (ALWAYS / NEVER / "for all" / "no input") tagged `scenario` is `assertion-type-mismatch`; a structural tag problem — bare mechanism tag, wrong subsection, missing tag, more than one tag — is `invalid-tag`.

**Failure 4: Flagged a tooling product's observable state as architecture**

Claude audited a PDR for a command-line tool whose product document declares its audience operates the product through a CLI and an on-disk layout. The PDR described the repository layout the audience inspects on disk and the version-control state it observes. Claude saw git commands and filesystem paths, applied the end-user-application reflex ("a user does not see git"), and rejected the statements as `architecture-content`. That is a false positive: the declared audience operates exactly that surface, so the layout is observable product behavior.

How to avoid: Step 4 reads the product document's declared audience first and judges "observable" against it. A git topology, a path layout, or a CLI behavior the audience operates is product behavior. Reserve `architecture-content` for what the audience never operates — the tool's internal algorithm, in-memory data structures, persisted schema, and library choices — which stays an ADR concern even for a tooling product.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every PDR rule was judged with none skipped — content classification, property quality (observability, falsifiability, and stability), per-rule tag validity and assertion-type fit, atemporal voice, and consistency (coverage-complete).
- The sealed run carries one root unit and one unit per evidence-model property, and its terminal status is `approved` only with no finding and every unit `audited`.
- Each finding is falsifiable: it names the section, the violated rule, and the evidence — the architecture content wrongly placed, the non-observable, unfalsifiable, or unstable property, the absent verification section or rules, the unverifiable rule or mismatched tag, the temporal phrase, or the contradicted product spec or ancestor PDR.
- An absent or empty Verification section and an unevaluable property each record a finding, so neither can seal `approved` through an empty iteration.
- The same PDR, standards, and run-driver identity yield the same units, finding keys, and terminal status.

</success_criteria>
