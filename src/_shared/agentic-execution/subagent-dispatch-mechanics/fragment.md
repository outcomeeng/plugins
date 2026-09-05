{!% if target == 'claude' %!}
**Use the `Agent` tool for every configured verifier or reviewer.** Launch in the foreground with `subagent_type` set to the exact configured agent type and `prompt` set to the role-task body from the shared contracts. The completed `Agent` tool result is that configured agent's final message; apply the matching output contract to that message. An error, missing final message, or output outside the matching contract blocks the gate.
{!% else %!}
**Read each file fully in its designated context.** A file the user names is read in the main conversation. A file this conversation authored is verified by a configured verifier or reviewer in an independent context. Subagents may locate files; a file the main conversation needs is then read in the main conversation in full.

**Dispatch each named role through the runtime's exposed typed-subagent spawn capability** (`{{! tool('spawn_agent') !}}` when that identifier is available), spawning the matching subagents in parallel when several roles apply. The managed router's `### Sub-agent dispatch` section governs when to dispatch, forbids asking the operator to confirm, and blocks the gate when a named role cannot be dispatched; this reference governs only the Codex mechanics. Act only on the result the subagent returns.

**STOP TRIGGER — in the main authoring conversation, discover deferred agent tools before reporting an agent unavailable.**

If a named agent or lifecycle tool is absent from the initial list, inspect the runtime's complete deferred-tool registry. Use top-level `functions.exec`; inside it, inspect `ALL_TOOLS`. Treat `exec_command` as the nested shell tool. Check typed `{{! tool('spawn_agent') !}}` and its `Available roles`; an exact match proves availability. Report unavailable only when discovery finds no typed spawn capability or omits the exact role, and include that result. Visible catalogs, initial tools, generated rosters, and local `agents/*.md` files are not availability evidence.

**Use the exposed multi-agent tool schema exactly.** The examples below use the `multi_agent_v1` identifiers emitted by this Codex harness. When the runtime exposes different identifiers, discover the equivalent typed spawn, wait, send-input, and close capabilities and preserve the same fields and result contracts. The initial turn goes in `message`; use `items` only when the turn must pass structured mentions. Omit `fork_context`, `model`, `reasoning_effort`, and `service_tier` for the typed verifier and reviewer agents. Full-history forks are incompatible with changing `agent_type` in this harness, and the named verifier/reviewer roles already carry their own model settings. Store every returned agent id verbatim. The role task is the spawn's initial `message`, so one spawn and one wait complete a role. After spawning, continue only non-overlapping work while the subagent runs, then collect the result with the exposed wait capability and close the child immediately. Completed agents remain open until closed and can interfere with future spawns.

**Subagent lifecycle — preserve every handle and close every thread.** Treat every spawned subagent as an owned resource. Maintain a registry in the main conversation containing its exact `agent_id`, role or task, and lifecycle state. Record a successful spawn's returned id before issuing another spawn or making any unrelated tool call. Preserve every unresolved registry entry across interruption and compaction.

**Acquire handles sequentially while agents execute concurrently.** Call `{{! tool('spawn_agent') !}}` once per tool call. Several sequential spawn calls may occur within one main-agent tool-call sequence before control returns to the operator, and every agent already spawned may run concurrently while later calls are issued. NEVER place multiple spawn calls in `Promise.all`, another fail-fast combinator, or one parallel tool-call batch: one rejected call can suppress successful sibling results and lose their ids even though those agents remain open. Respect the runtime's configured `agents.max_threads` limit; NEVER hard-code a maximum such as eight and NEVER fill capacity with agents that are not required.

Before each spawn sequence, reconcile the registry: preserve any final results already returned, close their agents, and close work that has been abandoned or superseded. If a spawn fails, stop issuing new spawns, retain every id already acquired, and collect or close those known agents before retrying. A failed individual spawn yields no id for that call and does not erase ids returned by earlier calls.

**Collect, preserve, then close.** Use `{{! tool('wait_agent') !}}` with only exact ids from the registry. A timeout with no final status is non-final. When the result remains required, wait again; when the work is explicitly abandoned or superseded, close the agent. For every final status, preserve the complete final message, structured verdict, or journal token first, then close the child and mark it closed in the registry. A notification, pending handle, or open id is never a final result.

Reconcile every registry entry at these checkpoints:

- immediately after a final result;
- before another spawn sequence;
- after any spawn failure;
- after interruption or compaction;
- before asking the operator a question;
- before entering a merge or publication phase; and
- before yielding control to the operator or ending the turn.

At a checkpoint, wait again for every still-required result and close every abandoned or superseded agent. Before merge, publication, or response end, every known id must be closed and every required result must already be preserved. Do not leave completed agents open; completed agents continue consuming thread capacity until closed.

NEVER invent, shorten, or substitute an agent id, including an all-zero placeholder. NEVER assume `multi_agent_v1.list_agents` exists; if the runtime exposes a listing tool, use it only to reconcile the registry. The interactive `/agent` picker is operator-side recovery when registry reconstruction is impossible, never a substitute for preserving ids. If `{{! tool('close_agent') !}}` returns `not_found`, record that exact result and do not call `multi_agent_v1.resume_agent` merely to close the id. Resume only when intentionally continuing a known closed agent's work.

**Spawn each verifier or reviewer with its role task as the initial turn.** The `agent_type` binds the child to its configured agent definition, so the role task goes directly in the spawn's `message` and no separate turn precedes it:

```json
{
  "tool": "{{! tool('spawn_agent') !}}",
  "arguments": {
    "agent_type": "<exact-agent-type>",
    "message": "<role-task>"
  }
}
```

Record the returned agent id verbatim, then collect the role-task result with `{{! tool('wait_agent') !}}`. The role task passes only through its own output contract; an error, timeout, missing final message, or output outside that contract blocks the gate. Record the full agent id and observed result, and close the child.

Wait once for one or more spawned agents. Use the 10-minute individual-file timeout for subagents such as `{{! agent_role('spec-tree', 'implementation-auditor') !}}` or `{{! agent_role('spec-tree', 'spec-auditor') !}}`:

```json
{
  "tool": "{{! tool('wait_agent') !}}",
  "arguments": {
    "targets": ["<agent-id-from-spawn-agent>"],
    "timeout_ms": 600000
  }
}
```

Use the 30-minute changeset timeout only for `{{! agent_role('spec-tree', 'changes-reviewer') !}}` role work:

```json
{
  "tool": "{{! tool('wait_agent') !}}",
  "arguments": {
    "targets": ["<agent-id-from-spawn-agent>"],
    "timeout_ms": 1800000
  }
}
```

Close a completed or no-longer-needed agent:

```json
{
  "tool": "{{! tool('close_agent') !}}",
  "arguments": {
    "target": "<agent-id-from-spawn-agent>"
  }
}
```

In the main authoring conversation, if `{{! tool('spawn_agent') !}}`, `{{! tool('wait_agent') !}}`, or `{{! tool('close_agent') !}}` is not initially exposed, discover it through the runtime's complete deferred-tool registry before concluding the capability or role is unavailable. Accept a subagent notification only when the harness delivers it while the main conversation is working or waiting; do not choose notifications as the planned result-collection mechanism. Do not use web search, time lookup, shell polling, or `{{! tool('ask_user') !}}` or any other tools as a substitute for result collection.

**Result collection for verifier and reviewer agents.** The exposed typed wait capability (`{{! tool('wait_agent') !}}` in the examples below) is the planned result-collection mechanism for the role task. Read its returned JSON, keyed by the spawned subagent id under `status`. A timeout returns an empty `status` object and is not a result. A final status for the target id is the turn result; when that final status carries a final message, that message is the turn output. Do not infer success from a subagent notification, a pending handle, or an open subagent id.

Successful `{{! agent_role('spec-tree', 'changes-reviewer') !}}` result shape:

```json
{
  "status": {
    "<agent-id-from-spawn-agent>": {
      "status": "completed",
      "message": "<raw-spx-review-journal-token>"
    }
  },
  "timed_out": false
}
```

Blocked or incomplete result shape:

```json
{
  "status": {},
  "timed_out": true
}
```

**Codex `{{! agent_role('spec-tree', 'changes-reviewer') !}}` output contract.** For `agent_type: "{{! agent_role('spec-tree', 'changes-reviewer') !}}"`, a successful final message is the raw `spx journal --type review` run token. Treat that token as the only review result. Inspect the review by reading or rendering the sealed journal prefix for that token. Do not ask the reviewer to summarize findings, do not accept a prose summary as the gate result, and do not run `spec-tree:review-changes` in the main thread to replace a missing token.

**Codex blocked-result rule.** If `wait_agent` returns an error, `not_found`, timeout with no final status, usage-limit failure, model-capacity failure, or any final message that is not a raw review journal token, the review gate is blocked. Record the exact agent id, tool result, and blocking reason. Do not publish, merge, or mark the gate passed. When repairing a finding or blocked subject, rerun deterministic verification, create a new local checkpoint commit, and review that new head; an operator-approved process exception is the only other path past the gate.

**Use raw scope only for the `{{! agent_role('spec-tree', 'changes-reviewer') !}}` role task.** The review agent owns `spec-tree:review-changes`, severity taxonomy, scope expansion, and finding shape. Pass only the raw scope token as the spawn `message`: `HEAD` for the current committed branch scope, `origin/<base>...HEAD` for a specific committed range, a branch name, or a PR reference. Confirm the worktree is clean before dispatch; commit the exact current version before the reviewer agent session reads it.

- ALWAYS prepare the worktree first: isolate the intended changes, sync to the base using the `spec-tree:sync-base` skill when the governing workflow requires it, pass deterministic verification, create a local checkpoint commit, and leave the worktree clean so the reviewer judges an exact committed head. Never dispatch the reviewer over a working diff.
- NEVER invoke the `spec-tree:review-changes` skill in the main authoring conversation; the `{{! agent_role('spec-tree', 'changes-reviewer') !}}` invokes it inside its isolated role workflow.
- NEVER pass a prose prompt, restate review instructions, add severity filters, or tell the reviewer to focus only on new changes, or what to emphasize.

```json
{
  "tool": "{{! tool('spawn_agent') !}}",
  "arguments": {
    "agent_type": "{{! agent_role('spec-tree', 'changes-reviewer') !}}",
    "message": "HEAD"
  }
}
```

```json
{
  "tool": "{{! tool('spawn_agent') !}}",
  "arguments": {
    "agent_type": "{{! agent_role('spec-tree', 'changes-reviewer') !}}",
    "message": "origin/<base>...HEAD"
  }
}
```

**Use explicit prompts for audit-agent role tasks.** The `message` field comes from the `{{! tool('spawn_agent') !}}` schema. This reference owns the prompt content below for required verifier roles. Keep the prompt narrow: repository path, governed artifact paths, governing node or decision, deterministic verification state when relevant, audit task, and output shape. Do not ask the subagent to edit files.

Use this shape for an implementation audit:

```json
{
  "tool": "{{! tool('spawn_agent') !}}",
  "arguments": {
    "agent_type": "{{! agent_role('spec-tree', 'implementation-auditor') !}}",
    "message": "Repository: <absolute-repository-path>\nScope: <base>..<head> committed changeset scope\nLive file list: <none for reusable gate evidence | full modified and untracked paths for explicit advisory audit>\nGoverning node(s): <full spx/... path(s)>\nDeterministic verification already run: <commands and results, or advisory state>\nRun driver identity: {\"producerKind\":\"agent\",\"agentName\":\"implementation-auditor\",\"agentOwningPluginName\":\"spec-tree\",\"skillName\":\"audit-implementation\",\"skillOwningPluginName\":\"spec-tree\",\"invocationRole\":\"run-driver\"}\nTask: Run the implementation audit through spx verification run. Return the run token and rendered projection; the complete blocked SPX diagnostic with run token or not-started, exact command, payload source, payload key, exit code, and stderr; or the complete pre-run skill-load diagnostic with run token not-started, required skill spec-tree:audit-implementation, and the exact load or availability failure."
  }
}
```

**Codex `{{! agent_role('spec-tree', 'implementation-auditor') !}}` output contract.** A successful final message carries the raw `spx verification run` token and rendered projection, without a competing prose verdict envelope. Treat the projection's `terminalStatus` as authoritative: `approved` passes the implementation-audit gate and `rejected` requires repair. A command-failure `BLOCKED` result leaves the gate blocked and must carry the run token or `not-started`, exact command, payload source, payload key, exit code, and stderr. A pre-run skill-load `BLOCKED` result also leaves the gate blocked and must carry run token `not-started`, required skill `spec-tree:audit-implementation`, and the exact load or availability failure. A missing token or projection, a terminal status outside that vocabulary, or an incomplete blocked diagnostic also leaves the gate blocked.

**Implementation audit subject.** A gate-eligible implementation audit reads an exact locally committed subject, carries `Live file list: none`, and runs only after applicable deterministic verification passes on that subject. An explicit advisory implementation audit may carry the full modified and untracked path list; its result supplies no reusable gate evidence.

**Full deterministic gate ordering.** When the repository declares a full deterministic bundle, run its declared command only after every applicable prior agentic gate has converged on the same clean committed head — including evidence audits, decision audits with any required language-architecture concerns, implementation audits, skill or subagent audits, and changeset review. Never launch it before agentic verification, from inside an agent, or concurrently with another heavy command. Any later change invalidates the full-gate result and requires the affected agentic checks to converge again before rerunning the full bundle.

Use this shape for test-evidence audits:

```json
{
  "tool": "{{! tool('spawn_agent') !}}",
  "arguments": {
    "agent_type": "{{! agent_role('spec-tree', 'test-evidence-auditor') !}}",
    "message": "Repository: <absolute-repository-path>\nGoverning node: <full spx/... node path>\nSpec assertions: <full assertion text or exact spec file path plus assertion headings>\nTest files: <full paths to test files under the node>\nTask: Audit whether the test evidence proves the listed assertions without weakening the selected verification type or test assertion type. Return only the audit-tests JSON verdict, with schema_version 1, skill audit-tests, overall APPROVED or REJECTED, rows, and metadata. Do not add prose outside the JSON object."
  }
}
```

Use this shape for eval-evidence audits:

```json
{
  "tool": "{{! tool('spawn_agent') !}}",
  "arguments": {
    "agent_type": "{{! agent_role('spec-tree', 'eval-evidence-auditor') !}}",
    "message": "Repository: <absolute-repository-path>\nGoverning node: <full spx/... node path>\nSpec assertions: <full [eval] assertion text or exact spec file path plus assertion headings>\nEval artifacts: <full paths to eval.toml, prompt.md, cases.jsonl, and history.jsonl>\nProducer artifacts: <full paths to the producing skill, agent, classifier, script, or command source>\nTask: Audit whether the eval evidence proves the listed assertions without replacing the real producer with a prompt-only simulation. Return the JSON verdict specified by audit-eval-evidence, with overall PASS, FAIL, or UNKNOWN and row findings for failed evidence properties. Do not add prose outside the JSON object."
  }
}
```

Use this shape for spec-node audits:

```json
{
  "tool": "{{! tool('spawn_agent') !}}",
  "arguments": {
    "agent_type": "{{! agent_role('spec-tree', 'spec-auditor') !}}",
    "message": "Repository: <absolute-repository-path>\nNode: <full spx/... node path>\nTask: Audit the node spec for assertion quality, evidence tags, atemporal voice, decision alignment, and spec-tree structure. Return only the audit-specs JSON verdict, with schema_version 1, skill audit-specs, overall APPROVED or REJECTED, the section-structure, atemporal-voice, and tag-fitness rows, and metadata. Do not add prose outside the JSON object."
  }
}
```

Use this shape for decision audits:

```json
{
  "tool": "{{! tool('spawn_agent') !}}",
  "arguments": {
    "agent_type": "{{! agent_role('spec-tree', 'adr-auditor') !}}",
    "message": "Repository: <absolute-repository-path>\nDecision file: <full spx/.../*.adr.md path>\nGoverning node: <full spx/... node path>\nAudit scope: <exact committed changeset or artifact scope>\nScope classification: <language-neutral | implementation-language partitions: comma-separated languages>\nTask: Audit the ADR for decision structure, atemporal voice, tag validity, and every language-specific architecture concern required by the scope classification. Return only the structured JSON verdict specified by audit-adr, with no prose outside the JSON object."
  }
}
```

```json
{
  "tool": "{{! tool('spawn_agent') !}}",
  "arguments": {
    "agent_type": "{{! agent_role('spec-tree', 'pdr-auditor') !}}",
    "message": "Repository: <absolute-repository-path>\nDecision file: <full spx/.../*.pdr.md path>\nGoverning node: <full spx/... node path>\nTask: Audit the PDR for product-decision structure, atemporal voice, tag validity, downstream alignment, and evidence quality. Return only the audit-pdr JSON verdict, with schema_version 1, skill audit-pdr, overall APPROVED or REJECTED, the content-classification, property-quality, tag-validity, atemporal-voice, and consistency rows, and metadata. Do not add prose outside the JSON object."
  }
}
```

Use this shape for skill audits:

```json
{
  "tool": "{{! tool('spawn_agent') !}}",
  "arguments": {
    "agent_type": "{{! agent_role('instructions', 'skill-auditor') !}}",
    "message": "Repository: <absolute-repository-path>\nSkill content: <full paths to every changed artifact governing the skill surface, including SKILL.md files, skill subdirectory files, authored shared fragments, and generated runtime copies>\nGoverning node(s): <full spx/... path(s) when known>\nDeterministic verification already run: <commands and results, or why this audit is being run before verification>\nTask: Audit the changed skill content for skill-authoring standards, agent-prompt standards, progressive disclosure, portability, voice, and structure; also audit the complete plugin skill-name set when the active repository skill-authoring overlay requires a plugin-wide naming audit. Return only the structured JSON verdict specified by instructions:audit-skill, with no prose outside the JSON object."
  }
}
```

Use this shape for one subagent audit. When several custom-agent configurations changed, dispatch one `{{! agent_role('instructions', 'subagent-auditor') !}}` per file: acquire each handle sequentially, then let the role tasks run concurrently.

```json
{
  "tool": "{{! tool('spawn_agent') !}}",
  "arguments": {
    "agent_type": "{{! agent_role('instructions', 'subagent-auditor') !}}",
    "message": "Repository: <absolute-repository-path>\nCustom agent file: <full path to one changed agent-directory file in the checkout>\nGoverning node(s): <full spx/... path(s) when known>\nDeterministic verification already run: <commands and results, or why this audit is being run before verification>\nTask: Audit the changed custom agent configuration for subagent-authoring standards, prompt voice, tool boundaries, model settings, skill preloads, and output contract. Return only the structured JSON verdict specified by instructions:audit-subagent, with no prose outside the JSON object."
  }
}
```

{!% endif %!}
