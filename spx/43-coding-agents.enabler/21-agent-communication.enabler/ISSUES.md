# Issues: Agent communication

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## `/message-agents` constraints contradict its workflow, and its objective and description leave outputs and triggers open

**Evidence.** `instructions:skill-auditor` run `2026-10-07_07-54-09-987-97277308ac36` on `src/plugins/coding-agents/skills/message-agents` raised one `blocking` and four `debt` findings:

- `constraint-consistency` at `SKILL.md:100` (`<constraints>`): "NEVER ... use another terminal multiplexer" contradicts the herdr doorbell step at `SKILL.md:26` and the constraint at `SKILL.md:94`, which direct a herdr doorbell through `coding-agents:operate-herdr`.
- `constraint-ambiguity` at `SKILL.md:99`: "no scratch file or shell redirect is part of this workflow" does not say which redirects it excludes, while `<command_forms>` prescribes heredoc stdin.
- `empty-arguments` at `SKILL.md:15` (`<route_selection>`): an empty request or one matching neither shape has no stated route, and the one empty-input rule names only the Prowl fields.
- `objective-output-coverage` at `SKILL.md:28` (`<mail_route>` step 8): the doorbell-resolution output has no place in the objective or the success criteria.
- `description-distinct-triggers` at `SKILL.md:4`: the description claims "sending a message record", the trigger the `operate-agent-mail` description also claims.

**Standing.** The findings lie on text the changeset leaves untouched: the diff of the skill against `origin/main` holds one hunk, the closing failure-mode paragraph at `SKILL.md:131`.

**Impact.** A session routing a herdr doorbell meets a NEVER rule that forbids a step the workflow requires, and a send-a-message-record request matches two skill descriptions.

**Settlement condition.** The constraints name the sanctioned endpoint hosts and the excluded redirect form, route selection states the empty and no-match cases, the objective and success criteria cover the doorbell resolution, the description's trigger is distinct from `operate-agent-mail`, and a typed skill audit raises none of the five findings.
