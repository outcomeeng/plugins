# Issues: Apply

## The decision row is dispatched twice on a changeset that changes a decision

`src/plugins/spec-tree/skills/apply/SKILL.md` requires the ADR or PDR auditor at Step 4 whenever a decision changed, and names those same auditors again in the artifact-auditor gate's dispatch list. A changeset that changes a decision therefore launches its decision auditor twice, contradicting the once-per-kind rule the lane table states. Both generated copies under `dist/` render the same duplicate instruction.

**Evidence.** Finding F-001 of review run `2026-09-19_04-35-13-090-46287928ddf3` against `src/plugins/spec-tree/skills/apply/SKILL.md`.

**Settlement condition**: the artifact-auditor gate's dispatch list names neither `adr-auditor` nor `pdr-auditor`, leaving decision auditing to Step 4 alone.

**Why separate**: the dedup carries different evidence from the gate-taxonomy change that surfaced it, and repairing it inside that changeset would prejudge the split its Frame requires.

## The apply skill loads its whole surface eagerly

`src/plugins/spec-tree/skills/apply/SKILL.md` renders to 47,802 code points under `dist/claude/` and a comparable size under `dist/codex/`, entirely eager, with no `references/` directory. Every activation pays the full gate-selection machinery — the lane table, scope detection, the verification checkpoint, result carryover, the evidence-auditor gate, and the terminal full gate — including an activation the directive description matched by mistake.

This is not a standards breach. `/skill-standards` `<progressive_disclosure>` caps a SKILL.md at 500 lines, and the 40,000-code-point ceiling belongs to `<eager_foundation_exception>`, which governs only a skill invoking that exception to exceed the line limit. This skill is 369 lines and invokes no exception, so neither limit binds it.

**Evidence.** Raised as a warning by two independent skill audits of `src/plugins/spec-tree/skills/apply/SKILL.md`; the second states the non-violation explicitly. An earlier audit asserted a ceiling breach, and the standard's own text does not support that reading.

**Settlement condition**: the conditional detail only some selections consume — the cross-node widening rules, the checkpoint record fields, and the result-carryover projection — loads from cited one-level `references/` files at the step consuming each, leaving the selector tables and the numbered workflow in SKILL.md.

**Why separate**: introducing a `references/` directory restructures the skill's information architecture rather than amending the lines that carry a rule, and the restructured surface needs its own skill audit.
