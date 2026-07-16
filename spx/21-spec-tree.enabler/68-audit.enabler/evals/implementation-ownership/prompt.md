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

For every implementation-owned language partition, ALWAYS plan all three required
concern units: code, tests, and architecture. This trio is required even when the
changed paths contain only one implementation artifact kind. A successful concern
producer marks its unit `audited`; the tests concern inspects the linked or
partition-level test surface even when no test file changed, so absence of a test
diff never makes that required unit optional or incomplete.

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

Coverage statuses have these complete semantics:

| Status           | Meaning                                                                                                                                               |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `audited`        | The executable concern producer completed and every accepted finding was recorded.                                                                    |
| `not-applicable` | The unit is optional transparency for non-implementation artifacts and requires no concern producer.                                                  |
| `unsupported`    | The unit is required, but its implementation language or artifact kind has no executable concern producer.                                            |
| `missing-skill`  | The unit is required and names an expected concern skill that is unavailable.                                                                         |
| `skipped`        | The unit is required and its producer is available, but dispatch stopped after another required unit was classified `unsupported` or `missing-skill`. |
| `incomplete`     | The unit is required and dispatch began, but no accepted concern result was recorded.                                                                 |

Plan the complete inventory before dispatch, but NEVER mark a planned unit `audited`. Invoke each concern skill inside the open run. After that concern returns, immediately record one path-scoped row per inspected path with a stable path-scoped unit id, the exact path in `subject`, and `coverageStatus: audited` before inspecting the next concern. Record each returned finding immediately after those scope rows and associate it with the matching path-scoped unit. Derive the concern's finding count from the accepted finding rows; do not emit a custom count SPX discards. When a concern cannot return a complete result, record `incomplete` or the applicable non-audited status; never manufacture a completed result from the orchestration's own inspection.

A missing required concern skill, unsupported implementation-owned artifact, or required unit that receives no concern result rejects the run through accepted coverage status and the evidence-derived terminal rollup. Do not continue concern dispatch after detecting an absent required skill for a language partition; finish and render the rejected run after the complete expected inventory is recorded. An SPX command or payload rejection is a command failure and returns BLOCKED under `<verdict_format>` rather than becoming coverage evidence.

When the caller supplied an explicit live file list, build the expected coverage inventory from that list rather than from the committed changeset alone. A live file that receives no concern result is a coverage gap even when it is absent from `<head>`.

</step>
The changeset and installed producer state (JSON-encoded):

```json
{input_json}
```
