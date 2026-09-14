---
name: audit-implementation
description: >-
  Implementation audit methodology — judges a changeset's implementation
  against its governing decisions, specs, and language standards, covering
  per-language code, test, and architecture concerns, finding falsifiability,
  and completeness of the inspection.
argument-hint: "<scope>"
allowed-tools: Read, Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_scope.py":*), Bash(git rev-parse:*), Bash(git status:*), Bash(git show:*), Bash(spx verification run:*), Bash(printf:*), Glob, Grep, Skill
---

<objective>

An authoritative SPX projection and raw run token for the requested implementation scope, carrying `terminalStatus` (`approved` or `rejected`) and findings that name the artifact, the violated rule, and observed-versus-expected evidence. A run that cannot reach that projection yields a `BLOCKED` diagnostic naming the request failure, command failure, or absent prerequisite that stopped it.

</objective>

<constraints>

- NEVER edit source, tests, specs, commits, branches, or pull requests — this orchestration is read-only over the audited project tree.
- ALWAYS persist audit state through `spx verification run`; NEVER use legacy journal commands, plugin-side verdict scripts, markdown comments, `.spx/audits/`, or tracked files as audit state.
- NEVER run deterministic verification — this orchestration composes agentic concern audits only.
- NEVER include language-specific file extensions, commands, examples, or evidence patterns beyond the dispatch template `audit-{lang}-{code|tests|architecture}`.
- ALWAYS treat the `spx verification run` command exit code as payload validity; NEVER hand-validate emitted payload JSON after SPX accepts it.
- NEVER end a run because work remains, time has passed, context is tight, or reading is unfinished — a stop names the failed command with its exit code and stderr, or the absent prerequisite.
- NEVER assign `incomplete` or `skipped` to a required coverage unit; neither describes an admissible terminal state for required coverage.
- NEVER derive a subject body from a single commit's patch, or leave a truncated read unrecovered — a partial read is re-issued, never converted into coverage evidence.
- ALWAYS start the verification run after resolving the target's Git metadata and validating the run-driver identity, before reading changed project file bodies or loading language concern standards — every substantive project inspection and concern result belongs to the open run.

</constraints>

<audit_workflow>

<execution_sequence>

Run these stages in order. Each names what holds before the next begins, and
`finish` is reachable only from stage 7.

1. **Anchor.** Resolve the repository, the scope selector, and the run-driver
   identity per `<request_contract>`. Retain the resolved `base` and `head`
   identities unchanged for the rest of the run.
2. **Open the run.** Start the run per `<verification_run_contract>` before any
   project inspection or standards load, so every later stage belongs to it.
3. **Load.** Read each discovered governing node's context, each concern's
   governing standards, and the audited repository's declared `spx/local/`
   overlays.
4. **Enumerate.** Build the complete expected coverage inventory per
   `<coverage_model>` before invoking any concern. A unit enters the inventory
   planned and carries no status.
5. **Inspect.** Read each subject body completely from the resolved
   `base..head` scope. MUST re-issue a truncated or partial read in bounded
   ranges until the body is complete. NEVER derive a subject body from a single
   commit's patch, and NEVER treat an unrecovered read as coverage evidence.
6. **Resolve.** Hold each unit planned until its concern returns a final result.
   A required unit reaches only `audited`, `not-applicable`, `missing-skill`, or
   `unsupported`. NEVER accept a finding raised before stage 3 loaded that
   concern's standards and overlays — withdraw it rather than record it.
7. **Reconcile, then finish.** Confirm every planned unit carries a final status
   and every recorded finding references an accepted unit. A failed
   reconciliation returns the run to stage 5 or 6; it never authorizes `finish`.

A run that cannot bring a required unit to a stage 6 status returns the
`<verdict_format>` blocked diagnostic naming the concrete failed operation or
absent prerequisite. Remaining work, elapsed time, context pressure, and
unfinished reading are never such a cause.

</execution_sequence>

<request_contract>

Capture `$ARGUMENTS` as the target scope selector before discovery. The target
is one scope selector: `HEAD`, a branch, or an explicit three-dot
range. `worktree:` before a selector explicitly requests an advisory audit of
that committed scope plus the complete modified and untracked file set. Preserve
the selector verbatim. Never infer advisory intent from a dirty checkout.

Run-driver identity uses the six published producer fields in the invocation
context, separate from `$ARGUMENTS`. Accept that identity generically in direct and composed invocations;
never infer it from a role name, installed plugin, or descriptive text.

Before reading project file bodies:

1. Resolve the repository root with `git rev-parse --show-toplevel`.
2. For an advisory target, remove only its `worktree:` prefix. Resolve the
   remaining selector through the bundled consumer of `/scope-changeset`:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_scope.py" '{selector}' --repo '{repository-root}'
   ```

   Preserve its `base`, `head`, and `changed_paths`. Its three-dot changed paths
   define the subject; the full endpoint IDs form the SPX scope identity
   `{base}..{head}`. Never reinterpret that identity as a two-dot changed-file
   query or substitute a local base branch.
   Quote each substituted argument independently, applying the apostrophe
   splice documented below when its value contains a literal apostrophe.
3. Read `git status --porcelain=v1 -z --untracked-files=all` at the repository
   root. An advisory audit includes every reported modified or untracked path,
   consuming NUL-delimited paths and both paths of a rename or copy. A committed
   audit includes none of those live changes. Read committed subject bodies with
   `git show '{head}:{path}'` whenever the working file differs or the selected
   head is not the checkout's `HEAD`; never silently audit a different version.
   For a deleted path, inspect its base-side body and the committed deletion.
4. Validate the generic run-driver identity and retain already-established
   deterministic verification facts for this exact committed subject from the
   available context. When evidence is unavailable, record it as unestablished;
   never infer passing checks from a clean checkout or run them inside the audit.

A missing selector or identity, failed repository discovery, or failed scope
resolution returns `BLOCKED` with `runToken: not-started` and the exact missing
input or command failure. Make no replacement scope selection or retry.

Start the run after this metadata preparation. Then discover governing nodes
from the resolved paths through the spec-tree evidence links and declared audit
ownership, load their context read-only, and pass that discovered context to the
concern skills. Never synchronize, rebase, or otherwise mutate the audited
checkout. Preserve missing governance as coverage evidence under the existing
coverage model. A committed audit is reusable only when the applicable
deterministic verification is established as passing for that subject; an
advisory audit never supplies reusable gate evidence.

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

The `--input` payload carries the original selector, resolved repository and
committed scope, discovered live file list or `none`, available deterministic
verification facts, generic run-driver identity, and advisory status. Governing
nodes are discovered after start and accompany the concern inputs and coverage
evidence. The command returns a JSON locator; extract its `runToken` field exactly
and use that token for every later command. Never pass the whole JSON locator
as `--run`.

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
  "coverageStatus": "<audited|not-applicable|missing-skill|unsupported>",
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

The `coverageStatus` values above are the required-unit set. An optional unit
may additionally carry `skipped`; no unit carries `incomplete`.

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

The idempotency key is a command argument, never a payload field. A scope
unit's key is the value its payload carries in `unitId`: audit class, language
partition, concern partition, and subject path joined with `:` —
`implementation:<lang>:<concern>:<subject-path>`. A finding's key extends its
unit's key with the violated rule — `<stable-scope-key>:<rule>`.

Keep the rule segment colon-free. SPX never parses the key back into segments,
so a `:` inside a subject path is not a separator; a colon-free rule makes the
last `:` the boundary between subject path and rule, and a colon inside the rule
collides two distinct findings on one key.

The key always carries a language segment, even though
`priorContext.languagePartition` may be omitted. Render an unknown language as
the literal `unknown`; the key substitutes no default for a segment left out.

Pass every key as one single-quoted argument, `--idempotency-key
'<stable-scope-key>'` — a subject path can carry `|`, `&`, `;`, `(`, `)`, `<`,
`>`, `*`, `?`, or whitespace, and unquoted it splits the command so the shell
runs a fragment as a program. Encode a literal apostrophe with the single-quote
splice `'"'"'`.

Never emit the retired aliases `id`, `subjectPaths`, `expectedProducerIdentity`,
`executionProducerIdentity`, `stableProducerIdentity`, top-level `observed`,
or top-level `expected`; SPX rejects or discards those shapes at the
verification-type boundary.

Choose the stdin form by harness for every `--input stdin` and
`--payload stdin` command. Interactive sessions use a
quoted heredoc after replacing the placeholder with one rendered JSON object
from the contracts above:

```bash
spx verification run scope add \
  --verification-type audit \
  --scope-type changeset \
  --scope <base>..<head> \
  --run <token> \
  --payload stdin \
  --idempotency-key '<stable-scope-key>' <<'JSON'
<rendered-scope-json-on-one-or-more-lines>
JSON
```

Programmatic runners, including hosted runners that
require one physical command line, use `printf` with the rendered JSON as one
single-quoted argument. Keep the pipeline on one physical line even when it
wraps visually; encode a literal apostrophe with the same single-quote splice:

```bash
printf '%s\n' '<rendered-json-on-one-line>' | spx verification run scope add --verification-type audit --scope-type changeset --scope <base>..<head> --run <token> --payload stdin --idempotency-key '<stable-scope-key>'
```

Apply the same two forms to `run start --input stdin` and `finding add
--payload stdin`. Never assemble or repair a payload through a temporary file,
helper file, command substitution, or post-hoc text substitution.

```bash
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

Give every complete trio the resolved endpoint identities, exact three-dot
changed paths, discovered governing context, and advisory live file list when
requested. Require inspection of the selected committed bodies for committed
audits. Each read-only concern skill owns language-specific applicability and
identifies the subject paths it audited or returns `NOT_APPLICABLE`; the
orchestration never substitutes its own file-pattern table. Build the
pre-invocation inventory by discovered language and concern, then expand each
concern's result into subject-path units when its final coverage status is known.
A discovered language with an incomplete trio records the missing required
concerns and rejects the run.

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
- coverage status: `audited`, `not-applicable`, `missing-skill`, or `unsupported` for a required unit; an optional unit may additionally carry `skipped`
- concern result: completion is represented by every expected path unit carrying `coverageStatus: audited`, and the finding count is the count of accepted finding rows for those path-scoped units

- Plan the complete inventory before invoking any concern skill. NEVER mark a planned unit `audited`.
- Queue each unit only once its final coverage status is known: immediately for a classified gap, or after its concern finishes for an executed producer.
- NEVER append a preliminary required unit before its final coverage status is known — every accepted required uncovered event rejects the terminal rollup permanently.
- A concern skill returns its result to the run driver and never writes SPX state itself.
- After a concern returns, queue one path-scoped row per inspected path, carrying a stable path-scoped unit id, the exact path in `subject`, and `coverageStatus: audited`.
- Queue each returned finding after those scope rows, associated with its matching path-scoped unit.
- Persist queued units one `spx verification run scope add` command at a time, ordered by language discovery order then concern order `code`, `tests`, `architecture`, preserving each command result before the next mutation.
- Derive the concern's finding count from the accepted finding rows; NEVER emit a custom count SPX discards.
- A concern returning no complete result for a required unit MUST name the failed operation or absent prerequisite. When it names neither, drive the concern to a final result rather than recording a non-audited status.
- NEVER manufacture a completed result from the orchestration's own inspection.

A missing required concern skill or an unsupported path already claimed by a recognized implementation-language partition rejects the run through accepted coverage status and the evidence-derived terminal rollup. A required unit that receives no concern result reaches no admissible status, so the run returns BLOCKED under `<verdict_format>` naming the failed operation or absent prerequisite rather than sealing. Do not continue concern dispatch after detecting an absent required skill for a recognized language partition; queue the complete final gap inventory, persist it serially, finish, and render the rejected run. An SPX command or payload rejection is a command failure and returns BLOCKED under `<verdict_format>` rather than becoming coverage evidence.

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

Finish the run only after stage 7 of `<execution_sequence>` reconciles: every required coverage unit is `audited`, `not-applicable`, `missing-skill`, or `unsupported`, every finding is recorded, and every recorded finding references an accepted unit. Record missing required skills, unsupported paths claimed by recognized implementation-language partitions, finding counts, and deterministic verification state in accepted scope and finding payload fields instead of terminal metadata.

Compute the terminal status from accepted coverage and finding evidence: `approved` when every required non-gap unit is `audited` or `not-applicable` and no finding exists; `rejected` when a required unit is uncovered or any finding exists. Pass that evidence-derived value through `finish --terminal-status`. Do not pass terminal metadata for audit runs; the run's coverage and findings already carry the facts behind the terminal value.

If SPX rejects terminal status, report the rejected command and stderr as the audit result. Do not manufacture a prose fallback.

</terminal_model>

</audit_workflow>

<verdict_format>

When the run completes, return the exact run token and rendered `spx verification run render` projection. The projection's `terminalStatus` is authoritative: `approved` passes and `rejected` requires repair. Do not add an `APPROVED` or `REJECTED` prose envelope.

Return BLOCKED for three causes: target preparation fails before `spx
verification run start`, SPX rejects a command, or a required unit cannot reach
a final status after the run started. For missing input, name the selector or
identity field that is absent. For command failures, include the complete
diagnostic below; preparation failures use `runToken: not-started`,
`payloadSource: none`, and `payloadKey: none`.

A required unit that cannot reach a final status is not a command rejection, so
its diagnostic carries the started `runToken`, the absent prerequisite or failed
operation in `command` — the exact operation attempted, such as the unreadable
subject path or the governing node that could not be discovered — and
`payloadSource: none`, `payloadKey: none`, `exitCode: none`, `stderr: none`.
Name the unit by its `unitId` in the `command` line so the blocked unit is
identifiable. After a run starts, record a missing required concern skill
as `missing-skill`, finish with terminal status `rejected`, render, and return
the run token plus projection.

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

For a failed preparation, concern invocation, payload submission, or projection,
read [operational failure records](${CLAUDE_SKILL_DIR}/references/operational-failures.md)
to diagnose the observed boundary. Preserve the exact diagnostic and apply the
existing no-retry rule; these records authorize no replacement invocation.

</failure_modes>

<success_criteria>

- The verdict covers every required implementation concern for every language partition in the supplied scope: code, tests, and architecture.
- A completed run returns the raw run token and rendered projection with no competing prose verdict; the projection's `terminalStatus` is the sole determination (`approved` or `rejected`). A missing required concern skill after run start appears as `missing-skill` rejected coverage in that projection. A blocked run names the exact malformed request field or failed SPX command that prevented a valid completed projection.
- Every rejected finding is falsifiable: it names the stable producer identity, unit, violated rule or principle, severity, location, message, and observed-versus-expected evidence.
- Every missing-skill, unsupported-path, or coverage-gap unit within a recognized implementation-language partition appears in the rendered projection rather than being hidden in prose; artifacts outside implementation-audit ownership produce no fabricated coverage unit.
- Every audited concern preserves its complete non-empty inspected-path set as path-scoped units whose `subject` fields are the exact paths; every expected unit is audited only after the concern completes, and its finding count derives from accepted finding rows rather than a custom field.
- The same request, committed scope, normalized live file list, and installed plugin versions produce the same coverage units, finding identities, and terminal determination.
- Every gate-eligible run addresses an exact committed head with no live-file additions and established passing deterministic evidence; an explicit `worktree:` target includes the complete discovered modified and untracked path list and supplies no reusable gate evidence.
- Every sealed run reconciles before finishing: every required unit carries `audited`, `not-applicable`, `missing-skill`, or `unsupported`, every finding references an accepted unit, and every subject body was read complete from the resolved `base..head` scope. A run that reaches none of those for a required unit returns the blocked diagnostic naming a concrete failed operation or absent prerequisite, never a sealed projection.
- No plugin-side verdict script, legacy journal command, deterministic verification command, or language-specific file pattern can affect the determination outside the SPX-recorded run.

</success_criteria>
