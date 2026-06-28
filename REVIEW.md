# Review policy

Repository reviews classify findings by **severity** and **concern**. Findings only report defects. Omit praise, commentary, notes, and open questions that are not defect claims.

## Severity

| Severity     | Use when                                                                                                                                                         |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **BLOCKING** | The defect can make the changeset unsafe to merge, invalidate its evidence, break a required workflow, or leave the review unable to trust the shipped behavior. |
| **DEBT**     | The defect is real and should be addressed, but it does not make the changeset unsafe to merge by itself.                                                        |

Do not use severity ranks such as `P0`, `P1`, `critical`, `high`, `medium`, `low`, `minor`, or `nit`. Do not use a third scope-shaped severity such as `FOLLOW-UP`. Reframe open questions as findings when they identify a defect; otherwise omit them.

## Concern

Each finding uses exactly one concern:

| Concern          | Use when                                                                                                                              |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **consistency**  | The change contradicts a spec, decision, workflow, generated artifact, or adjacent implementation contract.                           |
| **security**     | The change exposes data, weakens authorization, broadens unsafe tool access, or enables an unsafe external action.                    |
| **performance**  | The change adds avoidable runtime, resource, or process cost that affects users, CI, or agent execution.                              |
| **evidence**     | The change lacks required tests, evals, audits, validation, or proof that the declared behavior holds.                                |
| **standards**    | The change violates repository, skill, prompt, language, formatting, portability, or process standards.                               |
| **architecture** | The change puts behavior in the wrong layer, duplicates ownership, weakens boundaries, or creates an API shape that will not compose. |

## Finding shape

Use this shape for every finding:

```text
### <SEVERITY> [<concern>]: <path>
Reference: <file:line or governing rule>
Evidence: <what the changed code or document does, and why that is a defect>
Required: <the bounded fix required in this changeset>
```

- ALWAYS: every `Reference` cites rule text or a source contract the reviewer located in the repository or in a loaded governing skill. Do not cite memory, prior sessions, user/global instructions outside the repository, or training data.

## Disposition

The reviewer judges finding validity, severity, and concern. The author judges disposition. A bounded valid finding is fixed in the changeset. A `DEBT` finding is tracked outside the changeset only when the fix is a separate larger concern, and the tracking note states why that fix is larger than the current changeset.
