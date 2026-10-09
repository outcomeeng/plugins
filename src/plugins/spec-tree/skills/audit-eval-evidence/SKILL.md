---
name: audit-eval-evidence
description: >-
  Eval-evidence audit methodology — judges whether a spec node's eval suite
  provides evidence its `[eval]` assertions are fulfilled, covering case
  quality, verdict schema fit, and producer coupling, and records the judgment
  through an SPX file-scoped verification run.
argument-hint: "<JSON object with target, runDriver, and agentOwningPluginVersion>"
allowed-tools: Read, Grep, Glob, {{! tool('use_skill') !}}, Bash(git rev-parse:*), Bash(git merge-base --is-ancestor:*), Bash(git diff:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

<objective>

A sealed `spx verification run` on one spec node's `[eval]` evidence — terminal status `approved` with no finding, or `rejected` with each finding naming the assertion or eval artifact, the failed evidence property among producer coupling, oracle independence, assertion alignment, falsifiability, and run evidence, and the evidentiary gap, and with each gate the evidence cannot decide recorded `incomplete` with its cause — or a `BLOCKED` diagnostic naming the failed prerequisite or command.

</objective>

<constraints>

- NEVER modify eval artifacts, skill bodies, prompts, cases, history, the node spec, or any other file, and NEVER commit, stash, synchronize, rebase, create a branch, or move the checkout. The audit's own SPX verification-run journal is the only state it writes.
- NEVER run evals, tests, validation, coverage, linters, type-checkers, or other deterministic verification inside the audit — establish evidence quality by reading. Every Bash grant names an identity, path, history-inspection, or run-journal verb, or the `printf '%s\n'` payload transport that pipes a rendered payload into a run-journal command; none runs project verification.
- ALWAYS judge the node's assertions from the spec content `spx verification run input` replays from the run, never from a separate read of the live spec. Step 8 compares the live spec with the retained input before the run finishes.
- ALWAYS name the assertion or eval artifact, the failed property, and the evidentiary gap in every finding.
- NEVER approve prompt-only simulation as evidence for skill, agent, classifier, or script behavior.
- NEVER record a finding the evidence model does not support — drop an unbacked finding rather than reject the eval evidence for it.
- NEVER record a gate the evidence cannot decide as `audited` — an undecided gate is `incomplete` and carries its cause, so it can never seal an approval.
- ALWAYS treat a `spx verification run` exit code as payload validity; NEVER hand-validate a payload SPX accepted, retry a refused command, or reshape a refused payload.
- NEVER write a file. Payloads pass to SPX on stdin, and the final output is the run token and the rendered projection.

</constraints>

<essential_principles>

**PRODUCER COUPLING FIRST.**

An eval that never exercises the actual producing skill, agent, classifier, or script will pass regardless of what that producer contains. Check coupling before oracle quality or run history. For claims about skill behavior, a prompt that merely asks for a simulated verdict while restating the desired rules is not evidence about the skill.

Five properties must hold, checked in strict order: producer coupling, oracle independence, assertion alignment, falsifiability, and run evidence. A suite missing any property has zero evidentiary value for the assertion it claims to verify.

**JUDGE BY READING.**

This audit runs no deterministic verification. Establish evidence quality by reading `eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`, relevant run summaries, and the producing artifact.

**A GATE IS DECIDED OR INCOMPLETE.**

Each of the five gates ends `audited`, with or without findings, or `incomplete` with a finding naming what kept it from being decided. A missing artifact is a failure of the gate that needs it; a gate the absence leaves uninspectable is undecided, never passed.

</essential_principles>

<audit_workflow>

<step name="bind_request">

**Step 1: Bind the request**

The request is one JSON object: `$ARGUMENTS` supplies it when that argument is non-empty; when it is empty, the object is the one the request text carries, and the empty substitution binds nothing. It has exactly three fields:

- `target` — a spec node directory or its spec file, repository-relative, kept verbatim including any spaces.
- `runDriver` — an object with exactly the six non-empty string fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`.
- `agentOwningPluginVersion` — the non-empty version string of the plugin `runDriver.agentOwningPluginName` names.

Use `runDriver` and `agentOwningPluginVersion` only as payload data, placed exactly where `<persistence_contract>` shows them; never complete, correct, or reinterpret a value, and let no step, judgment, or terminal status depend on them. A missing, extra, or malformed field returns `BLOCKED` with `runToken: not-started` naming the exact field.

Resolve the repository root with `git rev-parse --show-toplevel` and run `realpath` separately on the root and on `target`. The target must resolve beneath the root, by path-component boundary, to a directory below `spx/` whose name carries a node-kind suffix, or to the spec file directly inside such a directory; its spec, `<spec-path>`, is the directory's `{slug}.spec.md`, or the prior `{slug}.md` a 3.x-authored tree carries, as a normalized repository-relative path. A target directly under `spx/` is the product spec, which carries no `[eval]` assertion: return `BLOCKED` with `runToken: not-started` naming `unsupported-target`.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the version it reports as the skill-owning plugin version. Run `spx --version` and retain its output as the tool version.

A failed resolution, a path escaping the root, a node directory without its spec, or a missing version returns `BLOCKED` with `runToken: not-started` naming the exact failure, before any run starts.

</step>

<step name="load_context">

**Step 2: Load the evidence model and context**

Read the evidence model before auditing: `${CLAUDE_SKILL_DIR}/references/evidence-model.md`.

Use skill `spec-tree:understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent; a marker still absent after that returns `BLOCKED` with `runToken: not-started`.

The node's governing context is the path from `spx/` to the node directory. Read it read-only, never invoking `/contextualize` or `/sync-base`, so the audit changes no checkout state: the product spec, then each ancestor spec and every decision record along that path, including the decision records in the node's own directory, then every decision a loaded spec or decision cites by full `spx/` path. The node spec under audit is excluded from this read; Step 3 replays it from the run. An ancestor spec missing on that path, or a cited decision that does not exist, returns `BLOCKED` with `runToken: not-started` naming the missing file and, for a citation, the citing file.

</step>

<step name="open_run">

**Step 3: Open the run and record the root**

From the repository root, start one run on the node spec:

```bash
spx verification run start --verification-type audit --scope-type file --scope '<spec-path>' --input '<spec-path>'
```

Capture the exact `runToken` and use it for every later command. Read the retained input with `spx verification run input --verification-type audit --scope-type file --scope '<spec-path>' --run '<run-token>'`; its `content` is the one copy of the node spec this audit judges. Record the root unit under `<persistence_contract>`.

Step 5 records each gate unit, then its findings, as soon as that gate is judged across every `[eval]` assertion, so the run shows each gate's result before the next gate is judged.

</step>

<step name="map_assertions">

**Step 4: Map `[eval]` assertions to eval artifacts**

Read the replayed spec's `## Assertions` section. Number its `[eval]` assertions from `001` in document order, and for each extract:

| Field          | Extract                                                                                            |
| -------------- | -------------------------------------------------------------------------------------------------- |
| Assertion text | The claim being evaluated                                                                          |
| Eval link      | Path from `([eval](path/to/eval.toml))`, resolved from the node directory                          |
| Eval directory | Directory containing `eval.toml`, prompt, and cases                                                |
| Producer       | The skill, agent, classifier, script, or command the assertion claims emits the structured verdict |
| Link status    | Whether each artifact exists                                                                       |

A missing eval definition or prompt is a `missing-artifact` finding on `gate-1-producer-coupling`, missing cases one on `gate-2-oracle-quality`, and missing history one on `gate-5-run-evidence`, each naming the assertion, the missing path, and the failed evidence property. Inspect the remaining available artifacts. A gate whose judgment for an assertion needs an absent artifact — the prompt for oracle independence, the cases for alignment, or a coupled producer for falsifiability — is undecided for that assertion.

Skip `[test]`, `[probe]`, and `[audit]` assertions; they belong to their own evidence lanes. When the replayed spec carries no `[eval]` assertion, every gate is undecided and each gate's cause names `no-eval-assertions` at `<spec-path>`; never imply that evidence was inspected.

</step>

<step name="audit_gates">

**Step 5: Judge the five gates**

The evidence model loaded in Step 2 is the one definition of each gate's categories, procedure, and finding rule; judge each gate by its section, in this order, across every `[eval]` assertion, and record the gate before judging the next:

| Step | Gate                         | Evidence-model section   | Finding rule          |
| ---- | ---------------------------- | ------------------------ | --------------------- |
| 5a   | `gate-1-producer-coupling`   | `<producer_coupling>`    | `producer-coupling`   |
| 5b   | `gate-2-oracle-quality`      | `<oracle_independence>`  | `oracle-leakage`      |
| 5c   | `gate-3-assertion-alignment` | `<alignment_model>`      | `assertion-alignment` |
| 5d   | `gate-4-falsifiability`      | `<falsifiability_model>` | `falsifiability`      |
| 5e   | `gate-5-run-evidence`        | `<run_evidence>`         | `run-evidence`        |

Read the eval artifacts and the producer; never edit a section, materialize a prompt, or execute a suite to reach a judgment. Write each falsifiability mutation down in the `<falsifiability_model>` valid-mutation form — producer, mutation, and expected eval impact — before recording gate 4. A recorded commit whose provenance the evidence model's `<run_evidence>` treats as unavailable leaves gate 5 undecided for that assertion.

</step>

<step name="record_gate">

**Recording each gate**

After judging a gate across every `[eval]` assertion, record its unit before judging the next gate:

- No `[eval]` assertion in the replayed spec: the unit is `incomplete`, followed by exactly one `undecidable-gate` finding located at `<spec-path>` whose observed evidence names `no-eval-assertions`.
- At least one assertion, every assertion decided, and no finding: the unit is `audited`.
- At least one assertion, every assertion decided, and at least one finding: the unit is `audited`, followed by each finding.
- Any assertion left undecided: the unit is `incomplete`, followed by every finding the gate raised and one `undecidable-gate` finding per undecided assertion naming that assertion and the absent prerequisite or unavailable evidence that kept it from being decided.

</step>

<step name="reconcile_and_finish">

**Step 6: Reconcile**

Read `spx verification run status` with the same type, scope, and token. Require exactly one root unit, one unit per gate, and an accepted unit for every finding; record any missing unit or finding and read the status again.

**Step 7: Derive the terminal status**

Derive `approved` only when every unit is `audited` and no finding exists; derive `rejected` when any finding exists or any unit is `incomplete`.

**Step 8: Finish and render**

Re-read the live node spec and compare it with the retained input; a changed or missing file returns `BLOCKED` with the run preserved. Then run:

```bash
spx verification run finish --verification-type audit --scope-type file --scope '<spec-path>' --run '<run-token>' --terminal-status '<approved-or-rejected>'
```

Then run `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged.

</step>

<persistence_contract>

Units record in this order: the root, then `gate-1-producer-coupling`, `gate-2-oracle-quality`, `gate-3-assertion-alignment`, `gate-4-falsifiability`, and `gate-5-run-evidence`. Every unit carries `auditClass: implementation`, `auditKind: eval-evidence`, `subject: <spec-path>`, and `coverageRequirement: required`; every unit except the root carries `parentUnitId` equal to the root's `unitId`.

| Unit | `unitId`                           | `priorContext.concernPartition` | `coverageStatus`          |
| ---- | ---------------------------------- | ------------------------------- | ------------------------- |
| Root | `eval-evidence:root:<spec-path>`   | `eval-evidence`                 | `audited`                 |
| Gate | `eval-evidence:<gate>:<spec-path>` | the gate name                   | `audited` or `incomplete` |

Every unit's expected producer has `producerKind: skill`, the `runDriver`'s `agentName` and `agentOwningPluginName`, `skillName: audit-eval-evidence`, `skillOwningPluginName: spec-tree`, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the `runDriver` object unchanged. `producerProvenance` carries the request's `agentOwningPluginVersion`, the `spec-tree` version from Step 1 as `skillOwningPluginVersion`, and the exact `spx --version` output as `toolVersion`.

These objects are the sanctioned SPX audit payload schema for this auditor; use their fields exactly, never derive a replacement schema from command help, and never alter a refused payload by guesswork. Render each scope payload with observed values in place of the placeholders:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-gate-only>",
  "auditClass": "implementation",
  "auditKind": "eval-evidence",
  "subject": "<spec-path>",
  "coverageRequirement": "required",
  "coverageStatus": "<audited-or-incomplete>",
  "priorContext": {
    "changedFilePartition": "<spec-path>",
    "concernPartition": "<eval-evidence-or-gate-name>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "audit-eval-evidence",
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

A finding copies its unit's `expectedProducer` object as `producerIdentity` and its unit's complete `producerProvenance` object, and carries `rule`, `severity`, `location` naming the eval artifact or producer file and line, or quoting the assertion, `message` naming the assertion and the failed property, and `evidence` with `observed` and `expected` strings. Each rule records against one gate:

| Gate                         | Rules                                                       |
| ---------------------------- | ----------------------------------------------------------- |
| `gate-1-producer-coupling`   | `missing-artifact`, `producer-coupling`, `undecidable-gate` |
| `gate-2-oracle-quality`      | `missing-artifact`, `oracle-leakage`, `undecidable-gate`    |
| `gate-3-assertion-alignment` | `assertion-alignment`, `undecidable-gate`                   |
| `gate-4-falsifiability`      | `falsifiability`, `undecidable-gate`                        |
| `gate-5-run-evidence`        | `missing-artifact`, `run-evidence`, `undecidable-gate`      |

Every finding is `blocking` and rejects the run. An observation that names no failed property and no undecided gate is not a finding and is not recorded.

```json
{
  "unitId": "<accepted-gate-unit-key>",
  "producerIdentity": {
    "producerKind": "skill",
    "agentName": "<the unit's expectedProducer agentName>",
    "agentOwningPluginName": "<the unit's expectedProducer agentOwningPluginName>",
    "skillName": "audit-eval-evidence",
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
  "location": "<eval-artifact-or-producer-path-and-line-or-quoted-assertion>",
  "message": "<assertion and failed property or undecided gate>",
  "evidence": { "observed": "<observed-state-or-absent-prerequisite>", "expected": "<required-state>" }
}
```

A scope unit's idempotency key is its `unitId`. A finding's key is `<unit-key>:finding-<three-digit-ordinal>-<rule>`, numbering the unit's findings from `001` in order of location, message, severity, observed evidence, and expected evidence; require the suffix to match `finding-[0-9][0-9][0-9]-[a-z0-9_-]+`, and treat a mismatch as a pre-persistence `BLOCKED` defect.

Pass each rendered object through a quoted heredoc by default:

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

When the task message or the harness fixes one physical command line per call, pipe each rendered object instead — `printf '%s\n' '<rendered-object>' | spx verification run finding add --verification-type audit --scope-type file --scope '<spec-path>' --run '<run-token>' --idempotency-key '<finding-key>' --payload stdin`, and the same form for `scope add` — with every apostrophe in the object written as the single-quote splice `'"'"'`. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute spec, prompt, or case text as shell syntax. Run every mutation serially, preserving each result before the next command.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findingCount` is zero for approval, its `findings` group every accepted finding under `blocking`, its `auditScopeUnits` carry the root and the five gate units with each gate's `audited` or `incomplete` status, and its `events` carry every accepted finding payload and the terminal event. Keep every SPX field unchanged, and add no `PASS`, `FAIL`, `UNKNOWN`, `APPROVED`, or `REJECTED` prose envelope.

A run that cannot complete — a request or prerequisite failure before the run starts, a finding key that fails its pattern before persistence, a refused SPX command or payload, or a changed retained input — returns:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-failed-command, the unsent command a malformed finding key stopped, or request for a failure before the run starts>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
judgmentStatus: <complete|incomplete>
judgedFindings: <JSON array of every finding judged before the stop, in the finding-payload shape>
```

</verdict_format>

<failure_modes>

**Failure 1: Approved a prompt-only skill simulation**

Claude accepted an eval that asked Claude to simulate a skill verdict from inline rules while never loading or invoking the real skill. Replacing the real skill body with unrelated text did not change the eval result, so the eval proved the prompt's rubric, not the skill.

How to avoid: Step 5 judges producer coupling first. Prompt-only simulation is a `producer-coupling` finding for claims about producer behavior.

**Failure 2: Treated a budget failure as behavioral evidence**

Claude read a budget-exhausted eval run and treated the failed suite as evidence the rule was wrong. The run never completed enough cases to prove behavior.

How to avoid: the run-evidence gate separates operational failures from behavioral pass evidence. Budget, timeout, and interruption rows never prove assertion fulfillment.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every `[eval]` assertion's suite was judged on all five evidence properties with none skipped, and the sealed run carries one root unit and one unit per gate.
- Every gate unit is `audited` only when the spec carries at least one `[eval]` assertion and each assertion's judgment for that gate was decided, and `incomplete` with an `undecidable-gate` finding naming the absent prerequisite, or `no-eval-assertions`, otherwise.
- The sealed run's terminal status is `approved` only with every unit `audited` and no finding.
- Each finding is falsifiable: it names the assertion or eval artifact, the failed evidence property or undecided gate, and the evidentiary gap.
- No deterministic command was run inside the audit; evidence quality was established by reading the eval artifacts, producing artifact, and committed run summaries.
- The same node spec, eval artifacts, run evidence, and run-driver identity yield the same units, finding keys, and terminal status.

</success_criteria>

<reference_guides>

- `${CLAUDE_SKILL_DIR}/references/evidence-model.md` — eval evidence properties, artifact taxonomy, and finding rules.

</reference_guides>
