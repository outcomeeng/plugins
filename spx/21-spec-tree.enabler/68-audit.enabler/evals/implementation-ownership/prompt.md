<!-- Generated from producer section classify_implementation_ownership at src/plugins/spec-tree/skills/audit-implementation/SKILL.md. -->

Apply the implementation-ownership producer section below to the supplied changeset. Classify artifact ownership, build the expected coverage inventory, and derive terminal status. Assume each listed installed concern producer executes successfully with zero findings. Return exactly one JSON object with these mandatory fields:

- `terminal_status`: `approved` or `rejected`
- `required_units`: an array whose entries carry `language`, `concern`, `coverage_requirement`, and `coverage_status`
- `optional_units`: an array whose entries carry `coverage_requirement` and `coverage_status`
- `unsupported_paths`: an array of implementation-owned paths without an executable producer

<step name="classify_implementation_ownership">

Classify every changed path by implementation-audit ownership before building
the expected coverage inventory:

- Implementation-owned artifacts are implementation code, linked tests, and
  implementation or test infrastructure. Partition these artifacts by language
  and require the applicable code, tests, and architecture concern units.
- Non-implementation artifacts include specs, decisions, coordination notes,
  skill or agent prompts, eval artifacts, generated copies, workflow
  configuration, documentation, and inert fixtures. Omit these paths from
  required implementation coverage or record one optional `not-applicable`
  unit that lists them for scope transparency. Such a unit has no expected
  language concern producer, never carries `unsupported` or `missing-skill`,
  and never rejects the run.
- Reserve `unsupported` for an implementation-owned artifact whose language or
  artifact kind requires implementation audit but has no executable concern
  producer. That unit remains required and rejects the run.

Derive ownership from the loaded project context, governing nodes, linked test
evidence, and artifact role. Do not classify every changed path as implementation
merely because it appears in the changeset, and do not hard-code repository-local
paths or language-specific extensions into this language-neutral orchestrator.

Build an expected coverage inventory before invoking any language concern skill. Each expected unit records:

- audit class: `implementation`
- audit kind: `code`, `tests`, or `architecture`
- language partition
- concern partition: `code`, `tests`, or `architecture`
- subject paths or explicit unsupported-file marker
- stable expected-producer identity: plugin name, skill name, audit class, language, and concern
- producer provenance: owning plugin version when the concern skill exists; null with reason `missing-skill` or `unsupported` when no executable concern skill can run
- execution producer identity: the wrapper and SPX command driver that recorded the unit, present for every unit so missing-skill and unsupported classifications still have provenance for the recorder
- coverage requirement: `required` or `optional`
- coverage status: `audited`, `not-applicable`, `unsupported`, `missing-skill`, `skipped`, or `incomplete`

Record the inventory with `spx verification run scope add` as soon as each unit is planned or classified. A missing required concern skill, unsupported implementation-owned artifact, or required unit that receives no concern result rejects the run through accepted coverage status and the evidence-derived terminal rollup. Do not continue concern dispatch after detecting an absent required skill for a language partition; finish and render the rejected run after the complete expected inventory is recorded. An SPX command or payload rejection is a command failure and returns BLOCKED under `<verdict_format>` rather than becoming coverage evidence.

When the caller supplied an explicit live file list, build the expected coverage inventory from that list rather than from the committed changeset alone. A live file that receives no concern result is a coverage gap even when it is absent from `<head>`.

</step>
The changeset and installed producer state (JSON-encoded):

```json
{input_json}
```
