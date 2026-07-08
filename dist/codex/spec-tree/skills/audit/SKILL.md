---
name: audit
description: >-
  Implementation-audit orchestration methodology preloaded by the
  implementation-auditor agent. Dispatch implementation-auditor for
  implementation audits; the main conversation reaches this audit only through
  that agent.
argument-hint: "[scope]"
arguments: request
allowed-tools: Read, Bash, Glob, Grep, Skill
---

<dispatch_gate>

This orchestration runs in the `implementation-auditor` agent's isolated context. When this skill loads in the main conversation rather than inside a dispatched implementation-auditor agent, STOP — dispatch `implementation-auditor` with the repository path, concrete changeset scope, governing node paths, and deterministic verification already run. The separate context keeps the verdict free of the bias the main conversation accumulates while doing the work under audit. An already-dispatched implementation-auditor that preloaded this skill proceeds.

</dispatch_gate>

<objective>

A verdict on one implementation audit scope — APPROVED when every required language concern is covered with no rejected findings, or REJECTED with each finding naming the concern, subject, violated rule, and required fix.

</objective>

<constraints>

- Read-only over the audited project tree. This skill never edits source, tests, specs, commits, branches, or pull requests.
- Persist audit state only through `spx verification run`; never use legacy journal commands, plugin-side verdict scripts, markdown comments, `.spx/audits/`, or tracked files as audit state.
- Run no deterministic verification. The main conversation passes validate, test, and evaluate over the changeset before dispatch; CI repeats deterministic verification over the repository.
- Contain no language-specific file extensions, commands, examples, or evidence patterns beyond the dispatch template `audit-{lang}-{code|tests|architecture}`.
- Treat the `spx verification run` command exit code as payload validity. Never hand-validate emitted payload JSON after SPX accepts it.

</constraints>

<audit_workflow>

<request_contract>

The invocation request `$request` carries:

- Repository path.
- Changeset scope as `<base>..<head>` for `--scope`.
- Optional explicit live file list for pre-commit audits, including modified and untracked files that are not yet part of `<head>`.
- Governing node paths and any explicit file-list partition the caller already resolved.
- Deterministic verification already run, or the concrete reason the audit is intentionally blocked before verification.

Use the caller's changeset scope and explicit live file list exactly. Do not derive a different base, widen to the whole repository, drop uncommitted files, or collapse the scope to only one file unless the caller supplied that exact scope. For pre-commit `/apply` audits, record the live file list in the `--input` payload at run start and in scope payloads so SPX persistence preserves the files the audit actually gated.

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

The `--input` payload carries the caller request, deterministic verification state, governing nodes, and any explicit live file list supplied for pre-commit audits. Capture the returned run token exactly. Use that token for every later command:

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
  --terminal-status <spx-accepted-status> \
  --terminal-metadata stdin

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
- subject paths or explicit unsupported-file marker
- stable expected-producer identity: plugin name, skill name, audit class, language, and concern
- producer provenance: owning plugin version when the concern skill exists; null with reason `missing-skill` or `unsupported` when no executable concern skill can run
- execution producer identity: the wrapper and SPX command driver that recorded the unit, present for every unit so missing-skill and unsupported classifications still have provenance for the recorder
- coverage status: required, optional, missing-skill, unsupported, covered, rejected, or coverage-gap

Record the inventory with `spx verification run scope add` as soon as each unit is planned or classified. A missing required concern skill, unsupported implementation file, rejected SPX payload, or required unit that receives no concern result rejects the run through coverage status and terminal metadata. Do not continue after detecting an absent required skill for a language partition.

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
- audit class and kind
- language and concern partition
- subject path and optional line
- rule or violated principle
- message
- required fix

Finding identity for convergence is content and stable producer identity, not plugin version. Version changes preserve provenance without making the same finding look new.

</finding_model>

<terminal_model>

Finish the run only after every required coverage unit is covered, rejected, missing, unsupported, or classified as a coverage gap. The terminal metadata carries:

- coverage totals by language and concern
- missing required skills
- unsupported files
- finding count by concern
- deterministic verification state supplied by the caller

If SPX rejects terminal status or metadata, report the rejected command and stderr as the audit result. Do not manufacture a prose fallback.

</terminal_model>

</audit_workflow>

<verdict_format>

Return one of these verdict forms:

- APPROVED with the exact run token and the rendered `spx verification run render` projection.
- REJECTED with the exact run token, rendered projection, and finding rows from the projection.
- BLOCKED when SPX rejects a command or a required skill is missing before dispatch. Include the exact command, stderr, and the coverage unit or payload key that failed.

Each finding row names:

- stable producer identity
- producer provenance when present
- audit class and kind
- language and concern partition
- subject path and optional line
- rule or violated principle
- message
- required fix

The rendered SPX projection is the inspection surface. Do not hand-format a competing verdict when `spx verification run render` succeeds.

</verdict_format>

<failure_modes>

**Main conversation invoked this skill directly.** Stop at `<dispatch_gate>` and dispatch `implementation-auditor`. Running the audit inside the authoring context reintroduces the bias the verifier context exists to remove.

**A missing concern skill appears after one concern already ran.** The coverage inventory belongs before concern dispatch. Validate the complete `audit-{lang}-{code|tests|architecture}` trio for every language partition before invoking any concern skill.

**A finding is reported only in prose.** Prose findings are not durable evidence. Every finding goes through `spx verification run finding add`; the rendered projection is the inspection surface.

**Deterministic verification runs inside the audit.** Stop and return the boundary failure. Validation, tests, and evals are caller and CI responsibilities, not work a dispatched audit repeats.

</failure_modes>

<success_criteria>

- The verdict covers every required implementation concern for every language partition in the caller's scope: code, tests, and architecture.
- The verdict states an explicit overall determination: APPROVED, REJECTED, or BLOCKED.
- Every rejected finding is falsifiable: it names the stable producer identity, subject, violated rule or principle, evidence message, and required fix.
- Every missing-skill, unsupported-file, or coverage-gap unit appears in the rendered projection rather than being hidden in prose.
- The same caller request, live file list, scope, and installed plugin versions produce the same coverage units, finding identities, and terminal determination.
- No plugin-side verdict script, legacy journal command, deterministic verification command, or language-specific file pattern can affect the determination outside the SPX-recorded run.

</success_criteria>
