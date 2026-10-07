# Issues: Agent communication

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## `/message-agents` constraints contradict its workflow, and its objective and description leave outputs and triggers open

**Evidence.** `instructions:skill-auditor` runs `2026-10-07_07-54-09-987-97277308ac36`, `2026-10-07_10-12-43-230-e30afb06559b` and `2026-10-07_10-22-02-701-3582867addbb` on `src/plugins/coding-agents/skills/message-agents` raised eight findings across the three runs, one `blocking` and seven `debt`; the `caller-independence` finding at `SKILL.md:34` is repaired in the changeset and seven remain open:

- `constraint-consistency` at `SKILL.md:100` (`<constraints>`): "NEVER ... use another terminal multiplexer" contradicts the herdr doorbell step at `SKILL.md:26` and the constraint at `SKILL.md:94`, which direct a herdr doorbell through `coding-agents:operate-herdr`.
- `constraint-ambiguity` at `SKILL.md:99`: "no scratch file or shell redirect is part of this workflow" does not say which redirects it excludes, while `<command_forms>` prescribes heredoc stdin.
- `empty-arguments` at `SKILL.md:15` (`<route_selection>`): an empty request or one matching neither shape has no stated route, and the one empty-input rule names only the Prowl fields.
- `objective-output-coverage` at `SKILL.md:28` (`<mail_route>` step 8): the doorbell-resolution output has no place in the objective or the success criteria.
- `description-distinct-triggers` at `SKILL.md:4`: the description claims "sending a message record", the trigger the `operate-agent-mail` description also claims.
- `success-criteria-consistency` at `SKILL.md:21`, `SKILL.md:110` and `SKILL.md:142` (run `2026-10-07_10-12-43-230-e30afb06559b`): step 1 says the script rejects no same-worktree delegation request that lacks `authority`, while `<testing>` and `<success_criteria>` require that a same-worktree request whose authority is other than exactly the sender as owner with Git mutation forbidden produces no record, and no request field says whether a delegation is same-worktree.
- `script-validation-messages` at `scripts/agent_message.py:466-470`, `924-928` and `1229-1237` (same run): three field-set rejections name neither the unexpected nor the missing fields, while the script's other field-set checks report them through `_field_mismatch`.

**Standing.** The findings lie on text the changeset leaves untouched: the diff of the skill against `origin/main` holds the hunks at `SKILL.md:34` and the closing failure-mode paragraph at `SKILL.md:131`, and no hunk in `scripts/agent_message.py`.

**Impact.** A session routing a herdr doorbell meets a NEVER rule that forbids a step the workflow requires, a send-a-message-record request matches two skill descriptions, a same-worktree delegation without an authority yields a record the success criteria say it must not, and a rejected request names no field to fix.

**Settlement condition.** The constraints name the sanctioned endpoint hosts and the excluded redirect form, route selection states the empty and no-match cases, the objective and success criteria cover the doorbell resolution, the description's trigger is distinct from `operate-agent-mail`, the success criteria and the testing record state when an absent authority produces a record, the three script rejections name the unexpected and missing fields as the script's other field-set checks do, and a typed skill audit raises none of the seven findings.
