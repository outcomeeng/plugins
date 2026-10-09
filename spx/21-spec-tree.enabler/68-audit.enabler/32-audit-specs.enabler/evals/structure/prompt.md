<!-- Generated from the complete producer at dist/claude/spec-tree/skills/audit-specs/SKILL.md. -->

Apply the complete producer below to the supplied spec node. When the input carries `context`, treat it as the governing methodology context loaded by the producer's contextualization step. Return only the producer's structured JSON verdict.

---
name: audit-specs
description: >-
  Spec-node audit methodology — judges one output or variant spec against the
  node-spec form, covering section structure, atemporal voice, and per-assertion
  tag fitness, and records the judgment through an SPX file-scoped verification
  run.
argument-hint: "<JSON object with path, runDriver, and agentOwningPluginVersion>"
allowed-tools: Read, Grep, Glob, Skill, Bash(git rev-parse:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

<objective>

A sealed `spx verification run` on one output or variant spec, including prior enabler/outcome forms — terminal status `approved` with no finding, or `rejected` with each finding naming the section or assertion, the violated rule, and the evidence for section structure, atemporal voice, or declaration form and tag fitness — or a `BLOCKED` diagnostic naming the failed prerequisite or command.

</objective>

<constraints>

**VERIFICATION TYPE MUST FIT THE CLAIM.**

The canonical template distinguishes untagged authoring declarations directly under `## Assertions` from routed assertions. Drafts may coexist with routed subsections and receive all applicable declaration-quality checks without missing-tag or missing-heading findings. For routed assertions, apply the foundation's tag and malleability rules. The loaded foundation's verification-type and verification-selection rules decide whether a verification type fits its claim; the assertion-type litmus of `spec-tree:test-evidence-standards`, loaded in Step 6, decides whether a `[test]` assertion type fits. Two checks decide selected-tag fitness:

- Under a `[test]` tag, the assertion type (scenario, mapping, conformance, property, compliance) fits the claim's quantifier. A universal claim (ALWAYS / NEVER / "for all" / "for every" / "no input") is never `scenario`, because a scenario proves one case and cannot establish a claim about every case; `scenario` fits only a single existential interaction.
- The tag is reachable for the claim's subject. A claim whose subject is the content of an authored prose or documentation artifact — text the product authors and maintains in a document, not executable behavior — is never `[test]`. Behavioral evidence cannot verify it: the only evidence available reads the authored text and asserts on it, which proves the prose was authored, not that code behaves — whether the read is direct or laundered through test infrastructure. Such a claim's tag is `[eval]` or `[audit]`.

A required tag missing from a routed assertion, an unsupported bare mechanism tag, a duplicate tag, an assertion type the litmus would not produce, or `[test]` on a prose-content claim is a finding. Declaration approval establishes no evidence completeness, implementation correctness, or Passing state for untagged claims.

**HEADINGS DESCRIBE CLAIM SHAPE.**

The headings under `## Assertions` group claims by shape independently of verification type. `### Scenarios` holds specific existential interactions. `### Mappings`, `### Conformance`, `### Properties`, and `### Compliance` hold their corresponding universal claim shapes. Classify the assertion text before considering its tag: a `Given … when … then …` assertion is an existential scenario under every verification type and is mismatched under `### Compliance`; an `ALWAYS:` or `NEVER:` assertion is universal and belongs under `### Compliance` unless its content establishes a mapping, conformance rule, or property. A universal ALWAYS/NEVER rule remains under `### Compliance` when its verification type is `[audit]` or `[eval]`; the heading does not assign the test-only compliance assertion type. A verification-type heading such as `### Test`, `### Eval`, or `### Audit` is outside the node-template shape and is a `heading-mismatch` finding.

**ATEMPORAL VOICE.**

A node states product truth. "The status rollup reports failing when any child fails" — not "We changed the rollup to propagate failures."

**THE SEALED RUN IS THE VERDICT.**

The run's terminal status is `approved` or `rejected`. A property that cannot be evaluated rejects the run through a finding naming the missing evidence; it never becomes an approval through an unjudged unit.

**ARTIFACT BOUNDARY.**

Decision-record form (ADR/PDR) is audited by `/audit-adr` and `/audit-pdr`; test-evidence quality is audited by `/audit-tests`. This audit checks the node spec's own form, not its tests or its decisions.

- NEVER edit the node spec or other product content, and NEVER commit, stash, create a branch, or move the checkout. The audit's own SPX verification-run journal is the only state it writes.
- ALWAYS make every judgment of the node spec from the content `spx verification run input` replays from the run, never from a separate read of the live file. Step 8 compares the live file with the retained input before the run finishes.
- ALWAYS judge each assertion's verification type against the loaded foundation and each test assertion type against the `spec-tree:test-evidence-standards` litmus — never accept a present tag as valid by its mere presence. NEVER invoke the `/verify` or `/test` authoring workflows or select a replacement tag during this audit.
- ALWAYS name the section or assertion, the violated rule, and the evidence in every finding.
- NEVER record a finding the cited rule does not support — drop an unbacked finding rather than reject the node for it.
- ALWAYS treat a `spx verification run` exit code as payload validity; NEVER hand-validate a payload SPX accepted, retry a refused command, or reshape a refused payload.
- NEVER write a file. Payloads pass to SPX on stdin, and the final output is the run token and the rendered projection.

</constraints>

<audit_workflow>

<step name="bind_request">

**Step 1: Bind the request**

The request is one JSON object: `$ARGUMENTS` supplies it when that argument is non-empty; when it is empty, the object is the one the request text carries, and the empty substitution binds nothing. It has exactly three fields:

- `path` — the node spec file, repository-relative, kept verbatim including any spaces.
- `runDriver` — an object with exactly the six non-empty string fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`.
- `agentOwningPluginVersion` — the non-empty version string of the plugin `runDriver.agentOwningPluginName` names.

Use `runDriver` and `agentOwningPluginVersion` only as payload data, placed exactly where `<persistence_contract>` shows them; never complete, correct, or reinterpret a value, and let no step, judgment, or terminal status depend on them. A missing, extra, or malformed field returns `BLOCKED` with `runToken: not-started` naming the exact field.

Resolve the repository root with `git rev-parse --show-toplevel`. Run `realpath` separately on the root and the spec path, and require a regular file beneath the root by path-component boundary. Retain the spec as its normalized repository-relative path, `<spec-path>`, for every later command.

The target is a node spec only when its parent directory lies below `spx/` and carries a node-kind suffix. A spec directly under `spx/` is the product spec, which carries no assertions and belongs to review: return `BLOCKED` with `runToken: not-started` naming `unsupported-target`.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the version it reports as the skill-owning plugin version. Run `spx --version` and retain its output as the tool version.

A failed resolution, a path escaping the root or naming no regular file, an unsupported target, or a missing version returns `BLOCKED` with `runToken: not-started` naming the exact failure, before any run starts.

</step>

<step name="load_context">

**Step 2: Load context**

Use skill `spec-tree:understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent or lacks `Template root`. A marker still absent after that returns `BLOCKED` with `runToken: not-started`.

The node's governing context is the path from `spx/` to the directory containing the spec. Read it read-only, never invoking `/contextualize` or `/sync-base`, so the audit changes no checkout state: the product spec, then each ancestor spec and every decision record along that path, including the decision records in the node's own directory, then every decision a loaded spec or decision cites by full `spx/` path. The node spec under audit is never read from the live file. An ancestor spec missing on that path, or a cited decision that does not exist, returns `BLOCKED` with `runToken: not-started` naming the missing file and, for a citation, the citing file.

A variant's kind is its parent's kind; Step 4 reads the parent spec from this context.

</step>

<step name="open_run">

**Step 3: Open the run and record the root**

From the repository root, start one run on the node spec:

```bash
spx verification run start --verification-type audit --scope-type file --scope '<spec-path>' --input '<spec-path>'
```

Capture the exact `runToken` and use it for every later command. Read the retained input with `spx verification run input --verification-type audit --scope-type file --scope '<spec-path>' --run '<run-token>'`; its `content` is the one copy of the node spec the audit judges. Record the root unit under `<persistence_contract>`.

Identify the node's kind from its directory suffix, or its parent's kind for a `.variant`, and read `nodes/{kind}-name.spec.md` beneath the `Template root` the foundation marker records; derive current openings, front matter, and tag forms from it. For a prior enabler/outcome artifact, apply the prior grammar the foundation admits. When a required template cannot be loaded, Step 4 records `template-missing` naming the blocked read.

From the replayed content, identify the node's opening, required front matter, `## Assertions` section, and each assertion's placement and optional tag.

Steps 4 through 6 each record their unit, then its findings, as soon as that unit's judgment is complete, so the run shows each property's result before the next property is judged.

</step>

<step name="audit_structure">

**Step 4: Section structure**

Verify three structural properties:

1. The opening and required front matter match the canonical kind template. Prior enablers retain `PROVIDES … SO THAT … CAN …`; prior outcomes retain `WE BELIEVE THAT … WILL … CONTRIBUTING TO …`. A missing required opening clause is `malformed-kind-statement`; missing required front matter is `missing-frontmatter`.
2. An `## Assertions` section contains at least one assertion. Specific untagged declarations may appear directly under it without a heading. Tagged assertions require the template's routed grouping. An empty assertion section is `missing-assertions`.
3. Each claim-shape heading (`### Scenarios`, `### Mappings`, `### Conformance`, `### Properties`, `### Compliance`) holds at least one assertion, and every assertion under it has the heading's claim shape under the classification rule in `<constraints>` **HEADINGS DESCRIBE CLAIM SHAPE**.

**No kind statement or no `## Assertions` section → finding `missing-section`. A kind statement that differs from its template → finding `malformed-kind-statement`. An empty, unsupported, or claim-mismatched heading → finding `heading-mismatch`. A draft assertion's absent heading is valid.**

</step>

<step name="audit_voice">

**Step 5: Atemporal voice**

Check EVERY section for temporal language:

| Temporal (finding)                    | Atemporal (correct)                |
| ------------------------------------- | ---------------------------------- |
| "We added a rollup so failures show"  | "The rollup propagates failures"   |
| "Currently the parser accepts X"      | "The parser accepts X"             |
| "After the rewrite, status derives Y" | "Status derives from test results" |

**Any temporal language in any section → finding `temporal-voice`.**

</step>

<step name="audit_tag_fitness">

**Step 6: Per-assertion tag fitness**

When any assertion carries `[test]`, use skill `spec-tree:test-evidence-standards` and load its assertion-type litmus; when it cannot load, record `test-standards-unavailable` naming the blocked read.

For each assertion under `## Assertions`:

1. An untagged assertion directly under `## Assertions` is an authoring declaration; without selecting evidence, require that it names its subject, the observable condition it constrains, and a concrete observation that would violate it. A draft that is vague or unfalsifiable on that test is `unfalsifiable-assertion`. For routed assertions, apply the foundation's malleability rule and canonical tag forms: test, eval, and probe carry paths; audit carries its rule slug, or the admitted pathless form for a toolchain without slug support. Missing required tags, duplicate or unsupported tags, and path-bearing mechanisms without a path are `invalid-tag`.
2. Under `[test]`, the assertion type fits the claim's quantifier — apply the quantifier rule from `<constraints>` and the loaded litmus. Record a type the litmus would not produce; do not relitigate a choice the litmus leaves open between equally valid types.
3. The tag is reachable for the claim's subject — apply the prose-content rule from `<constraints>`.

**A required tag missing from a routed assertion, a duplicate tag, or an unsupported bare mechanism tag → finding `invalid-tag`. A `[test]` assertion type that contradicts the claim's quantifier → finding `evidence-type-mismatch`. `[test]` on an authored-prose claim → finding `prose-coupling`. A vague or unfalsifiable draft → finding `unfalsifiable-assertion`.**

</step>

<step name="reconcile_and_finish">

**Step 7: Reconcile**

Read `spx verification run status` with the same type, scope, and token. Require exactly one root unit, one unit per declaration-quality property, and an accepted unit for every finding; record any missing unit or finding and read the status again.

**Step 8: Finish and render**

Re-read the live node spec and compare it with the retained input; a changed or missing file returns `BLOCKED` with the run preserved.

Derive `approved` only when every unit is `audited` and no finding exists; derive `rejected` when any finding exists. Then run:

```bash
spx verification run finish --verification-type audit --scope-type file --scope '<spec-path>' --run '<run-token>' --terminal-status '<approved-or-rejected>'
```

Then run `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged.

</step>

<persistence_contract>

Units record in this order: the root, then `section-structure`, `atemporal-voice`, and `tag-fitness`. Every unit carries `subject: <spec-path>`, `coverageRequirement: required`, `coverageStatus: audited`, and `parentUnitId` equal to the root's `unitId` on every unit except the root, which omits it.

| Unit                 | `unitId`                      | `auditClass` | `auditKind` | `priorContext.concernPartition` |
| -------------------- | ----------------------------- | ------------ | ----------- | ------------------------------- |
| Root                 | `spec:root:<spec-path>`       | `spec`       | `spec`      | `spec`                          |
| Declaration property | `spec:<property>:<spec-path>` | `spec`       | `spec`      | the property name               |

Every unit's expected producer has `producerKind: skill`, the `runDriver`'s `agentName` and `agentOwningPluginName`, `skillName: audit-specs`, `skillOwningPluginName: spec-tree`, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the `runDriver` object unchanged. `producerProvenance` carries the request's `agentOwningPluginVersion`, the `spec-tree` version from Step 1 as `skillOwningPluginVersion`, and the exact `spx --version` output as `toolVersion`.

These objects are the sanctioned SPX audit payload schema for this auditor; use their fields exactly, never derive a replacement schema from command help, and never alter a refused payload by guesswork. Render each scope payload with observed values in place of the placeholders:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-child-only>",
  "auditClass": "spec",
  "auditKind": "spec",
  "subject": "<spec-path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<spec-path>",
    "concernPartition": "<spec-or-property-name>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "audit-specs",
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

A finding copies its unit's `expectedProducer` object as `producerIdentity` and its unit's complete `producerProvenance` object, and carries `rule`, `severity`, `location` naming the section or quoted assertion, `message`, and `evidence` with `observed` and `expected` strings. Each rule records against one unit:

| Unit                | Rules                                                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `section-structure` | `missing-section`, `missing-frontmatter`, `missing-assertions`, `malformed-kind-statement`, `heading-mismatch`, `template-missing` |
| `atemporal-voice`   | `temporal-voice`                                                                                                                   |
| `tag-fitness`       | `invalid-tag`, `evidence-type-mismatch`, `prose-coupling`, `unfalsifiable-assertion`, `test-standards-unavailable`                 |

Every finding is `blocking` and rejects the run. An observation that names no defect is not a finding and is not recorded.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": {
    "producerKind": "skill",
    "agentName": "<the unit's expectedProducer agentName>",
    "agentOwningPluginName": "<the unit's expectedProducer agentOwningPluginName>",
    "skillName": "audit-specs",
    "skillOwningPluginName": "spec-tree",
    "invocationRole": "leaf-skill"
  },
  "producerProvenance": {
    "agentOwningPluginVersion": "<the unit's agentOwningPluginVersion>",
    "skillOwningPluginVersion": "<the unit's skillOwningPluginVersion>",
    "toolVersion": "<the unit's toolVersion>"
  },
  "rule": "<violated-rule-id>",
  "severity": "blocking",
  "location": "<section-or-quoted-assertion>",
  "message": "<finding-message>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

A scope unit's idempotency key is its `unitId`. A finding's key is `<unit-key>:finding-<three-digit-ordinal>-<rule>`, numbering the unit's findings from `001` in order of location, message, severity, observed evidence, and expected evidence; require the suffix to match `finding-[0-9][0-9][0-9]-[a-z0-9_-]+`, and treat a mismatch as a pre-persistence `BLOCKED` defect.

Interactive sessions pass each rendered object through a quoted heredoc:

```bash
spx verification run scope add --verification-type audit --scope-type file --scope '<spec-path>' --run '<run-token>' --idempotency-key '<unit-key>' --payload stdin <<'SCOPE_JSON'
<rendered-scope-object>
SCOPE_JSON
```

```bash
spx verification run finding add --verification-type audit --scope-type file --scope '<spec-path>' --run '<run-token>' --idempotency-key '<finding-key>' --payload stdin <<'FINDING_JSON'
<rendered-finding-object>
FINDING_JSON
```

When the task message or the harness fixes one physical command line per call, pipe each rendered object instead — `printf '%s\n' '<rendered-object>' | spx verification run finding add --verification-type audit --scope-type file --scope '<spec-path>' --run '<run-token>' --idempotency-key '<finding-key>' --payload stdin`, and the same form for `scope add` — with every apostrophe in the object written as the single-quote splice `'"'"'`. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute spec text as shell syntax. Run every mutation serially, preserving each result before the next command.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findingCount` is zero for approval, its `findings` group every accepted finding under `blocking`, its `auditScopeUnits` carry the root and the three property units, and its `events` carry every accepted finding payload and the terminal event. Keep every SPX field unchanged, and add no `APPROVED` or `REJECTED` prose envelope.

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

**Failure 1: Passed a `[test]` claim about a document's prose**

Claude read an assertion — "the skill body states the three-gate vocabulary ([test])" — and passed it because a `[test]` tag was present and pointed at a file. The only evidence such a claim admits reads the authored body and asserts a substring of it, so it proves the prose was typed, not that code behaves. The tag belongs in `[eval]` or `[audit]`. The coupling is identical whether the test reads the body directly or through a harness constant or reader helper — full-chain, the claim still verifies prose.

How to avoid: Step 6 check 3 — when the claim's subject is the content of an authored prose or documentation artifact, `[test]` is unreachable. Record `prose-coupling` and remediate to `[eval]` or `[audit]`.

**Failure 2: Passed a universal claim tagged `scenario`**

Claude saw a `### Compliance` assertion — a universal ALWAYS/NEVER claim — tagged `([test](… scenario …))` and passed it because the assertion type named one of the five. A scenario proves one case; it cannot establish a claim about every case, so the assertion ships unverified.

How to avoid: Step 6 check 2 verifies the assertion type fits the quantifier. Record `evidence-type-mismatch` for a universal tagged `scenario`, and for any type the litmus would not produce — without relitigating a choice the litmus leaves open between equally valid types.

**Failure 3: Rejected universal audit rules under `### Compliance`**

Claude read the evidence node's universal `[audit]` rules under `### Compliance` and rejected them as `heading-mismatch` because audit assertions carry no assertion type. That conflated the heading's claim-shape grouping with the test-only compliance assertion type and contradicted the canonical node templates.

How to avoid: Step 4 judges the heading from the claim's quantifier and form independently of its verification-type tag. Keep universal ALWAYS/NEVER rules under `### Compliance` with `[test]`, `[eval]`, or `[audit]`; record `heading-mismatch` for verification-type headings such as `### Audit` instead.

**Failure 4: Passed an existential scenario under `### Compliance`**

Claude read a `Given … when … then …` assertion under `### Compliance` and approved the node because the assertion carried `[eval]`. The tag described how the verdict was established; it did not change the assertion from a specific existential interaction into a universal rule.

How to avoid: Step 4 classifies explicit assertion form before verification type. Treat every `Given … when … then …` assertion as a scenario and record `heading-mismatch` under any heading other than `### Scenarios`.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every spec-node rule was judged with none skipped — claim-shape heading structure independent of verification type, atemporal voice, and per-assertion tag fitness (coverage-complete).
- The sealed run carries one root unit and one unit per declaration-quality property, every unit `audited`, and its terminal status is `approved` only with no finding.
- Each finding is falsifiable: it names the section or assertion, the violated rule, and the evidence — the malformed kind statement, the empty or mismatched heading, the temporal phrase, the invalid tag, the quantifier-mismatched assertion type, or the prose-coupled `[test]`.
- The same node spec, standards, and run-driver identity yield the same units, finding keys, and terminal status.

</success_criteria>

The spec-node input (JSON-encoded):

```json
{input_json}
```
