---
name: audit-implementation
description: >-
  Implementation-audit orchestration methodology — discovers implementation
  languages, composes code, test, and architecture concern audits, and records
  one audit verification run.
argument-hint: "<implementation audit request>"
allowed-tools: Read, Bash(spx verification run:*), Bash(printf:*), Glob, Grep, Skill
---

<objective>

A rendered SPX verification-run verdict for the requested implementation scope, accompanied by its raw run token, with `terminalStatus` set to `approved` or `rejected` and each finding naming the stable producer identity, unit, violated rule, severity, location, message, and observed-versus-expected evidence.

</objective>

<constraints>

- Read-only over the audited project tree. This skill never edits source, tests, specs, commits, branches, or pull requests.
- Persist audit state only through `spx verification run`; never use legacy journal commands, plugin-side verdict scripts, markdown comments, `.spx/audits/`, or tracked files as audit state.
- NEVER run deterministic verification — this orchestration composes agentic concern audits only.
- Contain no language-specific file extensions, commands, examples, or evidence patterns beyond the dispatch template `audit-{lang}-{code|tests|architecture}`.
- Treat the `spx verification run` command exit code as payload validity. Never hand-validate emitted payload JSON after SPX accepts it.
- Start the verification run immediately after validating the request, before reading changed project files or loading any language concern skill or its standards. Every project inspection and concern result belongs to the open run.

</constraints>

<audit_workflow>

<request_contract>

The invocation request `$ARGUMENTS` carries:

- Repository path.
- Changeset scope as `<base>..<head>` for `--scope`.
- Optional explicit live file list for advisory pre-commit audits, including modified and untracked files that are not yet part of `<head>`. A run with a live file list never satisfies an apply or merge gate.
- Governing node paths and any explicit file-list partition supplied with the request.
- Deterministic verification already run, or the concrete reason the audit is intentionally blocked before verification.
- Run-driver identity using the six published producer fields: producer kind, agent name, agent-owning plugin name, skill name, skill-owning plugin name, and invocation role.

`$ARGUMENTS` carries those fields with these exact labels:

```text
Repository: <absolute-repository-path>
Scope: <base>..<head> committed changeset scope
Live file list: none for a gating audit; <full modified and untracked paths> for an advisory audit
Governing node(s): <full spx/... paths>
Deterministic verification already run: <commands and results, or blocking reason>
Run driver identity: <one JSON object with the six published producer fields>
```

If `$ARGUMENTS` is empty or lacks repository path, changeset scope, governing nodes, deterministic verification state, or run-driver identity, return BLOCKED before starting a verification run. Name the missing request fields and the exact `$ARGUMENTS` shape required to retry.

Use the supplied changeset scope and explicit live file list exactly. Do not derive a different base, widen to the whole repository, drop uncommitted files, or collapse the scope to only one file unless the request supplied that exact scope. A gate-eligible request addresses an exact committed head and supplies no live file list. For an advisory pre-commit audit, record the live file list in the `--input` payload at run start and in scope payloads so SPX persistence preserves the files inspected, while reporting that the run cannot satisfy a gate.

</request_contract>

<verification_run_contract>

After validating the request, start one audit run as the first audit action. Do
this before loading language concern standards, inspecting the changeset, or
invoking concern skills, so the returned run token identifies the in-flight
audit from its beginning:

```bash
spx verification run start \
  --verification-type audit \
  --scope-type changeset \
  --scope <base>..<head> \
  --input stdin
```

The `--input` payload carries the request, deterministic verification state, governing nodes, and any explicit live file list supplied for pre-commit audits. The command returns a JSON locator; extract its `runToken` field exactly and use that token for every later command. Never pass the whole JSON locator as `--run`.

Execute every state-changing `spx verification run` command serially. A tool
response or tool-call batch contains at most one `start`, `scope add`, `finding
add`, or `finish` command for a run. Wait for that command to exit and preserve
its result before issuing the next mutation in a later response. NEVER place two
journal mutations in a parallel tool group, multi-call batch, shell background
group, or concurrently executing concern. Parallel concern analysis emits no
SPX commands; the run driver queues its completed results and persists them one
at a time. Parallel writes can race sequence assignment and produce a sealed
projection whose event prefix is neither strictly increasing nor contiguous.
Render only after `finish` exits successfully.

Every scope payload uses the published SPX field names below. Emit one scope
unit per subject path and concern partition; `subject` and
`priorContext.changedFilePartition` are strings, never path arrays. Emit only
the fields shown. The `producerProvenance` object is optional for a scope unit
and is omitted for `coverage-gap`; when present, both plugin-version fields are
required.

```json
{
  "unitId": "<stable-scope-key>",
  "auditClass": "implementation",
  "auditKind": "<code|tests|architecture|coverage-gap>",
  "subject": "<single-subject-path-or-explicit-gap-marker>",
  "coverageRequirement": "<required|optional>",
  "coverageStatus": "<audited|not-applicable|unsupported|missing-skill|skipped|incomplete>",
  "priorContext": {
    "changedFilePartition": "<single-subject-path-or-explicit-gap-marker>",
    "languagePartition": "<language-when-known>",
    "concernPartition": "<code|tests|architecture>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<run-driver-agent-name>",
    "agentOwningPluginName": "<run-driver-agent-owning-plugin-name>",
    "skillName": "audit-<lang>-<concern>",
    "skillOwningPluginName": "<lang>",
    "invocationRole": "leaf-skill"
  },
  "recordedByRunDriver": {
    "producerKind": "<run-driver-producer-kind>",
    "agentName": "<run-driver-agent-name>",
    "agentOwningPluginName": "<run-driver-agent-owning-plugin-name>",
    "skillName": "<run-driver-skill-name>",
    "skillOwningPluginName": "<run-driver-skill-owning-plugin-name>",
    "invocationRole": "<run-driver-invocation-role>"
  },
  "producerProvenance": {
    "agentOwningPluginVersion": "<spec-tree-plugin-version>",
    "skillOwningPluginVersion": "<language-plugin-version>",
    "toolVersion": "<spx-version-when-known>"
  }
}
```

`languagePartition` is the only optional prior-context field. Omit it when the
language is unknown; never replace `priorContext` with top-level partition
fields. Use `coverage-gap` for a missing producer or unsupported subject and
omit `producerProvenance` because no leaf skill executed.

Every finding payload uses the exact published SPX field names below. Its
`unitId` references a scope unit already accepted by the run, its
`producerIdentity` matches that unit's `expectedProducer`, and observed versus
expected text lives under `evidence`.

```json
{
  "unitId": "<accepted-scope-unit-id>",
  "producerIdentity": {
    "producerKind": "skill",
    "agentName": "<run-driver-agent-name>",
    "agentOwningPluginName": "<run-driver-agent-owning-plugin-name>",
    "skillName": "audit-<lang>-<concern>",
    "skillOwningPluginName": "<lang>",
    "invocationRole": "leaf-skill"
  },
  "producerProvenance": {
    "agentOwningPluginVersion": "<spec-tree-plugin-version>",
    "skillOwningPluginVersion": "<language-plugin-version>",
    "toolVersion": "<spx-version-when-known>"
  },
  "rule": "<violated-rule-or-principle>",
  "severity": "<blocking|debt>",
  "location": "<path-and-line-or-subject-location>",
  "message": "<finding-message>",
  "evidence": {
    "observed": "<observed-state>",
    "expected": "<required-state>"
  }
}
```

The idempotency key is a command argument, never a payload field. Never emit
the retired aliases `id`, `subjectPaths`, `expectedProducerIdentity`,
`executionProducerIdentity`, `stableProducerIdentity`, top-level `observed`,
or top-level `expected`; SPX rejects or discards those shapes at the
verification-type boundary.

Choose the stdin form by harness for every `--input stdin` and
`--payload stdin` command. Interactive Claude Code and Codex sessions use a
quoted heredoc after replacing the placeholder with one rendered JSON object
from the contracts above:

```bash
spx verification run scope add \
  --verification-type audit \
  --scope-type changeset \
  --scope <base>..<head> \
  --run <token> \
  --payload stdin \
  --idempotency-key <stable-scope-key> <<'JSON'
<rendered-scope-json-on-one-or-more-lines>
JSON
```

Programmatic Claude Code and Codex runners, including hosted runners that
require one physical command line, use `printf` with the rendered JSON as one
single-quoted argument. Keep the pipeline on one physical line even when it
wraps visually; encode a literal apostrophe with the single-quote splice
`'"'"'`:

```bash
printf '%s\n' '<rendered-json-on-one-line>' | spx verification run scope add --verification-type audit --scope-type changeset --scope <base>..<head> --run <token> --payload stdin --idempotency-key <stable-scope-key>
```

Apply the same two forms to `run start --input stdin` and `finding add
--payload stdin`. Never assemble or repair a payload through a temporary file,
helper file, command substitution, or post-hoc text substitution.

```bash
spx verification run scope add \
  --verification-type audit \
  --scope-type changeset \
  --scope <base>..<head> \
  --run <token> \
  --payload stdin \
  --idempotency-key <stable-scope-key>

spx verification run finding add \
  --verification-type audit \
  --scope-type changeset \
  --scope <base>..<head> \
  --run <token> \
  --payload stdin \
  --idempotency-key <stable-finding-key>

spx verification run finish \
  --verification-type audit \
  --scope-type changeset \
  --scope <base>..<head> \
  --run <token> \
  --terminal-status <evidence-derived-status>

spx verification run render \
  --verification-type audit \
  --scope-type changeset \
  --scope <base>..<head> \
  --run <token>
```

The final response relays the rendered SPX projection and run token. Do not summarize findings from memory when the render is available.

</verification_run_contract>

<coverage_model>

Build an expected coverage inventory before invoking any language concern skill. Discover programming-language plugins from installed `code-{lang}` skill names, then validate the complete read-only `audit-{lang}-{code|tests|architecture}` trio for each discovered language before invoking any concern. Never load a write-capable `code-{lang}` skill inside the audit, and never create a language partition from a file extension, filename, or artifact class alone.

Only paths claimed by a discovered programming-language implementation skill belong to implementation-audit coverage. Leave every other artifact class to its artifact-type auditor and the whole-changeset review; do not manufacture a language name, missing concern skill, unsupported unit, or coverage gap for a path outside implementation-audit ownership.

Give every complete trio the supplied scope exactly. Each read-only concern skill owns language-specific applicability and identifies the subject paths it audited or returns `NOT_APPLICABLE`; the orchestration never substitutes its own file-pattern table. Build the pre-invocation inventory by discovered language and concern, then expand each concern's result into subject-path units when its final coverage status is known. A discovered language with an incomplete trio records the missing required concerns and rejects the run.

Each expected unit records:

- audit class: `implementation`
- audit kind: `code`, `tests`, or `architecture`
- language partition
- concern partition: `code`, `tests`, or `architecture`
- one project path inspected by the concern, or an explicit unsupported-file marker; every inspected path becomes one SPX scope unit whose preserved `subject` field is that exact path
- stable `expectedProducer` identity using the six published producer fields
- optional `producerProvenance` using both owning-plugin versions and optional SPX tool version when a concern skill executed
- `recordedByRunDriver` identity for the SPX command driver, present for every unit so missing-skill and unsupported classifications still identify the recorder
- coverage requirement: `required` or `optional`
- coverage status: `audited`, `not-applicable`, `unsupported`, `missing-skill`, `skipped`, or `incomplete`
- concern result: completion is represented by every expected path unit carrying `coverageStatus: audited`, and the finding count is the count of accepted finding rows for those path-scoped units

Plan the complete inventory before invoking any concern skill, but NEVER mark a planned unit `audited`. Queue each unit only when its final coverage status is known: immediately for a classified gap, or after the corresponding concern finishes for an executed producer. A concern skill returns its result to the run driver and never writes SPX state itself. After a concern returns, queue one path-scoped row per inspected path with a stable path-scoped unit id, the exact path in `subject`, and `coverageStatus: audited`; queue each returned finding after those scope rows and associate it with the matching path-scoped unit. Persist queued units with one `spx verification run scope add` command at a time, ordered by language discovery order and then concern order `code`, `tests`, `architecture`; preserve each command result before issuing the next mutation. Derive the concern's finding count from the accepted finding rows; do not emit a custom count SPX discards. Never append a preliminary required `incomplete` unit that later becomes audited; every accepted required uncovered event rejects the terminal rollup permanently. When a concern cannot return a complete result, queue `incomplete` or the applicable non-audited status; never manufacture a completed result from the orchestration's own inspection.

A missing required concern skill, unsupported path already claimed by a recognized implementation-language partition, or required unit that receives no concern result rejects the run through accepted coverage status and the evidence-derived terminal rollup. Do not continue concern dispatch after detecting an absent required skill for a recognized language partition; queue the complete final gap inventory, persist it serially, finish, and render the rejected run. An SPX command or payload rejection is a command failure and returns BLOCKED under `<verdict_format>` rather than becoming coverage evidence.

When the request supplies an explicit live file list, pass that list as the exact advisory scope to every complete concern trio rather than inspecting the committed changeset alone. A live path claimed by a recognized implementation-language concern that receives no result is a coverage gap even when it is absent from `<head>`; an artifact outside every implementation concern remains outside implementation-audit ownership.

</coverage_model>

<skill_map>

For each language partition, invoke the required implementation concern skills:

| Concern      | Dispatch template           |
| ------------ | --------------------------- |
| Code         | `audit-{lang}-code`         |
| Tests        | `audit-{lang}-tests`        |
| Architecture | `audit-{lang}-architecture` |

The dispatch contract is the skill name. The orchestration does not embed per-language file globs, commands, test naming, architecture examples, or local standards. Each concern skill owns its policy and returns findings for its concern only.

</skill_map>

<finding_model>

Record each accepted concern finding through `spx verification run finding add`. The payload includes:

- stable producer identity matching the coverage unit
- producer provenance, including owning plugin version when present
- unit identity for a scope unit already recorded in the run
- rule or violated principle
- severity: `blocking` or `debt`
- location
- message
- observed-versus-expected evidence

Finding identity for convergence is content and stable producer identity, not plugin version. Version changes preserve provenance without making the same finding look new.

</finding_model>

<terminal_model>

Finish the run only after every required coverage unit is `audited`, `not-applicable`, `unsupported`, `missing-skill`, `skipped`, or `incomplete`, and after every finding has been recorded. Record missing required skills, unsupported paths claimed by recognized implementation-language partitions, finding counts, and deterministic verification state in accepted scope and finding payload fields instead of terminal metadata.

Compute the terminal status from accepted coverage and finding evidence: `approved` when every required non-gap unit is `audited` or `not-applicable` and no finding exists; `rejected` when a required unit is uncovered or any finding exists. Pass that evidence-derived value through `finish --terminal-status`. Do not pass terminal metadata for audit runs; the run's coverage and findings already carry the facts behind the terminal value.

If SPX rejects terminal status, report the rejected command and stderr as the audit result. Do not manufacture a prose fallback.

</terminal_model>

</audit_workflow>

<verdict_format>

When the run completes, return the exact run token and rendered `spx verification run render` projection. The projection's `terminalStatus` is authoritative: `approved` passes and `rejected` requires repair. Do not add an `APPROVED` or `REJECTED` prose envelope.

Return BLOCKED only when the invocation request is malformed before `spx verification run start` or SPX rejects a command. For malformed requests, name the absent labeled fields from `<request_contract>`. For command failures, include the exact command, stderr, and the coverage unit or payload key that failed. After a run starts, record a missing required concern skill as `missing-skill`, finish the run with terminal status `rejected`, render it, and return the run token plus projection.

Use this complete blocked diagnostic after any SPX command failure; preserve
each value verbatim from the invocation and command result:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-command-with-selectors-and-no-invented-redaction>
payloadSource: <stdin|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code>
stderr: <exact-stderr>
```

Never return the command alone. The run token locates durable state, the
payload source and key identify the rejected boundary, and the exit code plus
stderr carry the failure evidence.

Each finding row names:

- stable producer identity
- producer provenance when present
- unit identity
- rule or violated principle
- severity
- location
- message
- observed-versus-expected evidence

The rendered SPX projection is the inspection surface. Do not hand-format a competing verdict when `spx verification run render` succeeds.

</verdict_format>

<failure_modes>

**The request was empty or malformed.**

What happened: Claude received no `$ARGUMENTS`, or `$ARGUMENTS` omitted repository path, changeset scope, governing nodes, deterministic verification state, or run-driver identity.

Why it failed: Starting a verification run without the required selector fields creates durable audit state that cannot be tied to the intended scope.

How to avoid: Return BLOCKED before `spx verification run start`, name the missing request fields, and request the exact `$ARGUMENTS` shape from `<request_contract>`.

**A missing concern skill appeared after one concern already ran.**

What happened: Claude invoked one concern skill before validating that the complete `audit-{lang}-{code|tests|architecture}` trio existed for every language partition.

Why it failed: The coverage inventory belongs before concern dispatch, so a late missing-skill discovery can leave other concern results without a complete expected-unit classification.

How to avoid: Validate and record the complete concern-skill trio for every language partition before invoking any concern skill. Record an absent required skill as `missing-skill`, then finish and render the rejected run.

**Every changed file extension became a required language partition.**

What happened: Claude treated documentation and manifest suffixes as programming languages, required concern skills that do not exist, rejected the run before dispatch, and skipped an installed implementation-language concern trio.

Why it failed: Implementation-audit ownership comes from installed `code-{lang}` skill surfaces and their scope guidance, not from the set of suffixes present in a changeset. Artifact-specific auditors and whole-changeset review own files outside those programming-language surfaces.

How to avoid: Discover languages from installed `code-{lang}` skills, validate the required concern trio for every discovered language before dispatch, then let each complete concern trio claim applicable paths or return `NOT_APPLICABLE`; omit non-implementation artifacts from the coverage inventory.

**A finding was reported only in prose.**

What happened: Claude named a concern finding in text without recording it through `spx verification run finding add`.

Why it failed: Prose findings are not durable evidence and cannot appear in the rendered SPX projection.

How to avoid: Record every finding through `spx verification run finding add`; use the rendered projection as the inspection surface.

**Coverage labels replaced concern execution.**

What happened: Claude inspected changed files before opening the verification run, then emitted three scope rows labeled `audited` with generic partition subjects and no observable concern-skill results.

Why it failed: An `audited` label asserted completion without naming the inspected paths or preserving the concern invocation that produced the judgment. The sealed projection could not distinguish a completed concern audit from orchestration self-certification.

How to avoid: Start the run before project inspection and invoke each concern skill while the run is open. After a concern returns, record one accepted scope row per inspected path using the exact path in `subject` and `priorContext.changedFilePartition`, then record every finding with the accepted path-scoped `unitId`. Assign `coverageStatus: audited` only to those completed path-scoped rows; never emit custom concern-result fields.

**Scope events were persisted concurrently.**

What happened: Claude launched multiple `spx verification run scope add` commands at the same time. The sealed render carried duplicate sequence numbers and skipped the intervening sequence even though the terminal status was approved.

Why it failed: Concurrent mutations raced the journal's sequence assignment, so the rendered event prefix violated the strictly increasing, contiguous sequence contract.

How to avoid: Execute every state-changing `spx verification run` command serially and wait for its exit before issuing the next mutation for that run.

**An implementation code scope used semantic aliases instead of SPX fields.**

What happened: Claude submitted `id`, `subjectPaths`,
`expectedProducerIdentity`, and `executionProducerIdentity` for a code unit.
`spx verification run scope add` exited `1` with
`spx verification run scope add payload failed verification-type validation`,
then Claude returned only the command and dropped the run token, exit code, and
stderr.

Why it failed: The published scope contract requires `unitId`, one string
`subject`, nested `priorContext`, `expectedProducer`, and
`recordedByRunDriver`. A command-only fallback also discarded the
evidence needed to reproduce the rejected payload boundary.

How to avoid: Construct scope and finding payloads from the exact JSON contracts
in `<verification_run_contract>` and relay the complete blocked diagnostic from
`<verdict_format>` without reformatting or omission.

**Deterministic verification ran inside the audit.**

What happened: Claude ran validation, tests, or evals during implementation-audit orchestration.

Why it failed: This orchestration composes agentic concern audits only; running deterministic verification changes the audit boundary.

How to avoid: Stop and return the boundary failure with the deterministic command that was attempted.

</failure_modes>

<success_criteria>

- The verdict covers every required implementation concern for every language partition in the supplied scope: code, tests, and architecture.
- A completed run returns the raw run token and rendered projection with no competing prose verdict; the projection's `terminalStatus` is the sole determination (`approved` or `rejected`). A missing required concern skill after run start appears as `missing-skill` rejected coverage in that projection. A blocked run names the exact malformed request field or failed SPX command that prevented a valid completed projection.
- Every rejected finding is falsifiable: it names the stable producer identity, unit, violated rule or principle, severity, location, message, and observed-versus-expected evidence.
- Every missing-skill, unsupported-path, or coverage-gap unit within a recognized implementation-language partition appears in the rendered projection rather than being hidden in prose; artifacts outside implementation-audit ownership produce no fabricated coverage unit.
- Every audited concern preserves its complete non-empty inspected-path set as path-scoped units whose `subject` fields are the exact paths; every expected unit is audited only after the concern completes, and its finding count derives from accepted finding rows rather than a custom field.
- The same request, live file list, scope, and installed plugin versions produce the same coverage units, finding identities, and terminal determination.
- A gating run addresses a committed head with no live file list; a run carrying modified or untracked files identifies itself as advisory and is never presented as gate evidence.
- No plugin-side verdict script, legacy journal command, deterministic verification command, or language-specific file pattern can affect the determination outside the SPX-recorded run.

</success_criteria>
