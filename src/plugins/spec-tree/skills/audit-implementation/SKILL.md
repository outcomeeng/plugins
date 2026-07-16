---
name: audit-implementation
description: >-
  Implementation-audit orchestration methodology preloaded by the
  implementation-auditor agent. Dispatch implementation-auditor for
  implementation audits; the main conversation reaches this audit only through
  that agent.
argument-hint: "<implementation audit request>"
allowed-tools: Read, Glob, Grep, Skill, Bash(spx verification run:*)
---

<dispatch_gate>

This orchestration runs in the `implementation-auditor` agent's isolated context. When this skill loads in the main conversation rather than inside a dispatched implementation-auditor agent, STOP — dispatch `implementation-auditor` with the repository path, concrete changeset scope, governing node paths, and deterministic verification already run. The separate context keeps the verdict free of the bias the main conversation accumulates while doing the work under audit. An already-dispatched implementation-auditor that preloaded this skill proceeds.

</dispatch_gate>

<objective>

A rendered SPX verification-run verdict for the requested implementation scope, accompanied by its raw run token, with `terminalStatus` set to `approved` or `rejected` and each finding naming the stable producer identity, unit, violated rule, severity, location, message, and observed-versus-expected evidence.

</objective>

<constraints>

- Read-only over the audited project tree. This skill never edits source, tests, specs, commits, branches, or pull requests.
- Persist audit state only through `spx verification run`; never use legacy journal commands, plugin-side verdict scripts, markdown comments, `.spx/audits/`, or tracked files as audit state.
- Run no deterministic verification. The main conversation passes validate, test, and evaluate over the changeset before dispatch; CI repeats deterministic verification over the repository.
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
- Governing node paths and any explicit file-list partition the caller already resolved.
- Deterministic verification already run, or the concrete reason the audit is intentionally blocked before verification.

The wrapper passes those fields with these exact labels:

```text
Repository: <absolute-repository-path>
Scope: <base>..<head> committed changeset scope
Live file list: none for a gating audit; <full modified and untracked paths> for an advisory audit
Governing node(s): <full spx/... paths>
Deterministic verification already run: <commands and results, or blocking reason>
```

If `$ARGUMENTS` is empty or lacks repository path, changeset scope, governing nodes, or deterministic verification state, return BLOCKED before starting a verification run. Name the missing request fields and the exact wrapper prompt shape required to retry.

Use the caller's changeset scope and explicit live file list exactly. Do not derive a different base, widen to the whole repository, drop uncommitted files, or collapse the scope to only one file unless the caller supplied that exact scope. A gate-eligible request addresses an exact committed head and supplies no live file list. For an advisory pre-commit audit, record the live file list in the `--input` payload at run start and in scope payloads so SPX persistence preserves the files inspected, while reporting that the run cannot satisfy a gate.

</request_contract>

<verification_run_contract>

Start one audit run before invoking concern skills:

```bash
spx verification run start \
  --verification-type audit \
  --scope-type changeset \
  --scope <base>..<head> \
  --input stdin
```

The `--input` payload carries the caller request, deterministic verification state, governing nodes, and any explicit live file list supplied for pre-commit audits. The command returns a JSON locator; extract its `runToken` field exactly and use that token for every later command. Never pass the whole JSON locator as `--run`.

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

Build an expected coverage inventory before invoking any language concern skill. Each expected unit records:

- audit class: `implementation`
- audit kind: `code`, `tests`, or `architecture`
- language partition
- concern partition: `code`, `tests`, or `architecture`
- the complete non-empty list of project paths inspected by the concern, or an explicit unsupported-file marker; each path becomes one SPX scope unit whose preserved `subject` field is that exact path
- stable expected-producer identity: plugin name, skill name, audit class, language, and concern
- producer provenance: owning plugin version when the concern skill exists; null with reason `missing-skill` or `unsupported` when no executable concern skill can run
- execution producer identity: the wrapper and SPX command driver that recorded the unit, present for every unit so missing-skill and unsupported classifications still have provenance for the recorder
- coverage requirement: `required` or `optional`
- coverage status: `audited`, `not-applicable`, `unsupported`, `missing-skill`, `skipped`, or `incomplete`
- concern result: completion is represented by every expected path unit carrying `coverageStatus: audited`, and the finding count is the count of accepted finding rows for those path-scoped units

Plan the complete inventory before dispatch, but NEVER mark a planned unit `audited`. Invoke each concern skill inside the open run. After that concern returns, immediately record one path-scoped row per inspected path with a stable path-scoped unit id, the exact path in `subject`, and `coverageStatus: audited` before inspecting the next concern. Record each returned finding immediately after those scope rows and associate it with the matching path-scoped unit. Derive the concern's finding count from the accepted finding rows; do not emit a custom count SPX discards. When a concern cannot return a complete result, record `incomplete` or the applicable non-audited status; never manufacture a completed result from the orchestration's own inspection.

A missing required concern skill, unsupported implementation file, or required unit that receives no concern result rejects the run through accepted coverage status and the evidence-derived terminal rollup. Do not continue concern dispatch after detecting an absent required skill for a language partition; finish and render the rejected run after the complete expected inventory is recorded. An SPX command or payload rejection is a command failure and returns BLOCKED under `<verdict_format>` rather than becoming coverage evidence.

When the caller supplied an explicit live file list, build the expected coverage inventory from that list rather than from the committed changeset alone. A live file that receives no concern result is a coverage gap even when it is absent from `<head>`.

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

Finish the run only after every required coverage unit is `audited`, `not-applicable`, `unsupported`, `missing-skill`, `skipped`, or `incomplete`, and after every finding has been recorded. Record missing required skills, unsupported files, finding counts, and deterministic verification state in accepted scope and finding payload fields instead of terminal metadata.

Compute the terminal status from accepted coverage and finding evidence: `approved` when every required non-gap unit is `audited` or `not-applicable` and no finding exists; `rejected` when a required unit is uncovered or any finding exists. Pass that evidence-derived value through `finish --terminal-status`. Do not pass terminal metadata for audit runs; the run's coverage and findings already carry the facts behind the terminal value.

If SPX rejects terminal status, report the rejected command and stderr as the audit result. Do not manufacture a prose fallback.

</terminal_model>

</audit_workflow>

<verdict_format>

When the run completes, return the exact run token and rendered `spx verification run render` projection. The projection's `terminalStatus` is authoritative: `approved` passes and `rejected` requires repair. Do not add an `APPROVED` or `REJECTED` prose envelope.

Return BLOCKED only when the invocation request is malformed before `spx verification run start` or SPX rejects a command. For malformed requests, name the absent labeled fields from `<request_contract>`. For command failures, include the exact command, stderr, and the coverage unit or payload key that failed. After a run starts, record a missing required concern skill as `missing-skill`, finish the run with terminal status `rejected`, render it, and return the run token plus projection.

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

**Main conversation invoked this skill directly.**

What happened: Claude loaded the implementation-audit skill in the authoring conversation instead of dispatching `implementation-auditor`.

Why it failed: Running the audit inside the authoring context reintroduces the bias the verifier context exists to remove.

How to avoid: Stop at `<dispatch_gate>` and dispatch `implementation-auditor` with repository path, changeset scope, governing nodes, and deterministic verification state.

**The request was empty or malformed.**

What happened: Claude received no `$ARGUMENTS`, or the wrapper request omitted repository path, changeset scope, governing nodes, or deterministic verification state.

Why it failed: Starting a verification run without the required selector fields creates durable audit state that cannot be tied to the intended scope.

How to avoid: Return BLOCKED before `spx verification run start`, name the missing request fields, and request the exact wrapper prompt shape from `<request_contract>`.

**A missing concern skill appeared after one concern already ran.**

What happened: Claude invoked one concern skill before validating that the complete `audit-{lang}-{code|tests|architecture}` trio existed for every language partition.

Why it failed: The coverage inventory belongs before concern dispatch, so a late missing-skill discovery can leave other concern results without a complete expected-unit classification.

How to avoid: Validate and record the complete concern-skill trio for every language partition before invoking any concern skill. Record an absent required skill as `missing-skill`, then finish and render the rejected run.

**A finding was reported only in prose.**

What happened: Claude named a concern finding in text without recording it through `spx verification run finding add`.

Why it failed: Prose findings are not durable evidence and cannot appear in the rendered SPX projection.

How to avoid: Record every finding through `spx verification run finding add`; use the rendered projection as the inspection surface.

**Coverage labels replaced concern execution.**

What happened: Claude inspected changed files before opening the verification run, then emitted three scope rows labeled `audited` with generic partition subjects and no observable concern-skill results.

Why it failed: An `audited` label asserted completion without naming the inspected paths or preserving the concern invocation that produced the judgment. The sealed projection could not distinguish a completed concern audit from orchestration self-certification.

How to avoid: Start the run before project inspection, invoke each concern skill while the run is open, and assign `audited` only after recording that concern's exact `subjectPaths` and completed `concernResult`.

**Deterministic verification ran inside the audit.**

What happened: Claude ran validation, tests, or evals from the dispatched audit context.

Why it failed: Validation, tests, and evals are caller and CI responsibilities, and repeating them inside the audit changes the audit boundary.

How to avoid: Stop and return the boundary failure with the deterministic command that was attempted.

</failure_modes>

<success_criteria>

- The verdict covers every required implementation concern for every language partition in the caller's scope: code, tests, and architecture.
- A completed run returns the raw run token and rendered projection with no competing prose verdict; the projection's `terminalStatus` is the sole determination (`approved` or `rejected`). A blocked run names the exact failed request field or SPX command that prevented a valid completed projection; a missing concern skill appears as `missing-skill` in a rendered rejected run.
- Every rejected finding is falsifiable: it names the stable producer identity, unit, violated rule or principle, severity, location, message, and observed-versus-expected evidence.
- Every missing-skill, unsupported-file, or coverage-gap unit appears in the rendered projection rather than being hidden in prose.
- Every audited concern preserves its complete non-empty inspected-path set as path-scoped units whose `subject` fields are the exact paths; every expected unit is audited only after the concern completes, and its finding count derives from accepted finding rows rather than a custom field.
- The same caller request, live file list, scope, and installed plugin versions produce the same coverage units, finding identities, and terminal determination.
- A gating run addresses a committed head with no live file list; a run carrying modified or untracked files identifies itself as advisory and is never presented as gate evidence.
- No plugin-side verdict script, legacy journal command, deterministic verification command, or language-specific file pattern can affect the determination outside the SPX-recorded run.

</success_criteria>
