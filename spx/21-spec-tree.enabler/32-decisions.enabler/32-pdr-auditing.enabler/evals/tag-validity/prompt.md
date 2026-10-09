<!-- Generated from the complete producer set:
dist/claude/spec-tree/skills/audit-pdr/SKILL.md
dist/claude/spec-tree/skills/audit-pdr/references/pdr-evidence-model.md
-->

Apply the complete producer below to the supplied PDR. Return only the producer's structured JSON verdict.

<pre><code>
<!-- Producer: dist/claude/spec-tree/skills/audit-pdr/SKILL.md -->

---
name: audit-pdr
description: >-
  PDR audit methodology — judges one PDR against the PDR evidence model,
  covering content classification, property quality, per-rule tag validity,
  atemporal voice, and consistency with ancestor decisions, and records the
  judgment through an SPX file-scoped verification run.
argument-hint: "<JSON object with path, runDriver, and agentOwningPluginVersion>"
allowed-tools: Read, Grep, Glob, Skill, Bash(git rev-parse:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

<objective>

A sealed `spx verification run` on one PDR against the PDR evidence model — terminal status `approved` with no finding, or `rejected` with each finding naming the section, the violated rule, and the evidence for content classification, property quality, declaration form and tag fitness, atemporal voice, or consistency with the product spec and ancestor PDRs — or a `BLOCKED` diagnostic naming the failed prerequisite or command.

</objective>

<constraints>

Read the PDR evidence model's boundary guidance for content classification, property quality, and tag validity before auditing: `${CLAUDE_SKILL_DIR}/references/pdr-evidence-model.md`

**PRODUCT BEHAVIOR, NOT ARCHITECTURE.**

PDRs govern what the product does, behavior that its users experience. "Sessions expire after 1 hour" is product behavior. "Sessions use JWT with 1-hour TTL" is architecture. If the content describes HOW something is built rather than WHAT users observe, it belongs in an ADR.

"Users" means the audience the product document declares, and "observe" means observe through the interaction surfaces that document names — not a fixed end-user-application assumption. When the product document declares an audience that operates the product through a command-line, filesystem, version-control, or other infrastructure surface, the CLI, filesystem, and version-control state that audience operates is product behavior; the internal algorithm, in-memory data structure, persisted schema, and library choices that audience never touches stay architecture.

**ATEMPORAL VOICE.**

PDRs state atemporal product truth without historical context. No references to past behavior or events.

**THE SEALED RUN IS THE VERDICT.**

The run's terminal status is `approved` or `rejected`. A property this audit cannot evaluate rejects the run through a blocking finding naming the missing evidence; it never becomes an approval through an unjudged unit.

- NEVER edit the PDR or other product content, and NEVER commit, stash, create a branch, or move the checkout. The audit's own SPX verification-run journal is the only state it writes.
- ALWAYS make every judgment of the PDR from the content `spx verification run input` replays from the run, never from a separate read of the live file. Step 9 compares the live file with the retained input before the run finishes.
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

The PDR's governing node is the directory containing it, `spx/` for a product-root PDR. Read its context read-only, never invoking `/contextualize` or `/sync-base`, so the audit changes no checkout state: the product spec, then each spec and every decision record along the path from `spx/` to the governing node, then every decision a loaded spec or decision cites by full `spx/` path. The PDR under audit is excluded from this read wherever it appears, as a decision record on the path or as a citation. A spec missing on that path, or a cited decision that does not exist, returns `BLOCKED` with `runToken: not-started` naming the missing file and, for a citation, the citing file.

The product document is the product spec this step loads. Steps 4 and 8 read its declared audience, interaction surfaces, and scope; Step 8 reads the ancestor PDRs and the sibling ADRs — the ADRs in the PDR's own directory — from this context. Every step reads the PDR under audit only from the replayed input.

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

How to avoid: Step 4 classifies every statement. "Would the product document's declared audience observe or operate this?" is the test.

**Failure 2: Accepted non-observable properties**

Claude saw "Product properties: Database connections are pooled with a maximum of 50 connections." This is an implementation detail observable only by a DBA, not by users. The PDR version would be "The product handles at least 500 concurrent users without degradation."

Why it failed: Claude treated an implementation detail measurable by a specialist as a guarantee observable by the product's users.

How to avoid: Step 5 asks whether each property is observable from the user's perspective and whether a scenario violates it.

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


<!-- Producer: dist/claude/spec-tree/skills/audit-pdr/references/pdr-evidence-model.md -->

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

1. **Tag matching its subsection** — under `### Testing`, one assertion type (`scenario`/`mapping`/`conformance`/`property`/`compliance`); under `### Eval`, `([eval])`; under `### Audit`, `([audit])`. An unsupported bare mechanism tag, a missing tag, more than one tag, or a tag that disagrees with its subsection is `invalid-tag`.
2. **Assertion-type fit** — a `### Testing` rule's assertion type fits the claim's quantifier under the `spec-tree:test-evidence-standards` assertion-type litmus; a universal `ALWAYS`/`NEVER` claim tagged `scenario` is `assertion-type-mismatch`, since a single case cannot establish a universal.

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

- ALWAYS: every theme variant is selectable from the settings surface ([audit])
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

</code></pre>

The PDR input (JSON-encoded):

```json
{input_json}
```
