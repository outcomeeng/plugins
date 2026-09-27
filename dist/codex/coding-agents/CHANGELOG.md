# Coding-agents plugin changelog

Coding-agent environments and coordination: Prowl and herdr pane operation, agent-mail message records, recipient discovery, bounded delegation, and cross-worktree coordination.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.11.0

### Breaking

- **`/operate-herdr`'s `open-worktree` requires `workspace`.** The worktree opens as its own herdr workspace, grouped with the one the request names as a linked-worktree workspace, and the result returns that workspace and its root pane. A request without `workspace` returns `invalid-schema` before any herdr command runs.
- **`/operate-herdr`'s `stop` keeps the pane.** It submits the agent's own `/exit`, so the session ends and the pane stays open at its shell for a `relaunch`. A `prompt` whose text is `/exit` or `/quit` needs mutation authorization, as `stop` does.
- **`/orchestrate-change` Start takes the herdr workspace** as the argument after the worktree root.

### Added

- **`/operate-herdr` creates worktrees.** `create-worktree` takes `workspace` and an absolute `path`, with an optional `branch` and `base`. One authorized operation creates the Git worktree, opens it grouped with the named workspace, and returns the checkout's path, its workspace and its root pane. It records no worktree-occupancy claim; the session `start` launches there claims it.
- **`/orchestrate-change` creates or opens the Executor's worktree.** Start runs `create-worktree` when the root is absent from the pool and `open-worktree` otherwise, each naming the invocation's herdr workspace, and starts the Executor in the root pane herdr returns.

### Changed

- **`/orchestrate-change` restarts an Executor in its kept pane.** When a Handoff records the Executor session's own stop, Check stops the session, claims the Change again for its worktree, and relaunches into the same pane. Collecting a terminal Change stops the session and leaves its pane at its shell.
- **`/operate-herdr`'s inventory reports every hosted agent.** An agent whose evidence lacks a projected field appears as an incomplete item naming the missing fields, and every other agent stays complete. `start`, `relaunch` and `wait` return `agent-evidence-incomplete` when readiness needs a missing field; `read` and `prompt` succeed carrying the incomplete item.

## 0.10.0

### Breaking

- **`/orchestrate-officers` is removed**, with its workflows and its ledger derivation script. `/orchestrate-change` takes its place.

### Added

- **`/orchestrate-change` carries the Orchestrator position's duties for one Change.** Start claims the Change for an Executor and starts that session with spec-tree's `change-executor` definition selected, withholding the structured-question tool on the start and every relaunch. Check reads the Change's `Lifecycle` issue field and its newest Handoff, restarts the Executor when its `Hazards` line records that session's own stop, and reports every other release, with each question verbatim, to the principal once. On Codex, Start returns `unavailable`.

### Changed

- **No skill, manifest or catalog text names an officer.** `/operate-herdr` and the plugin descriptions name the methodology's positions and roles.

## Unreleased

### Breaking

- **Agent mail separates listing, reading, and acknowledging.** `/operate-agent-mail` takes five operations — `register`, `send`, `list`, `read`, and `acknowledge` — and `inbox` and `receipt` are gone, with no alias. `list` takes `agent` and optional `allRecords`, `includeBodies`, and `limit`, returns the records not yet read or acknowledged (every record with `allRecords: true`), and marks nothing. `read` records, for the recipient alone, that it judged one message; `acknowledge` is a read the sender can observe. `register` takes no name and returns the name the store assigns. The capability accepts one versioned JSON request per invocation, never a free-text request. `/message-agents` fetches a record its doorbell names with `list` and then acknowledges it when it carries `ackRequired: true`, and reads it otherwise. `/orchestrate-officers` sends every record through a versioned `send` request, has officers register without a name and report the assigned one, lists with `allRecords: true` for ledger reconstruction and the pre-compaction durability proof, judges only the records addressed to its own identity, and gives every officer order the same judgment rule. Its officer order template's `Exact inbox instruction` field is now `Exact store listing instruction`.
- **The agent-mail project key is the repository, not a checkout.** `/operate-agent-mail` derives the key from the repository's own common Git directory, resolved for the adapter's working directory with every variable removed that could make Git answer the location question from somewhere else (`GIT_DIR`, `GIT_COMMON_DIR`, `GIT_WORK_TREE`, `GIT_CEILING_DIRECTORIES`) and normalized, so a linked worktree, the pool's bare repository, and the pool's main checkout all resolve one mail project and deleting any checkout removes none of it. The previous key was the pool's main checkout path, so a store keyed under the old derivation holds its registrations and message records under a different key; re-register before the first operation on an existing store. Carrying the old project's records into the new key is a store-side change the capability does not perform.
- **`diagnosis-unavailable` is replaced by `repository-unresolved`.** A working directory that is no repository, an absent Git executable, and a repository lookup that reports no absolute common directory each yield `repository-unresolved`. Neither that result nor `store-unavailable` admits a fallback command, key, or store.

### Added

- **`/orchestrate-officers`.** One operator-facing session can supervise officer sessions that each execute one Change through eight bounded operations: launch, order, read, correct, answer, escalate, housekeep, and close. The skill composes `/operate-herdr` and `/operate-agent-mail`, keeps reads event-driven, enforces the two-round ceiling and decision boundary, rebuilds its per-Change ledger from durable mail and verification-journal sources, and relaunches an officer after release so the next order uses the current plugin catalog. Every value a step uses comes from a capability result or the operator's invocation, which supplies each officer's worktree, herdr pane, and herdr agent name, the session's own agent program and model for its one registration, the launch and idle bounds in milliseconds, and optionally the doorbell endpoint of the session's own pane. The close runs in two halves selected by the records the all-records listing returns: the disposal half sends the order for the Change operation once, a repeated invocation sends nothing while that order stands, and the continuation half reads the officer's lifecycle fact through that listing before it stops and relaunches the officer.
- **Durable officer order and standing-rule contracts.** Bundled references define the complete order envelope, delegation roles, second-rejection procedure, reporting cadence, verdict-reuse rule, temporary `filed` disposition, lifecycle ownership, and known environment and mail constraints. A standard-library entry point derives the minimum versioned ledger from exported mail records and sealed journal runs.

### Removed

- **The SPX dependency of every mail operation.** No mail operation invokes an SPX command, so the capability no longer depends on `spx diagnose --format json` — an argument vector the next `@outcomeeng/spx` release retires — and an operation completes where only the store CLI and Git resolve.

### Requires

- **`git` on `PATH`, accepting `rev-parse --path-format=absolute --git-common-dir`.** Every mail operation resolves the project key through that vector before it reaches the store, so the capability depends on Git where it previously depended on the SPX diagnosis. The option arrived in Git 2.31; below it the vector reports no absolute common Git directory, so every operation returns `repository-unresolved`.

## 0.7.1

### Added

- **Mail delivery in `/message-agents`.** A request carrying an agent-mail `recipient`, `correlation`, `body`, and `ackRequired` takes the mail route: `mail-request` builds the message record the agent communication node declares — `schema`, `correlation`, `kind`, `sender`, `recipient`, `subject`, `body`, `ackRequired`, with `id` assigned by the store — and the `/operate-agent-mail` send request carrying it; `mail-result` maps the capability's checked `send` result to `delivered` with the store id and the doorbell line `[<sender>] mail <id>`, or to `delivery-failed` with the capability's status and detail; `doorbell` resolves a pane line to its sender and id against the live agent inventory. A same-worktree `delegation-request` carries `authority` — exactly the sender as `owner` and `gitMutation: false` — rendered at the top of the record body; an `authority` of any other shape, a missing or other owner, `gitMutation` admitted, or any extra field, reaches no record. The doorbell is the only line that reaches a pane; its submission evidence for a Prowl pane is the checked `trailing_enter_sent` record, reported beside the delivered message. The Prowl submission route is unchanged.

## 0.7.0

### Added

- **`/operate-agent-mail`.** A source-owned capability over the agent-mail store: `register`, `send`, `inbox`, and `receipt` map to checked results under the project key read from `spx diagnose --format json`'s `worktree-pool` record, so every worktree of one pool shares one mail project. A message record — `schema`, `kind`, `correlation`, `sender`, `recipient`, `subject`, `body`, `ackRequired` — maps onto the store's fields and reads back without loss; `recipient` names one agent, and a value carrying the store's `,` separator is rejected before any command runs. A row another sender wrote reads back rather than failing the inbox read: without a thread it reads as an `unclassified` record with `correlation: null` and its subject verbatim, and an acknowledgement status other than `pending` or `acked` reads as `ackRequired: false`; a row without the store's `id`, `from`, or `subject` key is a malformed store response and fails the read as `invalid-schema`. A registration result never carries the store's token; an absent store or diagnosis yields a named unavailable result and no fallback.
- **`/operate-herdr`.** A source-owned capability over the public herdr command surface: `inventory`, `read`, `wait`, `prompt`, `start`, `relaunch`, `stop`, `key`, and `open-worktree` map to checked results with herdr identities and states verbatim; a `read` result carries herdr's terminal text verbatim under `output`, and a `start`, `relaunch`, `wait`, or `prompt` result carries the one hosted session it acted on; the lifecycle codes `server_not_running`, `agent_not_found`, `agent_not_ready`, `agent_blocked`, `agent_prompt_stalled`, and `timeout` project to named statuses; every wait carries an explicit bound; pane-changing operations require mutation authorization in the request; a text argument beginning with `--`, which herdr reads as one of its options, is rejected with `invalid-schema` before any command runs.

### Requires

- **`@outcomeeng/spx` 0.7.0 or newer.** `/operate-agent-mail` derives the mail project key from the `worktree-pool` record's `mainCheckoutPath` in `spx diagnose --format json`.
- **`am` and `herdr` on `PATH`.** Each capability returns its named unavailable result when its executable or server is absent.

## 0.6.1

### Fixed

- **Production requests use source-generated handback commands.** Callers provide semantic completion text, and `/operate-prowl` returns one structured block whose command ends at `run`, carries checked submission criteria, and cannot gain a stray trailing argument during prompt assembly.

## 0.6.0

### Breaking

- **`/message-agents` requests require `recipientPath`.** Supply the recipient's absolute worktree, repository, or working-directory path. A previous `toPane` value remains an optional identity assertion and is no longer sufficient by itself.

### Added

- **Path-based Prowl target resolution.** `/operate-prowl` maps an operator-supplied work path to complete matching agent-pane metadata and candidate-specific send request templates.

## 0.5.0

### Removed

- `Skill` from the lifecycle skill's `allowed-tools`
- `MARKETPLACE-CHANGELOG.md`; it ships with the spec-tree plugin

## 0.4.0

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports this plugin's changelog and the marketplace changelog. Each is read from disk, without network access.

This changelog begins here; earlier history predates the line.
