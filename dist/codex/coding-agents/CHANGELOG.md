# Coding-agents plugin changelog

Coding-agent environments, coordination, and supervision: Prowl and herdr pane operation, agent-mail message records, recipient discovery, bounded delegation, officer fleets, and cross-worktree coordination.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.8.0

### Added

- **`/orchestrate-officers`.** One operator-facing session can supervise officer sessions that each execute one Change through eight bounded operations: launch, order, read, correct, answer, escalate, housekeep, and close. The skill composes `/operate-herdr` and `/operate-agent-mail`, keeps reads event-driven, enforces the two-round ceiling and decision boundary, rebuilds its per-Change ledger from durable mail and verification-journal sources, and relaunches an officer after release so the next order uses the current plugin catalog.
- **Durable officer order and standing-rule contracts.** Bundled references define the complete order envelope, delegation roles, second-rejection procedure, reporting cadence, verdict-reuse rule, temporary `filed` disposition, lifecycle ownership, and known environment and mail constraints. A standard-library entry point derives the minimum versioned ledger from exported mail records and sealed journal runs.

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
