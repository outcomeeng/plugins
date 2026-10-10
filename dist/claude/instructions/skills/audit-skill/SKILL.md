---
name: audit-skill
description: >-
  SKILL.md audit methodology — judges the skill-bundle files and included
  shared fragments a changeset changes against the skill-standards and agent-prompt-standards rule catalogs,
  and records the judgment through an SPX changeset-scoped verification run.
argument-hint: "<JSON object with path, runDriver, and optional base>"
allowed-tools: Read, Grep, Glob, Skill, Bash(python3 -c 'from pathlib import Path; import sys; print(len(Path(sys.argv[1]).read_text(encoding="utf-8")))':*), Bash(git rev-parse:*), Bash(git diff:*), Bash(git status:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

Use skill `instructions:skill-standards`.

Use skill `instructions:agent-prompt-standards`.

<objective>
A sealed changeset-scoped `spx verification run` over the files a changeset changes in one skill bundle and the shared fragments it includes, judged against the `/skill-standards` and `/agent-prompt-standards` rule catalogs — terminal status `approved` when no finding on touched text exists, or `rejected` with each such finding keyed `<unit>:<rule-id>` and naming every location and the evidence, every other finding recorded as `filed` — or a `BLOCKED` diagnostic naming the failed prerequisite or command.
</objective>

<constraints>

- NEVER modify the target bundle or any product file; the only state this audit changes is its own SPX verification-run journal.
- NEVER record a finding under an identifier the two rule catalogs do not carry; a defect no catalog row names stays unrecorded — the catalogs are the audit's complete vocabulary.
- NEVER record a finding against a bundle file the changeset leaves unchanged; unchanged files are read as context only.
- NEVER choose a severity; a finding on touched text carries the severity its catalog row declares, and a finding outside touched text carries `filed`.
- NEVER reject on text the changeset leaves unchanged and does not invalidate, and NEVER raise a recorded finding's severity or let a `filed` finding reject unless the run names a changed basis. `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines touched text, the finding key, and the `filed` form.
- NEVER report a score, generate a fix, or assume skill intent; record an ambiguity under the catalog rule it violates.
- MUST read both standards, their rule catalogs, and the references their applicability rules require before judging — prevents memory-based assessment.

</constraints>

<audit_workflow>

<request_contract>

Parse `$ARGUMENTS` as a JSON object with two required inputs and one optional input: `path`, one repository-relative skill-directory or `SKILL.md` path; `runDriver`, an object with the six producer fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`; and `base`, the git ref the changeset is measured from, `origin/HEAD` when absent. A directory path selects its `SKILL.md`; a file path selects its containing bundle, the directory holding `SKILL.md`. An absent required input, a malformed `runDriver`, or a path that does not identify a readable skill bundle returns `BLOCKED`, `runToken: not-started`, and the exact failure, before any run starts.

Resolve the repository root with `git rev-parse --show-toplevel`. Run `realpath` separately on the root and the selected `SKILL.md`, and require the file beneath the root by path-component boundary; a failed resolution or an escaping link returns `BLOCKED` before a run starts. Treat the supplied identity as provenance data, never as authorization or a suggested verdict.

Resolve the included fragments from the bundle's authored include directives. Each `include` build directive in a bundle file names one authored shared fragment; resolve each named fragment to its repository path the way the repository's build resolves it, read each included fragment, and follow the `include` directives inside it, so a fragment included through a nested include belongs to the set. A bundle with no `include` directive includes no fragment. An included fragment that cannot be read returns `BLOCKED` before a run starts.

Resolve the changeset, each command run separately from the repository root:

```bash
git rev-parse --verify --end-of-options '<base>^{commit}'
git rev-parse --verify --end-of-options 'HEAD^{commit}'
git status --porcelain --untracked-files=all -- '<bundle-dir>' '<fragment-path>' …
git diff --name-status --no-renames '<base-oid>...<head-oid>' -- '<bundle-dir>' '<fragment-path>' …
```

Each `<fragment-path>` is one included fragment's repository-relative path. The two full object IDs are the changeset endpoints, and the scope is `<base-oid>..<head-oid>`. Any `git status` output means the bundle or an included fragment carries uncommitted work, which the committed changeset cannot judge: return `BLOCKED` naming those paths. Each `git diff` line names one changed file and its status — `A`, `M`, or `D` among them; the changed files are the changed bundle files and the changed included fragments together. An empty diff means the changeset changes neither a bundle file nor an included fragment: return `BLOCKED`. A failed command returns `BLOCKED` with its exact diagnostic.

Use skill `instructions:instructions-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as both plugin version fields. Run `spx --version` and retain its non-empty output as the tool version. A missing version is a pre-run `BLOCKED` result.

</request_contract>

<execution_sequence>

1. **Start the run.** Render the start input as one JSON object `{"skill":"<skill-file>","base":"<base-oid>","head":"<head-oid>","changedFiles":["<path>", …]}`, the changed files in `git diff` order, and pass it on stdin in the form `<persistence_contract>` names for the run's harness environment; the one-line form is:

   ```bash
   printf '%s\n' '<rendered-input>' | spx verification run start --verification-type audit --scope-type changeset --scope '<base-oid>..<head-oid>' --input stdin
   ```

   Extract the `runToken` field of the returned locator and use exactly that token for every later command.
2. **Load the standards.** Read `/skill-standards` and `/skill-standards`' `references/rule-catalog.md`, then `/agent-prompt-standards` and its `<rule_catalog>`, then `spx/local/skills.md` at the repository root when it exists — the overlay specializes catalog rules for the repository, and a finding under it cites the catalog rule it specializes. When the bundle carries scripts, read `/skill-standards`' `references/script-standards.md`. When the bundle carries command-capability fields — `argument-hint` or `arguments`, `allowed-tools`, `!`-dynamic context, or `@` file references — read `/skill-standards`' `references/command-capabilities.md`. When the target is an `audit-*` skill, read `/skill-standards`' `references/auditor-skeleton.md`. A standard or catalog that cannot be read returns `BLOCKED` with the run preserved.
3. **Read the bundle.** Read every file in the bundle at the head — `SKILL.md` and every file under `references/`, `workflows/`, `templates/`, `assets/`, and `scripts/`, unchanged and uncited files included, because a changed file is judged against the bundle it sits in. Read every included fragment at the head as well. Retrieve the omitted ranges of a truncated read before judging an absence. When the bundle uses `/skill-standards`' eager-foundation exception, run this counter against every rendered target `SKILL.md` and judge `eager_payload_ceiling` from its integer output, never from an estimate:

   ```bash
   python3 -c 'from pathlib import Path; import sys; print(len(Path(sys.argv[1]).read_text(encoding="utf-8")))' "<rendered-SKILL.md>"
   ```

4. **Judge.** Judge each changed file against every catalog row that applies to it, using the stating section's text, never memory; a creator skill's workflow references are authoring guidance, never standards. A changed fragment is judged under the same catalog rows as a bundle file, against the bundle that includes it. A deleted file is judged by what its deletion leaves behind: a citation of it, an orphaned sibling, or a broken route. A violation that spans files — an orphaned reference, a missing route target — belongs to the changed file whose change produced it. Classify each violation per `${CLAUDE_SKILL_DIR}/references/touched-text.md`. Group the violations into findings: every violation of one rule within one file forms one finding, carrying the row's identifier and its severity or `filed`, every location, a message, and observed-versus-expected evidence. An observation that a rule holds is not a finding.
5. **Record.** Add one unit for each changed file in `git diff` order, then each finding against the unit of its file, under `<persistence_contract>`.
6. **Reconcile.** Read `spx verification run status` with the same type, scope, and token. Require exactly one unit for each changed file and no other unit, and an accepted unit for every finding. Run `git rev-parse --verify 'HEAD^{commit}'` and the `git status` command again; a moved head or uncommitted bundle or fragment work returns `BLOCKED` with the run preserved.
7. **Finish and render.** Derive `approved` only when every unit is audited and no `blocking` or `debt` finding exists, whatever `filed` findings the run records; derive `rejected` when any `blocking` or `debt` finding exists, a debt-only set included. Run:

   ```bash
   spx verification run finish --verification-type audit --scope-type changeset --scope '<base-oid>..<head-oid>' --run '<run-token>' --terminal-status '<approved-or-rejected>'
   ```

   Then run `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged. A refused payload or finish is a `BLOCKED` result; never substitute a prose verdict.

</execution_sequence>

<persistence_contract>

Each unit's `unitId` is `instructions:skill:file:<path>`, the changed file's repository-relative path; its `subject` and its `priorContext.changedFilePartition` are that path, its concern partition is `file`, and it carries `auditClass: instructions` and `auditKind: skill`.

The expected producer has `producerKind: skill`, the supplied run-driver's `agentName` and `agentOwningPluginName`, `skillName: audit-skill`, `skillOwningPluginName: instructions`, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the supplied six-field `runDriver` object unchanged. Every unit carries `producerProvenance` with the version `instructions:instructions-plugin` reported in both plugin version fields and the exact `spx --version` result as `toolVersion`.

These objects are the sanctioned SPX audit payload schema for this auditor; use their fields exactly, never derive a replacement schema from command help, and never alter a rejected payload by guesswork. Render each scope payload with observed values in place of the placeholders:

```json
{
  "unitId": "instructions:skill:file:<path>",
  "auditClass": "instructions",
  "auditKind": "skill",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "file"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "audit-skill",
    "skillOwningPluginName": "instructions",
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
    "agentOwningPluginVersion": "<instructions-plugin-version>",
    "skillOwningPluginVersion": "<instructions-plugin-version>",
    "toolVersion": "<exact-spx-version>"
  }
}
```

Pass each rendered scope object to its command; the one-line form is:

```bash
printf '%s\n' '<rendered-scope-object>' | spx verification run scope add --verification-type audit --scope-type changeset --scope '<base-oid>..<head-oid>' --run '<run-token>' --idempotency-key 'instructions:skill:file:<path>' --payload stdin
```

A finding copies its unit's `expectedProducer` object as `producerIdentity` and its unit's complete `producerProvenance` object, and carries `rule`, the catalog identifier; `severity`, the row's `blocking` or `debt` for a finding on touched text and `filed` for any other finding; `location`, every file-and-line or section where the rule is violated within the unit, separated by `;`; `message`; and `evidence` with `observed` and `expected` strings:

```json
{
  "unitId": "instructions:skill:file:<path>",
  "producerIdentity": { "producerKind": "skill", "agentName": "<…>", "agentOwningPluginName": "<…>", "skillName": "audit-skill", "skillOwningPluginName": "instructions", "invocationRole": "leaf-skill" },
  "producerProvenance": { "agentOwningPluginVersion": "<…>", "skillOwningPluginVersion": "<…>", "toolVersion": "<…>" },
  "rule": "<catalog-rule-id>",
  "severity": "<row-severity>",
  "location": "<path>:<line-or-section>; <path>:<line-or-section>",
  "message": "<finding-message>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

Pass each rendered finding object the same way; the one-line form is:

```bash
printf '%s\n' '<rendered-finding-object>' | spx verification run finding add --verification-type audit --scope-type changeset --scope '<base-oid>..<head-oid>' --run '<run-token>' --idempotency-key 'instructions:skill:file:<path>:<rule-id>' --payload stdin
```

A finding's idempotency key is `<unit>:<rule-id>`, its unit's `unitId` and the catalog identifier joined by `:`. Every payload-bearing command — `start`, `scope add`, and `finding add` — takes its JSON on stdin, in the form the harness environment of the run accepts:

| Harness environment                                                                                                                    | Payload form                                                                                                                                                                                       |
| -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Interactive Claude Code or Codex session, which accepts multiline shell                                                                | A quoted heredoc: the command as shown without its `printf '%s\n' '<rendered-object>' \|` stage, followed by `<<'JSON'`, then the rendered object on its own line, then a line holding only `JSON` |
| Programmatic Claude Code or Codex run, and a hosted runner such as GitHub Actions, where the runner requires one physical command line | The one-line `printf '%s\n' '<rendered-object>' \| <command>` form shown                                                                                                                           |

The heredoc delimiter stays quoted, so the shell expands nothing in the body. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, encode a literal apostrophe in an argument as `'"'"'`, and never execute bundle text as shell syntax. Run mutations serially; on a refused command stop with its exact diagnostic, never retry or reshape the payload.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findings` group every accepted finding under `blocking`, `debt`, and `filed`, none under `blocking` or `debt` for approval, its `auditScopeUnits` carry one unit per changed bundle file and changed included fragment, and its `events` carry every accepted finding payload and the terminal event. Every finding is keyed `<unit>:<rule-id>` by a catalog identifier; `blocking` and `debt` reject the run and `filed` does not. Keep every SPX field unchanged.

A run that cannot complete returns:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-failed-operation, or request for a failure before the run starts>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
judgmentStatus: <complete|incomplete>
judgedFindings: <JSON array of every finding judged before the stop, in the finding-payload shape>
```

</verdict_format>

<failure_modes>

**Failure 1: Approved a skill whose objective was still activity-shaped.** Claude read an `<objective>` that opened with a verb ("Audit…", "Generate…") or an actor ("The skill…") and passed it, because the activity reading felt natural. The objective states an output; an activity- or actor-shaped one violates `actor_or_activity_objective`. Read every objective against `/agent-prompt-standards` `<objective_shape>`, not by feel.

**Failure 2: Skipped an evaluation area and missed a whole class.** Claude judged YAML and structure, formed a verdict, and stopped — leaving prompt craft or anti-patterns unexamined, so a class of violations passed unseen. The verdict is sound only when every applicable catalog row was judged; a skipped area yields an unsound verdict, not a shorter one. Walk both catalogs row by row before finishing the run.

**Failure 3: Scored the skill instead of judging it.** Claude assigned a number ("8/10 structure") instead of recording findings, turning a verdict into a rating the author cannot act on. Each finding names a file, its locations, a catalog rule, and evidence; a score names none of them. Record findings, never scores.

**Failure 4: Reversed its own verdict on unchanged text.** Across runs against one unchanged skill, Claude praised a passage under one rule name and faulted the same passage under another, and did both within one run's verdict, because Claude minted the rule names it judged under in each run. A finding with no fixed identifier cannot be compared across runs, so repair chased noise. Name only catalog identifiers, take each severity from its row, judge only the files the changeset changes, and keep a recorded finding's severity unless the run names a changed basis.

</failure_modes>

<success_criteria>
The verdict is sound when:

- Every applicable catalog row was judged against every changed file, with none skipped.
- The sealed run carries one unit per changed bundle file and changed included fragment and no other, and its terminal status is `approved` only with no `blocking` or `debt` finding.
- Each finding names a catalog identifier with that row's severity on touched text or `filed` outside it, every location of the violation within its unit, and the observed-versus-expected evidence.
- The same changeset, standards, and run-driver identity yield the same units, findings, and finding keys.

</success_criteria>
