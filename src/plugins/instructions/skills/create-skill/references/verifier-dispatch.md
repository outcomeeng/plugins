<objective>
The dispatch mechanics and per-role role-task contracts for every configured verifier and reviewer a governed flow dispatches, loaded with the dispatching skill so they survive root-instruction compaction and truncation.
</objective>

<contents>

- `<dispatch_mechanics>` — how this harness launches a configured role and collects its result
- `<role_task_contracts>` — the per-role input fields and the output contract that passes or blocks the gate

</contents>

<dispatch_mechanics>

Skills run in the main conversation. Agents preload the skill and run autonomously in their own agent sessions. Audit agents return structured verdicts; changeset reviewer agents return the raw review journal token for the main conversation to inspect and process through the governing review workflow. Dispatch agents in parallel when auditing multiple targets; the managed router's `### Sub-agent dispatch` section governs when to dispatch one.

{!% include 'agentic-execution/subagent-dispatch-mechanics/fragment.md' %!}

</dispatch_mechanics>

<role_task_contracts>

{!% include 'agentic-execution/configured-verifier-contracts/fragment.md' %!}

</role_task_contracts>
