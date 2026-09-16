# Repository Installation

PROVIDES `just install-marketplace` for persistent installation and `just verify-marketplace-installation` for isolated end-to-end proof
SO THAT marketplace maintainers and the merge lifecycle
CAN refresh exactly the selected plugins in every Claude Code checkout on the machine and the selected Codex home while preserving activation, and verify installation behavior with disposable state and native saved-login refresh for subscription discovery

## Assertions

- ALWAYS: persistent selection is the catalog-bounded Claude Code inventory recorded for the invocation checkout at project or local scope, or the catalog-bounded plugin keys in the selected Codex home's raw configuration, including disabled plugins and plugins with missing caches; product overrides never change that home-wide set.
- ALWAYS: persistent Claude Code refresh reaches every `outcomeeng` install record on the machine, updating each natively at its own scope from its own project path so that every Claude Code session on the machine starts and reloads at the canonical source; the machine registry's marketplace entry is validated against the canonical source first, and a record it cannot refresh — outside the catalog, outside project and local scope, with a project path that is no existing directory, in a project whose own settings register a noncanonical source, or in a project whose settings cannot be read — is reported and left unchanged. The invocation checkout's own declared source is validated before any plan: a noncanonical declaration or unreadable settings stop the run.
- Given an empty selected Codex home, when persistent installation runs, then only `spec-tree` is registered and cached, its home activation is explicitly disabled, and the run warns that the operator can select additional plugins.
- Given an invocation checkout with no `outcomeeng` install record at project or local scope, when bootstrap runs, then only `spec-tree` is installed at project scope, declared project activation is preserved, and absent activation defaults to disabled with a warning; a checkout recording a plugin at either scope is refreshed through that record's native update and receives no install or enable.
- Given a trusted product enabling a home-disabled plugin, when that product loads, then the plugin's skills are active for that product; a product that supplies no override retains disabled activation, and a home-wide refresh preserves both products' configuration and the home's activation.
- Given configured home plugins whose marketplace snapshot or plugin cache is absent, when refresh runs or resumes after interruption, then all selected published plugins become available with the same activation and no additional selection, including when the marketplace revision is unchanged.
- Given an existing noncanonical marketplace source for either agent, when persistent preflight runs, then it reports the observed and canonical sources and the need for explicit repair, and no agent performs a state-changing operation. ([test](tests/test_repository_installation.scenario.l1.py))
- For each supported agent, refreshing a valid selected subset preserves every pre-run activation entry, including disabled plugins and explicitly enabled home plugins, while updating every selected published plugin through native refresh operations.
- Given an unexpected selection or activation write during persistent execution, when verification detects it, then the run reports failure and retains the changed state for diagnosis without restoring an earlier settings snapshot or issuing compensating activation commands.
- ALWAYS: selected Codex plugins' subagent definitions remain globally registered under the selected home's digest-bound ownership record regardless of product skill activation; disabling a plugin in a product neither removes its home definitions nor generates a product registry.
- ALWAYS: a pending-publication result names a selected plugin whose absence from the canonical source is established, preserves its prior owned definitions, and reports it separately from successfully refreshed plugins; other failures stop all later operations.

### Scenarios

- Given a native probe command whose parent emits a byte sequence that is invalid UTF-8 and exits while a descendant keeps the captured output stream open, when the runner collects the result, then it returns the parent's completed result promptly, replaces undecodable bytes, and terminates the descendant before returning. ([test](tests/test_native_profile_process.scenario.l1.py))
- Given a native probe command whose parent and descendant remain running, when the execution timeout expires, then the runner reports the timeout promptly and terminates the descendant before returning. ([test](tests/test_native_profile_process.scenario.l1.py))

- Given a nonempty selected subset that omits `spec-tree`, when persistent installation starts, then it reports the invalid selection and performs no state-changing operation. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a selected plugin absent from the registered checkout marketplace, when isolated installation runs, then the absence is terminal at that plugin's install. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a user-scoped Claude Code `outcomeeng` marketplace registration, when persistent installation starts, then it reports the colliding settings path and performs no state-changing operation. ([test](tests/test_repository_installation.scenario.l1.py))
- Given `just verify-marketplace-installation`, when the recipe runs, then it passes the repository-installation node's tests directory to the repository test command so pytest discovers every evidence file. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a generated subset omitting `spec-tree`, when isolated installation plans that selection, then it reports the invalid subset before an agent CLI mutates state. ([test](tests/test_repository_installation.scenario.l1.py))
- Given unchanged committed catalogs and checkout content, when isolated installation runs twice against the same disposable homes, then the first run places every shipped Codex agent definition in the disposable home's agent directory beside the skills it invokes, and the second run succeeds with the same installed and home-placed state. ([test](tests/test_repository_installation.scenario.l3.py))
- Given a persistent marketplace inspection that fails, when persistent installation runs, then it reports a failure naming that operation and attempts no plan operation. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a checkout declaring the canonical marketplace source and an agent home whose live marketplace listing lacks the marketplace, when persistent installation plans, then the plan adds the marketplace for that agent instead of refreshing it. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a Claude Code listing entry at project scope that names no project path, when persistent installation plans, then it reports the listing defect and issues no command. ([test](tests/test_repository_installation.scenario.l1.py))
- Given an invocation checkout whose own Claude Code settings cannot be read, when persistent preflight runs, then it reports that settings path and issues no state-changing command. ([test](tests/test_repository_installation.scenario.l1.py))
- Given Claude Code's marketplace registry carrying `outcomeeng` from a noncanonical source, when persistent installation plans, then it reports the observed and canonical sources and the need for explicit repair and issues no state-changing command. ([test](tests/test_repository_installation.scenario.l1.py))
- Given Claude Code install records for catalog plugins in the invocation checkout and in other checkouts on the machine, when persistent installation runs, then each record receives one native plugin update at its scope from its project path, the run issues no install or enable for a plugin the invocation checkout records, and the report lists every refreshed record. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a project-scope record in the invocation checkout and a local-scope record in a second checkout, both installed through the real Claude Code CLI into one disposable agent state, when the persistent recipe runs from the invocation checkout, then the native update executes for both records at their own scope from their own project path, the listing still reports both records, and neither checkout's activation entries change. ([test](tests/test_repository_installation.scenario.l3.py))
- Given a disposable `CODEX_HOME` that isolated installation populated and authentication from the explicitly selected mode, when a fresh non-interactive Codex session in that home is asked for its available subagent names as structured output, then the returned subagent name set contains every canonical subagent name whose definition the installation placed under that home's `agents/` directory. ([test](tests/test_repository_installation.scenario.l3.py))

### Mappings

- Every target/profile pair in `outcomeeng.distribution.profiles.AGENT_PROFILES`
  maps to one native-profile probe row whose immutable identifier, complete native
  configuration, disposable state root, and artifact paths derive from that
  registry entry. ([test](tests/test_native_profile_execution.mapping.l1.py))
- Each isolated verification selection — the complete committed catalogs and a generated valid subset containing `spec-tree` — maps to registration of the invocation checkout and exactly that selection reported as installed and enabled by the corresponding real agent CLI. ([test](tests/test_repository_installation.mapping.l3.py))
- For each supported agent, an explicitly selected valid isolated subset maps to a plan containing exactly its members in catalog order. ([test](tests/test_repository_installation.mapping.l1.py))
- Every Claude Code install record in a listing maps to exactly one native plugin update at its own scope from its own project path when its plugin is cataloged, its scope is project or local, its project path is an existing directory, and its project declares no noncanonical marketplace source in readable settings, read in Claude Code's own precedence order with the local document over the project document, and otherwise to one warning naming the record and why it is left unchanged, with no command for it; an entry from another marketplace maps to nothing. ([test](tests/test_repository_installation.mapping.l1.py))
- Each marketplace, plugin, and lifecycle operation a repository-installation plan performs maps to a failure report naming that operation and its agent, with the attempted commands ending at that operation and no later operation performed. ([test](tests/test_repository_installation.mapping.l1.py))

### Compliance

- ALWAYS: discovery selects subscription by default locally, requires an explicit authentication mode in CI, and requires the selected mode's credential without falling back to another mode. ([test](tests/test_repository_installation.compliance.l1.py))
- ALWAYS: subscription discovery checks native file-store write-through compatibility before linking only the selected saved-login file into disposable state, then serializes participating uses and reports detected file, link, or account replacement without restoring an older copy. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: subscription discovery implements OAuth refresh, migrates a credential store, or invokes login or logout against a home linked to the saved login; native refresh persists through the file link and cleanup leaves its target intact. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: discovery exposes initial or refreshed credentials in arguments, child credential variables, returned captures, or exceptions; API and workspace-token login receive their respective credential only through stdin in disposable state. ([test](tests/test_repository_installation.compliance.l1.py))
- ALWAYS: for every native-profile probe row, the producer materializes the
  native definition, retains configuration/loading/result artifacts, removes
  ambient model and effort overrides, passes only the selected harness
  credential, and invokes its native-child command exactly once; a failed row
  records its terminal condition without a retry, credential fallback, profile
  substitution, or alternate launch. ([test](tests/test_native_profile_execution.compliance.l1.py))
- ALWAYS: release acceptance is established independently for each supported
  harness and retains configuration, native loading, and one minimal isolated
  execution result for all three of that harness's profiles declared in
  `spx/15-subagent-execution.pdr.md`. Evidence for one harness establishes no
  execution claim for another; a combined acceptance claim requires complete
  evidence for every harness it names. Each row derives
  its complete configuration from the central profile owner, uses disposable
  state, and makes one native subagent invocation. The retained artifacts
  distinguish definition loading, parent-session configuration, and the child
  invocation result. For Codex, the retained result includes one native
  parent-filtered app-server listing of active and archived spawned children,
  complete pagination, and one read of the sole child from disposable state.
  The read carries the configured role, recorded model and effort, and
  completion; recorded configuration is not per-turn execution telemetry. An independent Auditor judges the actual artifacts and result.
  A missing credential, failed load, or unusable launch is reported
  without retry, credential fallback, profile substitution, or another launch
  mechanism ([audit]).
- ALWAYS: persistent installation places each refreshed selected plugin's generated Codex agent definitions in the selected `CODEX_HOME/agents/` directory beside the skill content they invoke, leaving definitions outside the marketplace's recorded ownership unchanged ([test](tests/test_repository_installation.compliance.l1.py))
- ALWAYS: marketplace reconciliation leaves exactly one current marketplace-owned definition for each authored Codex agent of a refreshed selected plugin, preserves pending plugins' prior owned definitions, and removes unchanged owned definitions for agents removed from refreshed plugins or plugins outside the catalog-bounded home selection ([test](tests/test_repository_installation.compliance.l1.py))
- ALWAYS: a scope split — plugin-owned agent definitions in a checkout whose invoked skill content lives in the selected agent home — stops installation before mutation, reports every mismatched definition, and directs removal of byte-identical plugin copies while identifying changed or unrecognized copies as collisions for inspection ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: isolated installation reads or mutates persistent marketplace registration, plugin caches, or agent definitions; subscription discovery may read and natively refresh only the selected saved-login file. ([test](tests/test_repository_installation.compliance.l3.py))
- ALWAYS: reconciliation adopts a present destination whose bytes equal the plugin's current shipped definition but which no ownership entry records, so a run interrupted before its ownership-record write completes cleanly when re-run. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: a persistent plan reinstalls a plugin the invocation checkout already records — a reinstall moves no Claude Code install record, so refresh of a recorded plugin is the native update alone, and a native update failing outside the pending-publication wording stops the run. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: the fresh-session subagent-discovery probe continues without its credential or stores a captured stream carrying the credential substring — absence raises a loud error before any agent process runs, and capture-time scrubbing replaces every occurrence in stored streams and messages. ([test](tests/test_repository_installation.compliance.l1.py))
