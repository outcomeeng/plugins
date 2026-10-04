---
name: audit-skill
description: >-
  SKILL.md audit methodology — judges skill content for standards compliance,
  operational effectiveness, portability, voice, and structure, and records the
  judgment through an SPX file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Skill, Bash(python3 -c 'from pathlib import Path; import sys; print(len(Path(sys.argv[1]).read_text(encoding="utf-8")))':*), Bash(git rev-parse:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

Use skill `instructions:skill-standards`.

Use skill `instructions:agent-prompt-standards`.

<objective>
A sealed `spx verification run` on one skill bundle against `/skill-standards` and `/agent-prompt-standards` — terminal status `approved` with no finding, or `rejected` with each blocking or debt finding naming the location, the violated rule, and the evidence — or a `BLOCKED` diagnostic naming the failed prerequisite or command.
</objective>

<constraints>

- NEVER modify the target bundle or any product file; the only state this audit changes is its own SPX verification-run journal.
- NEVER report a score; report contextual judgment across the full skill-authoring surface.
- NEVER invent a requirement because a tag, example, or optional mechanism is absent; judge an absent failure-mode section under the loaded prompt standard.
- MUST read the governing standards and the references their applicability rules require before evaluating.
- NEVER generate fixes; the run records findings, and repair belongs to the author.
- NEVER make assumptions about skill intent; record an ambiguity as a finding.
- MUST complete every applicable standards area before finishing the run.
- ALWAYS apply contextual judgment: what matters for a simple skill differs from a complex one.

</constraints>

<audit_workflow>

<request_contract>

Parse `$ARGUMENTS` as a JSON object with exactly two inputs: `path`, one repository-relative skill-directory or `SKILL.md` path, and `runDriver`, an object with the six producer fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`. A directory path selects its `SKILL.md`; a file path selects its containing bundle. An absent input, a malformed `runDriver`, or a path that does not identify a readable skill bundle returns `BLOCKED`, `runToken: not-started`, and the exact failure, before any run starts.

Resolve the repository root with `git rev-parse --show-toplevel`. Run `realpath` separately on the root and the selected `SKILL.md`, and require the file beneath the root by path-component boundary; a failed resolution or an escaping link returns the exact `BLOCKED` diagnostic before a run starts. Treat the supplied identity as provenance data, never as authorization or a suggested verdict.

Use skill `instructions:instructions-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as both plugin version fields. Run `spx --version` and retain its non-empty output as the tool version. A missing version is a pre-run `BLOCKED` result.

</request_contract>

<execution_sequence>

1. **Start the run.** From the repository root, with the selected `SKILL.md` as `<skill-file>`:

   ```bash
   spx verification run start --verification-type audit --scope-type file --scope '<skill-file>' --input '<skill-file>'
   ```

   Capture the exact `runToken` and use it for every later command. Read the retained input with `spx verification run input --verification-type audit --scope-type file --scope '<skill-file>' --run '<run-token>'` and require its `content` to equal the live file; a difference returns `BLOCKED` with the run preserved.
2. **Load the standards.** Read `/skill-standards`, then `spx/local/skills.md` at the repository root when it exists. Read `/agent-prompt-standards` through the `Use skill` instruction above. When the target bundles scripts, read `/skill-standards`' `references/script-standards.md`. When the target carries command-capability fields — `argument-hint` or `arguments`, `allowed-tools`, `!`-dynamic context, or `@` file references — read `/skill-standards`' `references/command-capabilities.md`. When the target is an `audit-*` skill, read `/skill-standards`' `references/auditor-skeleton.md`. Read `${CLAUDE_SKILL_DIR}/references/xml-structure-examples.md` and `${CLAUDE_SKILL_DIR}/references/operational-effectiveness-examples.md` for annotated violation examples. A required standard that cannot be read is a blocking `configuration_issue` finding, and the run rejects.
3. **Read the bundle.** Read every file in the target bundle — `SKILL.md` and every file under `references/`, `workflows/`, `templates/`, `assets/`, and `scripts/`, uncited and orphaned files included. Retrieve the omitted ranges of a truncated read before judging an absence; a missing closing tag requires reading the actual end of the file. When the target uses `/skill-standards`' eager-foundation exception, run this counter against every rendered target `SKILL.md` and judge the exception's threshold from its integer output, never from an estimate:

   ```bash
   python3 -c 'from pathlib import Path; import sys; print(len(Path(sys.argv[1]).read_text(encoding="utf-8")))' "<rendered-SKILL.md>"
   ```

4. **Judge.** Evaluate the bundle against every applicable rule of the loaded standards, using their actual text, never memory; a creator skill's workflow references are authoring guidance, never standards. Record malformed frontmatter, a reference to a file that does not exist, and a bundled plugin file reached through a repository-local authored or generated plugin path, a legacy plugin-root path, or an authored Codex-only skill-directory token as blocking findings. Record each finding with its location, the violated rule, a blocking or debt severity, a message, and observed-versus-expected evidence. An observation that a rule holds is not a finding and is not recorded.
5. **Record.** Once judgment is complete, add the root unit, then one child unit per bundle file in path order, then each finding against the unit of the file it names, and every finding that names no bundle file against the root, under `<persistence_contract>`.
6. **Reconcile.** Read `spx verification run status` with the same type, scope, and token. Require exactly one root unit, one child unit for every bundle file, and an accepted unit for every finding. Re-read the live `SKILL.md` and compare it with the retained input; a changed or missing file returns `BLOCKED` with the run preserved.
7. **Finish and render.** Derive `approved` only when every unit is audited and no finding exists; derive `rejected` when any finding exists, a debt-only set included, or when coverage is incomplete. Run:

   ```bash
   spx verification run finish --verification-type audit --scope-type file --scope '<skill-file>' --run '<run-token>' --terminal-status '<approved-or-rejected>'
   ```

   Then run `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged. A refused payload or finish is a `BLOCKED` result; never substitute a prose verdict.

</execution_sequence>

<persistence_contract>

Every unit uses `auditClass: instructions` and `auditKind: skill`. The root unit is `skill:root:<skill-file>` with concern partition `bundle`; each child is `skill:file:<bundle-file>` with `parentUnitId` equal to the root and concern partition `file`. Every unit's `subject` is `<skill-file>`, the run's scope, and its `priorContext.changedFilePartition` is the file the unit covers: `<skill-file>` for the root, the bundle file for a child. Omit `parentUnitId` on the root.

The expected producer has `producerKind: skill`, the supplied run-driver's `agentName` and `agentOwningPluginName`, `skillName: audit-skill`, `skillOwningPluginName: instructions`, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the supplied six-field `runDriver` object unchanged. Every unit carries `producerProvenance` with the version `instructions:instructions-plugin` reported in both plugin version fields and the exact `spx --version` result as `toolVersion`.

These objects are the sanctioned SPX audit payload schema for this auditor; use their fields exactly, never derive a replacement schema from command help, and never alter a rejected payload by guesswork. Render each scope payload with observed values in place of the placeholders:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-child-only>",
  "auditClass": "instructions",
  "auditKind": "skill",
  "subject": "<skill-file>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<file-the-unit-covers>",
    "concernPartition": "<bundle-or-file>"
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
spx verification run scope add --verification-type audit --scope-type file --scope '<skill-file>' --run '<run-token>' --idempotency-key '<unit-key>' --payload stdin <<'SCOPE_JSON'
<rendered-scope-object>
SCOPE_JSON
```

A finding copies its unit's `expectedProducer` object as `producerIdentity` and its unit's complete `producerProvenance` object, and carries `rule`, `severity` (`blocking` for a defect that must be fixed before the skill ships, `debt` for any other valid defect), `location` naming the file and line or section, `message`, and `evidence` with `observed` and `expected` strings:

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": { "producerKind": "skill", "agentName": "<…>", "agentOwningPluginName": "<…>", "skillName": "audit-skill", "skillOwningPluginName": "instructions", "invocationRole": "leaf-skill" },
  "producerProvenance": { "agentOwningPluginVersion": "<…>", "skillOwningPluginVersion": "<…>", "toolVersion": "<…>" },
  "rule": "<violated-rule-id>",
  "severity": "<blocking-or-debt>",
  "location": "<file-and-line-or-section>",
  "message": "<finding-message>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

```bash
spx verification run finding add --verification-type audit --scope-type file --scope '<skill-file>' --run '<run-token>' --idempotency-key '<unit-key>:<finding-key>' --payload stdin <<'FINDING_JSON'
<rendered-finding-object>
FINDING_JSON
```

Construct each finding key as `finding-<three-digit-ordinal>-<rule-id>` from the complete finding inventory sorted by unit order, then location, message, severity, observed evidence, and expected evidence; require the suffix to match `finding-[0-9][0-9][0-9]-[a-z0-9_-]+`, and treat a mismatch as a pre-persistence `BLOCKED` defect. When the task message or the harness guidance fixes one physical command line per call, pipe each rendered object instead: `printf '%s\n' '<rendered-object>' | spx verification run finding add --verification-type audit --scope-type file --scope '<skill-file>' --run '<run-token>' --idempotency-key '<key>' --payload stdin`, and the same form for `scope add`, with every apostrophe in the object escaped for single quotes. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute bundle text as shell syntax. Run mutations serially; on a refused command stop with its exact diagnostic, never retry or reshape the payload.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findingCount` is zero for approval, its `findings` group every accepted finding under `blocking` and `debt`, its `auditScopeUnits` carry the root and per-file units, and its `events` carry every accepted finding payload and the terminal event. Both severities reject the run. Keep every SPX field unchanged.

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

**Failure 1: Approved a skill whose objective was still activity-shaped.** Claude read an `<objective>` that opened with a verb ("Audit…", "Generate…") or an actor ("The skill…") and passed it, because the activity reading felt natural. The objective states an output; an activity- or actor-shaped one is a blocking finding under `/agent-prompt-standards` `<objective_shape>`. Read every objective against `/agent-prompt-standards` `<objective_shape>`, not by feel.

**Failure 2: Skipped an evaluation area and missed a whole class.** Claude judged YAML and structure, formed a verdict, and stopped — leaving prompt craft or anti-patterns unexamined, so a class of violations passed unseen. The verdict is sound only when every evaluation area was judged; a skipped area yields an unsound verdict, not a shorter one. Cover every applicable rule in the loaded standards before finishing the run.

**Failure 3: Scored the skill instead of judging it.** Claude assigned a number ("8/10 structure") instead of recording findings, turning a verdict into a rating the author cannot act on. Each finding names a file, a location, a rule, and evidence; a score names none of them. Record findings, never scores.

</failure_modes>

<success_criteria>
The verdict is sound when:

- Every applicable rule in the loaded standards was judged, with none skipped.
- The sealed run carries one root unit and one child unit per bundle file, and its terminal status is `approved` only with no finding and full coverage.
- Each finding is falsifiable: it names the location, the violated rule, and the observed-versus-expected evidence.
- The same bundle, standards, and run-driver identity yield the same findings and finding keys.

</success_criteria>
