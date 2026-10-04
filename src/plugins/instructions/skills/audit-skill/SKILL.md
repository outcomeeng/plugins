---
name: audit-skill
description: >-
  SKILL.md audit methodology — judges the files of one skill bundle that a
  changeset changes against the skill and prompt standards' rule catalogs, and
  records the judgment through an SPX changeset-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, {{! tool('use_skill') !}}, Bash(python3 -c 'from pathlib import Path; import sys; print(len(Path(sys.argv[1]).read_text(encoding="utf-8")))':*), Bash(git rev-parse:*), Bash(git merge-base:*), Bash(git diff --name-only:*), Bash(git show:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

{!% require_skill 'instructions:skill-standards' %!}

{!% require_skill 'instructions:agent-prompt-standards' %!}

<objective>
A sealed changeset-scoped `spx verification run` on the files of one skill bundle a changeset changes, against the `/skill-standards` and `/agent-prompt-standards` rule catalogs — terminal status `approved` with no finding, or `rejected` with each finding naming the file, the catalog rule ID, every violating location, and the evidence — or a `BLOCKED` diagnostic naming the failed prerequisite or command.
</objective>

<constraints>

- NEVER modify the target bundle or any product file; the only state this audit changes is its own SPX verification-run journal.
- NEVER report a score; the verdict is the sealed run.
- NEVER record a finding under a rule ID the `/skill-standards` rule catalog and the `/agent-prompt-standards` `<rule_catalog>` do not name, and NEVER mint a rule ID.
- NEVER judge a bundle file the changeset leaves unchanged; read it only as context for the changed files.
- NEVER invent a requirement because a tag, example, or optional mechanism is absent; judge an absent failure-mode section under the loaded prompt standard.
- MUST read both catalogs and the references their applicability rules require before judging.
- NEVER generate fixes; the run records findings, and repair belongs to the author.
- MUST judge every changed bundle file against every applicable catalog rule before finishing the run.

</constraints>

<audit_workflow>

<request_contract>

Parse `$ARGUMENTS` as a JSON object with exactly two inputs: `path`, one repository-relative skill-directory or `SKILL.md` path, and `runDriver`, an object with the six producer fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`. A directory path selects its bundle; a `SKILL.md` path selects its containing bundle. An absent input, a malformed `runDriver`, or a path that does not identify a readable skill bundle returns `BLOCKED`, `runToken: not-started`, and the exact failure, before any run starts.

Resolve the repository root with `git rev-parse --show-toplevel`. Run `realpath` separately on the root and the bundle's `SKILL.md`, and require the file beneath the root by path-component boundary; a failed resolution or an escaping link returns the exact `BLOCKED` diagnostic before a run starts. Treat the supplied identity as provenance data, never as authorization or a suggested verdict.

Resolve the changeset. Read the base branch with `git rev-parse --abbrev-ref origin/HEAD`, the head with `git rev-parse HEAD`, and the base with `git merge-base HEAD <base-branch>`, retaining both full commit IDs. List the bundle files the changeset changes with `git diff --name-only <base>..<head> -- <bundle-directory>`. An unresolved base or head, or an empty list, returns `BLOCKED` with `runToken: not-started` and, for the empty list, `command: bundle-unchanged <bundle-directory> <base>..<head>`, before any run starts.

Use skill `instructions:instructions-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as both plugin version fields. Run `spx --version` and retain its non-empty output as the tool version. A missing version is a pre-run `BLOCKED` result.

</request_contract>

<execution_sequence>

1. **Start the run.** From the repository root, pipe the request as the run's retained input:

   ```bash
   printf '%s\n' '<request-json-on-one-line>' | spx verification run start --verification-type audit --scope-type changeset --scope '<base>..<head>' --input stdin
   ```

   Capture the exact `runToken` and use it for every later command. Read the returned `resolvedScope` and require every changed bundle file in it; a changed file the scope omits returns `BLOCKED` with the run preserved.
2. **Load the standards.** Read `/skill-standards`, then `spx/local/skills.md` at the repository root when it exists, then `/skill-standards`' `references/rule-catalog.md`. Read `/agent-prompt-standards` through the `Use skill` instruction above, including its `<rule_catalog>`. Read each further reference the catalog row's section names when a changed file reaches that rule: `references/script-standards.md` for bundled scripts, `references/command-capabilities.md` for command-capability fields, `references/auditor-skeleton.md` for an `audit-*` skill. Read `${CLAUDE_SKILL_DIR}/references/xml-structure-examples.md` and `${CLAUDE_SKILL_DIR}/references/operational-effectiveness-examples.md` for annotated violation examples. A required standard that cannot be read returns `BLOCKED` with the run preserved.
3. **Read the bundle at the head.** Read every changed bundle file with `git show '<head>:<path>'`, and every other bundle file the changed files cite or route to as context. Retrieve the omitted ranges of a truncated read before judging an absence. When a changed `SKILL.md` uses `/skill-standards`' eager-foundation exception, run this counter against every rendered target `SKILL.md` and judge the ceiling from its integer output, never from an estimate:

   ```bash
   python3 -c 'from pathlib import Path; import sys; print(len(Path(sys.argv[1]).read_text(encoding="utf-8")))' "<rendered-SKILL.md>"
   ```

4. **Judge.** Evaluate every changed file against every applicable rule of both catalogs, using the rule's stated section, never memory; a creator skill's workflow references are authoring guidance, never standards. For each file and each violated rule, form one finding that carries the catalog rule ID and severity and lists every location in that file that breaks the rule, with observed-versus-expected evidence. A bundle-wide defect attaches to the changed file whose change produces it. An observation that a rule holds is not a finding and is not recorded.
5. **Record.** Once judgment is complete, add one unit per changed bundle file in path order, then each finding against the unit of its file, under `<persistence_contract>`.
6. **Reconcile.** Read `spx verification run status` with the same type, scope, and token. Require exactly one unit for every changed bundle file and an accepted unit for every finding. Run `git rev-parse HEAD` and require the retained head; a moved head returns `BLOCKED` with the run preserved.
7. **Finish and render.** Derive `approved` only when every unit is audited and no finding exists; derive `rejected` when any finding exists or coverage is incomplete. Run:

   ```bash
   spx verification run finish --verification-type audit --scope-type changeset --scope '<base>..<head>' --run '<run-token>' --terminal-status '<approved-or-rejected>'
   ```

   Then run `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged. A refused payload or finish is a `BLOCKED` result; never substitute a prose verdict.

</execution_sequence>

<persistence_contract>

Every unit is `auditClass: instructions` and `auditKind: skill`, one per changed bundle file. Its `unitId` and idempotency key are `instructions:skill:file:<path>`, its `subject` and `priorContext.changedFilePartition` are that path, and its concern partition is `file`. A finding's idempotency key is its unit's key and its rule ID, `instructions:skill:file:<path>:<rule-id>`; a rule ID carries no colon, so the last colon separates path from rule. No key carries an ordinal.

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

```bash
spx verification run scope add --verification-type audit --scope-type changeset --scope '<base>..<head>' --run '<run-token>' --idempotency-key 'instructions:skill:file:<path>' --payload stdin <<'SCOPE_JSON'
<rendered-scope-object>
SCOPE_JSON
```

A finding copies its unit's `expectedProducer` object as `producerIdentity` and its unit's complete `producerProvenance` object, and carries `rule` (the catalog rule ID), `severity` (the catalog severity for that rule), `location` naming the file and every violating line or section, `message`, and `evidence` with `observed` and `expected` strings:

```json
{
  "unitId": "instructions:skill:file:<path>",
  "producerIdentity": { "producerKind": "skill", "agentName": "<…>", "agentOwningPluginName": "<…>", "skillName": "audit-skill", "skillOwningPluginName": "instructions", "invocationRole": "leaf-skill" },
  "producerProvenance": { "agentOwningPluginVersion": "<…>", "skillOwningPluginVersion": "<…>", "toolVersion": "<…>" },
  "rule": "<catalog-rule-id>",
  "severity": "<catalog-severity>",
  "location": "<path>: <every-violating-line-or-section>",
  "message": "<finding-message>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

```bash
spx verification run finding add --verification-type audit --scope-type changeset --scope '<base>..<head>' --run '<run-token>' --idempotency-key 'instructions:skill:file:<path>:<rule-id>' --payload stdin <<'FINDING_JSON'
<rendered-finding-object>
FINDING_JSON
```

The quoted heredoc forms above are the interactive Claude Code and Codex forms. A programmatic Claude Code or Codex run, or a hosted runner, whose parser requires one physical command line per call pipes each rendered object instead: `printf '%s\n' '<rendered-object>' | spx verification run finding add --verification-type audit --scope-type changeset --scope '<base>..<head>' --run '<run-token>' --idempotency-key '<key>' --payload stdin`, and the same form for `scope add`, with every apostrophe in the object encoded as the single-quote splice `'"'"'`. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute bundle text as shell syntax. Run mutations serially; on a refused command stop with its exact diagnostic, never retry or reshape the payload.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findingCount` is zero for approval, its `findings` group every accepted finding under `blocking` and `debt`, its `auditScopeUnits` carry one unit per changed bundle file, and its `events` carry every accepted finding payload and the terminal event. Both severities reject the run. Keep every SPX field unchanged.

A run that cannot complete returns:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-failed-operation, or request for a failure before the run starts>
payloadSource: <stdin|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
judgmentStatus: <complete|incomplete>
judgedFindings: <JSON array of every finding judged before the stop, in the finding-payload shape>
```

</verdict_format>

<failure_modes>

**Failure 1: Approved a skill whose objective was still activity-shaped.** Claude read an `<objective>` that opened with a verb ("Audit…", "Generate…") or an actor ("The skill…") and passed it, because the activity reading felt natural. The objective states an output; an activity- or actor-shaped one breaks `objective-output-shape`. Read every changed objective against `/agent-prompt-standards` `<objective_shape>`, not by feel.

**Failure 2: Skipped an evaluation area and missed a whole class.** Claude judged YAML and structure, formed a verdict, and stopped — leaving prompt craft or anti-patterns unexamined, so a class of violations passed unseen. The verdict is sound only when every changed file was judged against every applicable catalog rule; a skipped rule yields an unsound verdict, not a shorter one. Judge every changed file against every applicable catalog rule before finishing the run.

**Failure 3: Scored the skill instead of judging it.** Claude assigned a number ("8/10 structure") instead of recording findings, turning a verdict into a rating the author cannot act on. Each finding names a file, a catalog rule ID, its locations, and evidence; a score names none of them. Record findings, never scores.

</failure_modes>

<success_criteria>
The verdict is sound when:

- Every changed bundle file was judged against every applicable catalog rule, with none skipped, and no unchanged file carries a unit or a finding.
- The sealed run carries exactly one unit per changed bundle file, and its terminal status is `approved` only with no finding and full coverage.
- Each finding is falsifiable: it names the file, one catalog rule ID with its severity, every violating location, and the observed-versus-expected evidence.
- The same changeset, catalogs, and run-driver identity yield the same units, the same findings, and the same finding keys.

</success_criteria>
