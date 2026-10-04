---
name: change-standards
user-invocable: false
description: >-
  Change record standards for Intent, maturity, lifecycle, authority,
  refinement, and continuation. Loaded by other skills, not invoked directly.
argument-hint: "<Proposed|Framed|Sliced|Executable|Lifecycle>"
arguments: selection
allowed-tools: Read
---

<objective>
The complete Change record contract, accompanied by exactly one selected reference: the cumulative Definition of Ready for one Maturity, or the Lifecycle transition rules for the declared store.
</objective>

<loading_contract>

Require `$selection` to equal `Proposed`, `Framed`, `Sliced`, `Executable`, or `Lifecycle` exactly. A missing or unsupported value is a blocked standards load and names the accepted values.

Read `${SKILL_DIR}/references/change-record.md` completely for every selection. Then read exactly one selected reference:

| `$selection` | Reference                                   |
| ------------ | ------------------------------------------- |
| `Proposed`   | `${SKILL_DIR}/references/dor-proposed.md`   |
| `Framed`     | `${SKILL_DIR}/references/dor-framed.md`     |
| `Sliced`     | `${SKILL_DIR}/references/dor-sliced.md`     |
| `Executable` | `${SKILL_DIR}/references/dor-executable.md` |
| `Lifecycle`  | `${SKILL_DIR}/references/lifecycle.md`      |

NEVER load another Maturity's Definition of Ready in the same invocation. Each Definition of Ready is cumulative and complete for its level.

`change-record.md` states the record rules, and each Definition of Ready states criteria that judge a record against those rules by identifier; neither carries a store command. `lifecycle.md` carries the store-binding, canonical-state, authority-read, ordered-write, complete-readback, write-inspection, inert-stdin, claim-record, handoff-record, confirmation-record, and terminal-record rules, together with the store commands those rules name; it alone assigns each field's home in the declared store and names the reads that establish authority, so a record rule that needs a field home or an authority read applies under the `Lifecycle` selection.

</loading_contract>

<success_criteria>

- Each record rule is stated once, in `change-record.md`; a Definition of Ready criterion cites the rule it applies by identifier and adds only the level's own condition.
- Exactly one selected reference is loaded beside `change-record.md`: the cumulative Definition of Ready for a Maturity, or the Lifecycle rules.
- Every loaded criterion has a stable identifier and can be judged from the complete record and necessary repository references.
- The authority for each Maturity advance is read from the store's field-change events and confirmation comments under `authority-read`, and no rule or criterion requires body authority text.
- The four Maturity values, the six Lifecycle values, lineage, blockers, authority, product truth, and continuation remain distinct.

</success_criteria>
