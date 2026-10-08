# Issues: Agent communication

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## `/message-agents` description claims a trigger the `operate-agent-mail` description may also claim

**Evidence.** `instructions:skill-auditor` run `2026-10-07_07-54-09-987-97277308ac36` on `src/plugins/coding-agents/skills/message-agents` raised a `debt` finding, rule `description-distinct-triggers`, at `SKILL.md:4`: the description claims "sending a message record to a registered agent-mail name with its one-line doorbell", the trigger the `operate-agent-mail` description also claims.

**Standing.** Unjudged. The advisor could not judge it without the two complete selection descriptions and the alleged ambiguous case: an overlap in "sending a message record" alone does not establish indistinct selection, because a message-and-doorbell orchestrator and its underlying mail adapter can legitimately compose.

**Impact.** A request to send a message record may match both skill descriptions.

**Settlement condition.** The two complete descriptions and a concrete request that selects the wrong skill are compared, and the descriptions either differ in their triggers or the comparison shows the composition is intended.
