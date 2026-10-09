# Issues: Agent communication

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## `/message-agents` description claims a trigger the `operate-agent-mail` description may also claim

**Evidence.** `instructions:skill-auditor` run `2026-10-07_07-54-09-987-97277308ac36` on `src/plugins/coding-agents/skills/message-agents` raised a `debt` finding, rule `description-distinct-triggers`, at `SKILL.md:4`: the description claims "sending a message record to a registered agent-mail name with its one-line doorbell", the trigger the `operate-agent-mail` description also claims.

**Standing.** Unjudged. The advisor could not judge it without the two complete selection descriptions and the alleged ambiguous case: an overlap in "sending a message record" alone does not establish indistinct selection, because a message-and-doorbell orchestrator and its underlying mail adapter can legitimately compose.

**Impact.** A request to send a message record may match both skill descriptions.

**Settlement condition.** The two complete descriptions and a concrete request that selects the wrong skill are compared, and the descriptions either differ in their triggers or the comparison shows the composition is intended.

## DEBT: `/message-agents` states a narrower unrenderable-label rule than the node declares

The spec, the message-record decision, and the bundled script render a label only when it is non-empty, `str.isprintable()` holds for it, and it holds none of `[`, `]`, `<`, `>`. `src/plugins/coding-agents/skills/message-agents/SKILL.md` states the older rule in two places: workflow step 4 (line 24) calls a label unrenderable when it is empty, carries a line break, or carries a delimiter, and the testing record (line 111) lists the same three conditions. The generated `dist/` copies carry the same text, and so does the coordination-decision eval prompt `spx/43-coding-agents.enabler/32-inter-worktree-coordination.enabler/evals/coordination-decision/prompt.md` (lines 1992 and 2079), which embeds the skill body.

**Impact**: a caller reading the skill predicts a labeled doorbell for a label holding a tab, ESC, another control character, a format character, or a Unicode line or paragraph separator, while the script renders the unlabeled form. The eval scores its producer against the same outdated text.

**Settlement condition**: the skill body states the rule the node declares, or states the outcome a caller handles without restating the predicate the script owns, the generated copies are rebuilt from it, the eval prompt carries the current skill text, and the skill surface passes the typed skill auditor.

**Why separate**: the repair is a skill-surface edit, which carries its own skill-auditor gate and plugin version step, and the eval prompt belongs to `spx/43-coding-agents.enabler/32-inter-worktree-coordination.enabler`.

**Evidence**: `spec-tree:changes-reviewer` run `2026-10-09_21-16-21-663-cb5623784a49` on head `f2e86d4c4637f466795d15c787f442fb1b79205c`, a `consistency` finding at `src/plugins/coding-agents/skills/message-agents/SKILL.md` line 24.
