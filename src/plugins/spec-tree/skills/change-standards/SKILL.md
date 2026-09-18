---
name: change-standards
user-invocable: false
description: >-
  Change record standards for Output, maturity, lifecycle, refinement, and
  continuation. Loaded by composing workflows, not invoked directly.
argument-hint: "<Proposed|Framed|Sliced|Executable>"
arguments: maturity
allowed-tools: Read
---

<objective>
The complete Change record contract and one independently loadable Definition of Ready for the selected Maturity.
</objective>

<loading_contract>

Require `$maturity` to equal `Proposed`, `Framed`, `Sliced`, or `Executable` exactly. A missing or unsupported value is a blocked standards load and names the accepted values.

Read `${CLAUDE_SKILL_DIR}/references/change-record.md` completely. Then read exactly one Definition of Ready:

| `$maturity`  | Definition of Ready                                |
| ------------ | -------------------------------------------------- |
| `Proposed`   | `${CLAUDE_SKILL_DIR}/references/dor-proposed.md`   |
| `Framed`     | `${CLAUDE_SKILL_DIR}/references/dor-framed.md`     |
| `Sliced`     | `${CLAUDE_SKILL_DIR}/references/dor-sliced.md`     |
| `Executable` | `${CLAUDE_SKILL_DIR}/references/dor-executable.md` |

NEVER load another Maturity's Definition of Ready in the same invocation. Each file is cumulative and complete for its level. The shared reference owns the record rules; authoring and auditing procedures remain in their respective skills.

</loading_contract>

<success_criteria>

- Each record requirement has one canonical statement in the shared reference.
- Exactly one cumulative Definition of Ready is loaded for the selected Maturity.
- Every loaded criterion has a stable identifier and can be judged from the complete record and necessary repository references.
- The four Maturity values, Lifecycle, lineage, blockers, product truth, and continuation remain distinct.

</success_criteria>
