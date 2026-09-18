# Changelog — coding-agents plugin

Coding-agent environments and coordination: Prowl and herdr pane operation, agent-mail message records, recipient discovery, bounded delegation, and cross-worktree coordination.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.7.0

### Added

- **`/operate-agent-mail`.** A source-owned capability over the agent-mail store: `register`, `send`, `inbox`, and `receipt` map to checked results under the project key read from `spx diagnose --format json`'s `worktree-pool` record, so every worktree of one pool shares one mail project. A message record — `schema`, `kind`, `correlation`, `sender`, `recipient`, `subject`, `body`, `ackRequired` — maps onto the store's fields and reads back without loss; a registration result never carries the store's token; an absent store or diagnosis yields a named unavailable result and no fallback.
- **`/operate-herdr`.** A source-owned capability over the public herdr command surface: `inventory`, `read`, `wait`, `prompt`, `start`, `relaunch`, `stop`, `key`, and `open-worktree` map to checked results with herdr identities and states verbatim; a `read` result carries herdr's terminal text verbatim under `output`, and a `start`, `relaunch`, `wait`, or `prompt` result carries the one hosted session it acted on; the lifecycle codes `server_not_running`, `agent_not_found`, `agent_not_ready`, `agent_blocked`, `agent_prompt_stalled`, and `timeout` project to named statuses; every wait carries an explicit bound; pane-changing operations require mutation authorization in the request.

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
