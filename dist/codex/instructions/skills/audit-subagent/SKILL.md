---
name: audit-subagent
description: >-
  Custom agent-configuration audit methodology — judges a custom agent
  configuration file against the subagent and agent-prompt standards, covering
  frontmatter, role framing, constraints, and output contract.
argument-hint: <configured-agent-path>
arguments: configured_agent_path
allowed-tools: Read, Grep, Glob
---

Use skill `instructions:agent-prompt-standards`.

Use skill `instructions:subagent-standards`.

<objective>
An `APPROVED` or `REJECTED` verdict on one custom agent configuration file against `/subagent-standards` and `/agent-prompt-standards`, with findings grouped as critical-issues, recommendations, strengths, and quick-fixes, each naming its location, violated convention, evidence, and consequence.
</objective>

<constraints>

- NEVER: modify the target or another file, run a replacement authoring workflow, or issue a score.
- ALWAYS: judge against the loaded standards and independently discovered requirements.
- ALWAYS: verify every finding's location and distinguish a functional defect from a preference.
- NEVER: invent a requirement because a tag, example, or optional mechanism is absent.
- ALWAYS: cover every applicable standards area before issuing a verdict.

</constraints>

<audit_workflow>

1. Read `instructions:subagent-standards` and `instructions:agent-prompt-standards`.
   They own the rules; creator workflow references supply no additional standard.
2. Require exactly one authored configuration input or native definition path in
   `$configured_agent_path`. An absent,
   unreadable, or multi-file target produces `REJECTED` with a critical issue naming
   the input failure.
3. Apply `/subagent-standards` `<configuration_subject>` to classify the target and
   independently discover any declared source-to-output mapping, and `<configuration>`
   to resolve the target's governing context. Read the whole target, its governing
   decisions, selected profile, owning skill, and result contract.
   Read the exact emitted definitions when the target is a generation input, applying
   the appropriate harness standards to each. Preserve the supplied path as the target.
4. Apply every relevant rule from the loaded standards. Read the complete referenced
   skill when the configuration delegates its behavior; distinguish wrapper obligations
   from behavior the invoked skill already owns.
5. Admit invocation evidence as `/subagent-standards` `<evidence>` requires, reading the
   declared acceptance artifact or the retained native-loading and invocation evidence
   for the target. Missing required evidence remains a finding; do not launch the target
   during this read-only audit.
6. Check the whole target for equivalent functionality before declaring an omission.
   Record only findings backed by an exact standard, location, evidence, and consequence.
7. Emit the existing verdict contract. An unreadable required standard leaves its area
   unjudged and the verdict `REJECTED`.

</audit_workflow>

<verdict_format>
Emit a structured verdict. The skill's entire output is the verdict payload.

The skill's `overall` is `APPROVED` iff the `critical-issues` row has no findings with severity `REJECT`; otherwise it is `REJECTED`. A missing or unreadable subagent file, or an audit that cannot complete, records a `REJECT` critical issue and returns `REJECTED`. Recommendations land as `WARNING` findings; strengths and quick fixes land as `INFO` findings.

```json
{
  "schema_version": 1,
  "skill": "audit-subagent",
  "target": "<configured-agent-path>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    {
      "name": "critical-issues",
      "status": "PASS | FAIL",
      "findings": [
        {
          "id": "f-001",
          "file": "<configured-agent-file>",
          "line": null,
          "rule": "<issue-category>",
          "severity": "REJECT",
          "message": "Current: <…>. Should be: <…>. Why it matters: <…>. Fix: <…>."
        }
      ]
    },
    { "name": "recommendations", "status": "PASS", "findings": [] },
    { "name": "strengths", "status": "PASS", "findings": [] },
    { "name": "quick-fixes", "status": "PASS", "findings": [] }
  ],
  "metadata": {
    "configured_agent_type": "simple | complex | delegation",
    "tool_access": "appropriate | over-permissioned | under-specified",
    "model_selection": "appropriate | reconsider",
    "governing_context_declaration": "<the declaration form read — the owning node's spec assertion or the decision that reaches it — or null when none declares one>",
    "invocation_evidence": "<the acceptance artifact or invocation evidence read, or null when none is retained>"
  }
}
```

</verdict_format>

<failure_modes>

**Failure 1: Flagged a missing tag name when the content was present under a different name.** Claude penalized a subagent for lacking `<workflow>` when its procedure lived under `<approach>`. The audit checks for functionality, not exact tag spelling; a missing function is a finding, a renamed-but-present section is not. Search the whole file for equivalent content before flagging.

**Failure 2: Scored the subagent instead of judging it.** Claude assigned "role clarity 7/10" instead of naming the specific deficiency and its consequence. A score names no location, convention, or fix and the author cannot act on it. Emit findings, never scores.

**Failure 3: Skipped an evaluation area and missed a whole class.** Claude judged TOML configuration and role, formed a verdict, and stopped — leaving tool-access over-permissioning unexamined, so a class of issues passed unseen. The verdict is sound only when every evaluation area was judged; cover them all before issuing the verdict.

**Failure 4: Claude judged an authored template as a native definition.** Claude
rejected a profile-selecting source for absent native fields and requested a literal
model. The audit had skipped the declared generation relationship. Classify the
supplied target first, then judge its template and emitted native configuration in
their respective roles under `/subagent-standards`.

</failure_modes>

<success_criteria>
The verdict is sound when:

- Every applicable rule in the loaded standards was judged, with none skipped.
- The verdict states an overall APPROVED/REJECTED with findings grouped critical-issues / recommendations / strengths / quick-fixes.
- Each finding is falsifiable: it names the location, the convention at issue, and the consequence — every critical issue names what breaks if unfixed, judged on functionality rather than exact tag spelling.
- Every finding is supported by the target and its independently loaded requirements.
- The same configuration, governing requirements, and retained evidence produce the same verdict.

</success_criteria>

<validation>
Before completing the audit, verify:

1. **Completeness**: All evaluation areas assessed
2. **Precision**: Every issue has file:line reference where applicable
3. **Accuracy**: Line numbers verified against actual file content
4. **Actionability**: Recommendations are specific and implementable
5. **Fairness**: Verified content isn't present under different tag names before flagging
6. **Context**: Applied appropriate judgment for custom agent type and complexity
7. **Examples**: At least one concrete example given for major issues

</validation>
