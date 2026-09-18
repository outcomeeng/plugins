---
name: change-standards
user-invocable: false
description: >-
  Change record standards for Output, maturity, lifecycle, refinement, and
  continuation. Loaded by composing workflows, not invoked directly.
argument-hint: "<Proposed|Framed|Sliced|Executable|Lifecycle>"
arguments: selection
allowed-tools: Read
---

<objective>
The complete Change record contract plus one independently loadable Definition of Ready for the selected Maturity, or the Lifecycle transition rules for the declared store.
</objective>

<loading_contract>

Require `$selection` to equal `Proposed`, `Framed`, `Sliced`, `Executable`, or `Lifecycle` exactly. A missing or unsupported value is a blocked standards load and names the accepted values.

Read `${CLAUDE_SKILL_DIR}/references/change-record.md` completely. Then read exactly one selected reference:

| `$selection` | Reference                                          |
| ------------ | -------------------------------------------------- |
| `Proposed`   | `${CLAUDE_SKILL_DIR}/references/dor-proposed.md`   |
| `Framed`     | `${CLAUDE_SKILL_DIR}/references/dor-framed.md`     |
| `Sliced`     | `${CLAUDE_SKILL_DIR}/references/dor-sliced.md`     |
| `Executable` | `${CLAUDE_SKILL_DIR}/references/dor-executable.md` |
| `Lifecycle`  | `${CLAUDE_SKILL_DIR}/references/lifecycle.md`      |

NEVER load another Maturity's Definition of Ready in the same invocation. Each Definition of Ready is cumulative and complete for its level. `lifecycle.md` carries the store-binding, ordered-write, complete-readback, write-inspection, inert-stdin, and Claim, Handoff, and terminal-record rules. The shared references own the rules and no procedure.

</loading_contract>

<success_criteria>

- Each record requirement has one canonical statement in the shared reference.
- Exactly one selected reference is loaded: the cumulative Definition of Ready for a Maturity, or the Lifecycle rules.
- Every loaded criterion has a stable identifier and can be judged from the complete record and necessary repository references.
- The four Maturity values, the five Lifecycle values, lineage, blockers, product truth, and continuation remain distinct.

</success_criteria>
