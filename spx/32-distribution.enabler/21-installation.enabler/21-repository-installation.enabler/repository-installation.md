---
id: 01a1e064-65a9-7237-b11b-c83f47ce914b
---

# Repository Installation

PROVIDES `just install-marketplace` for persistent installation and `just verify-marketplace-installation` for isolated end-to-end proof
SO THAT marketplace maintainers and the merge lifecycle
CAN refresh exactly the selected plugins in every Claude Code checkout on the machine and the selected Codex home while preserving activation, and verify installation behavior with disposable state and native saved-login refresh for subscription discovery

## Assertions

### Test.Scenario: native probe process

- [undecodable-output](tests/test_native_profile_process.scenario.l1.py):
  - Given a native probe command whose parent emits a byte sequence that is invalid UTF-8 and exits while a descendant keeps the captured output stream open
  - When the runner collects the result
  - Then it returns the parent's completed result promptly, replaces undecodable bytes, and terminates the descendant before returning
- [probe-timeout](tests/test_native_profile_process.scenario.l1.py):
  - Given a native probe command whose parent and descendant remain running
  - When the execution timeout expires
  - Then the runner reports the timeout promptly and terminates the descendant before returning

### Test.Scenario: isolated installation

- [absent-plugin-terminal](tests/test_repository_installation.scenario.l1.py):
  - Given a selected plugin absent from the registered checkout marketplace
  - When isolated installation runs
  - Then the absence is terminal at that plugin's install
- [generated-subset-invalid](tests/test_repository_installation.scenario.l1.py):
  - Given a generated subset omitting `product-tree`
  - When isolated installation plans that selection
  - Then it reports the invalid subset before an agent CLI mutates state
- [isolated-rerun](tests/test_repository_installation.scenario.l3.py):
  - Given unchanged committed catalogs and checkout content
  - When isolated installation runs twice against the same disposable homes
  - Then the first run places every shipped Codex agent definition in the disposable home's agent directory beside the skills it invokes
  - And the second run succeeds with the same installed and home-placed state
- [codex-subagent-discovery](tests/test_repository_installation.scenario.l3.py):
  - Given a disposable `CODEX_HOME` that isolated installation populated, and authentication from the explicitly selected mode
  - When a fresh non-interactive Codex session in that home is asked for its available subagent names as structured output
  - Then the returned subagent name set contains every canonical subagent name whose definition the installation placed under that home's `agents/` directory
- [verify-recipe-scope](tests/test_repository_installation.scenario.l1.py):
  - Given `just verify-marketplace-installation`
  - When the recipe runs
  - Then it passes the repository-installation node's tests directory to the repository test command, so pytest discovers every evidence file other than the L3 tests [`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-l3-tests.pdr.md`](spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-l3-tests.pdr.md) declares
  - And it runs none of the node's `l3` files

### Test.Scenario: persistent selection

- persistent-bootstrap:
  - Given an invocation checkout with no install record of a cataloged plugin at project or local scope
  - When bootstrap runs
  - Then only `product-tree` is installed at project scope, declared project activation is preserved, and absent activation defaults to disabled with a warning
  - And a checkout recording a plugin at either scope is refreshed through that record's native update and receives no install or enable
- product-override-activation:
  - Given a trusted product enabling a home-disabled plugin
  - When that product loads
  - Then the plugin's skills are active for that product
  - And a product that supplies no override retains disabled activation, and a home-wide refresh preserves both products' configuration and the home's activation
- missing-cache-resume:
  - Given configured home plugins whose marketplace snapshot or plugin cache is absent, with the marketplace revision changed or unchanged
  - When refresh runs or resumes after interruption
  - Then all selected published plugins become available with the same activation and no additional selection
- unexpected-write-retained:
  - Given an unexpected selection or activation write during persistent execution
  - When verification detects it
  - Then the run reports failure and retains the changed state for diagnosis, without restoring an earlier settings snapshot or issuing compensating activation commands
- [empty-codex-home](tests/test_repository_installation.scenario.l3.py):
  - Given an empty selected Codex home
  - When persistent installation runs
  - Then only `product-tree` is registered and cached, its home activation is explicitly disabled, and the run warns that the operator can select additional plugins
- [invalid-selection](tests/test_repository_installation.scenario.l1.py):
  - Given a nonempty selected subset that omits both `product-tree` and `spec-tree`
  - When persistent installation starts
  - Then it reports the invalid selection and performs no state-changing operation
- [spec-tree-replaced](tests/test_repository_installation.scenario.l1.py):
  - Given a persistent inventory that holds `spec-tree` and not `product-tree`
  - When persistent installation plans and runs
  - Then the plan installs `product-tree` and uninstalls `spec-tree` at the record's scope and activation
  - And after the run no record holds `spec-tree`
- [inspection-failure](tests/test_repository_installation.scenario.l1.py):
  - Given a persistent marketplace inspection that fails
  - When persistent installation runs
  - Then it reports a failure naming that operation and attempts no plan operation
- [register-missing-source](tests/test_repository_installation.scenario.l1.py):
  - Given a checkout declaring a marketplace source, and an agent home whose registry carries no entry under the catalog's name
  - When persistent installation plans
  - Then the plan registers that source for that agent instead of refreshing it

### Test.Scenario: persistent refresh planning

- [listing-defects](tests/test_repository_installation.scenario.l1.py):
  - Given a Claude Code listing entry at project scope that names no project path, and one that reports no version
  - When persistent installation plans
  - Then it reports each listing defect, continues with every other record, and exits nonzero
- [unreadable-settings](tests/test_repository_installation.scenario.l1.py):
  - Given an invocation checkout whose own Claude Code settings cannot be read
  - When persistent installation runs
  - Then bootstrap for that checkout stops with the settings path reported, while the native update of every record that checkout already holds and the rewrite of every other checkout's record still run, and a run against registered agents whose invocation checkout records the plugin exits zero
  - And an agent whose registry carries no entry under the catalog's name has its registration withheld and issues no operation naming the marketplace it never registered, including a closing listing that names it and the native update of the invocation checkout's own records, while a closing listing over the machine's own records still runs and every record of that agent stays at its listed version
  - And neither state announces a first install, and the report names as that agent's installed plugins only the ones it reached
- [unregistered-registry](tests/test_repository_installation.scenario.l1.py):
  - Given a Claude Code registry carrying no entry under the catalog's name, one install record of the invocation checkout, and one of another checkout
  - When persistent installation runs
  - Then the report names no target, names the moved record with the version it held and the version it holds afterwards, and names the other checkout's record as unrefreshed at its listed version, and the run exits nonzero
- [entry-without-location](tests/test_repository_installation.scenario.l1.py):
  - Given a registry entry under the catalog's name that names no install location
  - When persistent installation plans
  - Then planning stops with that entry's source named and issues no command, because the run has nowhere to read the target's head from
- [head-unresolved](tests/test_repository_installation.scenario.l1.py):
  - Given a registered marketplace location the head read resolves no commit from, one install record of the invocation checkout, and one of another checkout
  - When persistent installation runs
  - Then the run completes past that read, the report names no target, every carried record is reported against no target, the other checkout's record stays at its listed version, and the run exits nonzero
- [unversioned-manifest](tests/test_repository_installation.scenario.l1.py):
  - Given a registered clone whose manifest for one cataloged plugin carries no version, and a listing whose only record of that plugin belongs to the invocation checkout beside a record of a plugin the clone does resolve
  - When persistent installation runs
  - Then the report names the unresolved record and no target version for its plugin, leaves it out of the off-target records the comparison could reach, moves the resolved plugin's record to the target, and the run exits nonzero

### Test.Scenario: persistent record refresh

- [records-across-checkouts](tests/test_repository_installation.scenario.l1.py):
  - Given Claude Code install records for catalog plugins in the invocation checkout and in other checkouts on the machine
  - When persistent installation runs
  - Then each invocation-checkout record receives one native plugin update at its scope with the invocation checkout as working directory, and every other record is rewritten in the install-record file to the target
  - And the run issues no install or enable for a plugin the invocation checkout records, no command names another checkout, and the report lists every record with its version before and after
- [real-cli-two-records](tests/test_repository_installation.scenario.l3.py):
  - Given a project-scope record in the invocation checkout and a local-scope record in a second checkout, both installed through the real Claude Code CLI into one disposable agent state
  - When the persistent recipe runs from the invocation checkout
  - Then the listing reports both records at the target, no command ran with the second checkout as working directory, and neither checkout's activation entries change
- [uncached-other-records](tests/test_repository_installation.scenario.l1.py):
  - Given Claude Code install records of a cataloged plugin only in checkouts other than the invocation checkout, and a target version the plugin cache lacks
  - When persistent installation runs
  - Then it issues one native project-scope install of that plugin with a run-owned temporary project as working directory, rewrites every such record to the target, drops the temporary project's record before the closing listing, leaves the invocation checkout's settings unchanged, and exits zero
- [real-cli-uncached](tests/test_repository_installation.scenario.l3.py):
  - Given a real Claude Code install-record file whose only record of a cataloged plugin belongs to another checkout, and a plugin cache without that plugin's target version
  - When the persistent recipe runs
  - Then `claude plugin list --json` reports that record at the target and lists no record of the temporary project, and the run exits zero with the invocation checkout's settings unchanged
- [differing-versions](tests/test_repository_installation.scenario.l3.py):
  - Given Claude Code install records for one cataloged plugin at differing recorded versions across checkouts on the machine
  - When the persistent recipe runs
  - Then every project- or local-scope record of that plugin in the closing listing lists the target version, and the report names each record's version before and after
- [already-current](tests/test_repository_installation.scenario.l3.py):
  - Given a Claude Code install record whose native update reports the record already current
  - When the persistent recipe runs
  - Then the record holds that version, the run continues, and the report names it refreshed at an unchanged version
- [concurrent-record](tests/test_repository_installation.scenario.l1.py):
  - Given a project- or local-scope install record of a cataloged plugin that another agent session writes after the run reads its listing
  - When the run's post-execution listing reports it
  - Then the run names that record's scope, project path, and version, issues no further update or rewrite, and exits nonzero when its version is not the target
- [missing-project-dir](tests/test_repository_installation.scenario.l1.py):
  - Given a project-scope record of a cataloged plugin whose project directory does not exist
  - When the persistent run executes
  - Then the closing listing shows it at the target, and no command named that directory
- [real-cli-gone-dir](tests/test_repository_installation.scenario.l3.py):
  - Given a real Claude Code install-record file holding a record whose directory is gone and a record at an older version
  - When the persistent recipe runs
  - Then `claude plugin list --json` reports both at the target, and the run exits zero

### Test.Property: selected refresh

- subset-preserves-activation: For each supported agent and every valid selected subset of its catalog-bounded selection, refreshing the subset preserves every pre-run activation entry, disabled plugins and explicitly enabled home plugins included, while it updates every selected published plugin through native refresh operations.

### Test.Mapping: [native-profile-rows](tests/test_native_profile_execution.mapping.l1.py)

Every target/profile pair in `outcomeeng.distribution.profiles.AGENT_PROFILES` maps to one native-profile probe row whose immutable identifier, complete native configuration, disposable state root, and artifact paths derive from that registry entry.

| Case            | Target      | Profile  | Probe row                                      |
| --------------- | ----------- | -------- | ---------------------------------------------- |
| claude-standard | Claude Code | Standard | one row derived from the pair's registry entry |
| claude-strong   | Claude Code | Strong   | one row derived from the pair's registry entry |
| claude-executor | Claude Code | Executor | one row derived from the pair's registry entry |
| claude-fast     | Claude Code | Fast     | one row derived from the pair's registry entry |
| codex-standard  | Codex       | Standard | one row derived from the pair's registry entry |
| codex-strong    | Codex       | Strong   | one row derived from the pair's registry entry |
| codex-executor  | Codex       | Executor | one row derived from the pair's registry entry |
| codex-fast      | Codex       | Fast     | one row derived from the pair's registry entry |

### Test.Mapping: [isolated-selection](tests/test_repository_installation.mapping.l3.py)

Each isolated verification selection maps to registration of the invocation checkout and exactly that selection reported as installed and enabled by the corresponding real agent CLI.

| Case              | Selection                                          | Result                                                                                      |
| ----------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| complete-catalogs | the complete committed catalogs                    | the invocation checkout registered, and exactly the catalogs' plugins installed and enabled |
| generated-subset  | a generated valid subset containing `product-tree` | the invocation checkout registered, and exactly the subset installed and enabled            |

### Test.Mapping: [isolated-subset-plan](tests/test_repository_installation.mapping.l1.py)

For each supported agent, an explicitly selected valid isolated subset maps to a plan containing exactly its members in catalog order.

| Case        | Agent       | Plan                                           |
| ----------- | ----------- | ---------------------------------------------- |
| claude-code | Claude Code | exactly the subset's members, in catalog order |
| codex       | Codex       | exactly the subset's members, in catalog order |

### Test.Mapping: [install-record-actions](tests/test_repository_installation.mapping.l1.py)

Every entry of a Claude Code install-record listing takes the action of the first row below whose record it matches, by its marketplace, checkout, scope, and plugin, and every project- or local-scope record of this marketplace takes, on top of that action, one report entry: for a record the run moved, an entry naming the version its opening listing entry carried and the version the closing listing carries, and for a record the run left unmoved, an unrefreshed entry naming its listed version.

| Case                 | Record                                                                                                                                                                                                         | Action                                                                                                                                                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| other-marketplace    | an entry of another marketplace                                                                                                                                                                                | none, and no report entry                                                                                                                                                                                               |
| invocation-cataloged | a record of this marketplace held by the invocation checkout, whose plugin is cataloged                                                                                                                        | exactly one native plugin update at its own scope, with the invocation checkout as working directory                                                                                                                    |
| invocation-renamed   | a project- or local-scope record of this marketplace held by the invocation checkout, whose plugin id the catalog's `renames` map retires to a cataloged successor the invocation checkout records at no scope | a native migration, with the invocation checkout as working directory: the successor's install at the record's scope, then a `plugin-uninstall` of the retired id at that scope; no rewrite of its install-record entry |
| other-cataloged      | a project- or local-scope record of this marketplace held by another checkout, whose plugin is cataloged, its project directory present or not                                                                 | exactly one rewrite of its install-record entry to the target                                                                                                                                                           |
| other-renamed        | a project- or local-scope record of this marketplace held by another checkout, whose plugin id the catalog's `renames` map retires to a cataloged successor, its project directory present or not              | exactly one rewrite of its install-record entry to the successor's entry at the target                                                                                                                                  |
| outside-catalog      | a record of this marketplace whose plugin is neither cataloged nor retired by the `renames` map to a cataloged successor                                                                                       | one warning naming the record and why it is left unchanged, with no command and no rewrite                                                                                                                              |
| otherwise            | any other record of this marketplace that no row above takes, such as a record of another checkout at a scope other than project or local                                                                      | one warning naming the record and why it is left unchanged, with no command and no rewrite                                                                                                                              |

### Test.Mapping: [uncached-fetch](tests/test_repository_installation.mapping.l1.py)

Each cataloged plugin maps to a fetch by whether an invocation-checkout record names it, whether another project- or local-scope record names it, and whether the plugin cache holds its target version.

| Case                | Plugin                                                                                                                          | Fetch                                                                                               |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| uncached-other-only | no invocation-checkout record names it, another project- or local-scope record names it, and the cache lacks its target version | exactly one native project-scope install, with the run-owned temporary project as working directory |
| any-other           | every other plugin                                                                                                              | no fetch                                                                                            |

### Test.Mapping: [operation-failures](tests/test_repository_installation.mapping.l1.py)

Each operation a repository-installation plan performs maps to one result when it fails.

| Case           | Failed operation                              | Result                                                                                                                                      |
| -------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| plan-operation | a marketplace, plugin, or lifecycle operation | a failure report naming that operation and its agent, with the attempted commands ending at that operation and no later operation performed |
| head-read      | the head read of the registered location      | a completed run carrying no target                                                                                                          |

### Test.Mapping: [registry-source](tests/test_repository_installation.mapping.l1.py)

Each registered marketplace entry shape maps to the source persistent refresh refreshes from and names in its report.

| Case       | Registered entry    | Source                                                                    |
| ---------- | ------------------- | ------------------------------------------------------------------------- |
| github     | a GitHub repository | that repository                                                           |
| git-url    | a git URL           | that URL                                                                  |
| local-path | a local path        | that path                                                                 |
| no-entry   | no entry            | the bootstrap registration from the invocation checkout's own declaration |

### Test.Mapping: [auditor-dispatch-rows](tests/test_native_auditor_dispatch.mapping.l1.py)

Every pair of an auditor the marketplace ships for dispatch and a supported harness maps to one auditor-dispatch row whose identifier, definition, and artifact paths derive from the shipped auditor definition, and the entrypoint's rows are exactly these four.

| Case                    | Auditor            | Harness     |
| ----------------------- | ------------------ | ----------- |
| skill-auditor-claude    | `skill-auditor`    | Claude Code |
| skill-auditor-codex     | `skill-auditor`    | Codex       |
| subagent-auditor-claude | `subagent-auditor` | Claude Code |
| subagent-auditor-codex  | `subagent-auditor` | Codex       |

### Test.Compliance: persistent selection and Codex placement

- persistent-selection: ALWAYS: persistent selection is the catalog-bounded Claude Code inventory recorded for the invocation checkout at project or local scope, or the catalog-bounded plugin keys in the selected Codex home's raw configuration, including disabled plugins and plugins with missing caches; product overrides never change that home-wide set.
- codex-definitions-global: ALWAYS: selected Codex plugins' subagent definitions remain globally registered under the selected home's digest-bound ownership record regardless of product skill activation; disabling a plugin in a product neither removes its home definitions nor generates a product registry.
- [rename-pruning](tests/test_repository_installation.compliance.l1.py): ALWAYS: a plugin's placement script, built from a catalog whose `renames` map retires one or more plugin ids to that plugin, prunes the definitions the ownership record attributes to each retired id while their digest still matches, retains a changed or linked definition of a retired id without blocking the placement of the plugin's own definitions, reports every retained definition as a `retained` line and a partial-migration status on each run, a check-only run after the placement included, with the home and the exit code unchanged by that status, and leaves a definition recorded for any other plugin untouched.
- [pending-publication](tests/test_repository_installation.compliance.l1.py): ALWAYS: a pending-publication result names a selected plugin whose absence from the registered source is established, preserves its prior owned definitions, and reports it separately from successfully refreshed plugins; other failures stop all later operations.
- [codex-placement](tests/test_repository_installation.compliance.l1.py): ALWAYS: persistent installation places each refreshed selected plugin's generated Codex agent definitions in the selected `CODEX_HOME/agents/` directory beside the skill content they invoke, leaving definitions outside the marketplace's recorded ownership unchanged.
- [one-owned-definition](tests/test_repository_installation.compliance.l1.py): ALWAYS: marketplace reconciliation leaves exactly one current marketplace-owned definition for each authored Codex agent of a refreshed selected plugin, preserves pending plugins' prior owned definitions, and removes unchanged owned definitions for agents removed from refreshed plugins or plugins outside the catalog-bounded home selection.
- [scope-split](tests/test_repository_installation.compliance.l1.py): ALWAYS: a scope split, plugin-owned agent definitions in a checkout whose invoked skill content lives in the selected agent home, stops installation before mutation, reports every mismatched definition, and directs removal of byte-identical plugin copies while identifying changed or unrecognized copies as collisions for inspection.
- [adopt-present-destination](tests/test_repository_installation.compliance.l1.py): ALWAYS: reconciliation adopts a present destination whose bytes equal the plugin's current shipped definition but which no ownership entry records, so a run interrupted before its ownership-record write completes cleanly when re-run.
- [no-false-first-install](tests/test_repository_installation.compliance.l1.py): NEVER: the run announces an agent's first install, or names that agent's installed plugins, from the empty inventory that proposed the bootstrap; the warning accompanies the bootstrap install the plan carries, and the named installed set is the plugins the plan carries an install or a native update for, less the pending ones, so an agent whose bootstrap unreadable invocation settings or a withheld registration suppresses announces nothing and is named as installing nothing.

### Test.Compliance: persistent record refresh

- [catalog-path-containment](tests/test_repository_installation.compliance.l1.py): NEVER: a catalog value moves a read or write outside the tree it names: a committed catalog plugin name that is not one path segment, empty, `.`, `..`, or carrying a path separator, is rejected when the catalog is read, before any path is built from it; every generated Codex agent definition the run reads resolves inside the checkout's generated Codex tree; and a plugin manifest whose registered-clone catalog source resolves outside the clone yields no target version.
- [machine-wide-refresh](tests/test_repository_installation.compliance.l1.py): ALWAYS: persistent Claude Code refresh reaches every project- or local-scope install record of a cataloged plugin on the machine so that every Claude Code session on the machine starts and reloads at the head of the registered marketplace source's default branch: the invocation checkout's own records receive the native update, and every other such record has its install-record entry rewritten to the target install path, version, and commit, its project directory present or not, a record of a plugin id the catalog renames having its entry replaced by the successor's entry at the same scope and project path in that rewrite, so no checkout on the machine keeps a record of the retired id; any other record outside the catalog or outside project and local scope is reported and left unchanged; no agent command runs with any checkout other than the invocation checkout as its working directory. A target version that no invocation-checkout record's native update fetches and the plugin cache lacks is fetched through one native project-scope install in a temporary project the run creates and removes, and the run drops that project's install record before the closing listing, so the rewrite points every other record at a tree the cache holds while the invocation checkout's settings stay unchanged; a record whose target version still has no cache directory after the fetch is reported as unrefreshable, its record untouched, and the run exits nonzero, and a failed fetch install stops the run. A cataloged plugin the registered clone resolves no target version for has every project- or local-scope record of it reported as unresolved and the run exits nonzero, the invocation checkout's own record included; that record has already received its native update, so the run reports it at the version the closing listing carries rather than as unchanged, and no target exists for the drift comparison to judge it against. The invocation checkout's own settings matter only to bootstrap: unreadable settings stop bootstrap and nothing else, so a checkout that already records the plugin is refreshed through its native update and unreadable settings alone leave the run's exit zero. A run that registers the marketplace itself has no target: it reports every other checkout's record as unrefreshed and exits nonzero, and the next run brings them to the target. A run whose registration is withheld reaches no target either and moves no record of that agent, the invocation checkout's own included: it reports each at its listed version and exits nonzero. The target's head is read by running git in the location the registry records, so a registered location that is no git working tree, a directory registration added from a plain directory, and any other failed head read resolve no head; that failure is reported rather than stopping the run, which then reaches no target, rewrites no record, reports every project- or local-scope record of a cataloged plugin it carries against no target, and exits nonzero.
- [no-reinstall](tests/test_repository_installation.compliance.l1.py): NEVER: a persistent plan reinstalls a plugin the invocation checkout already records; a reinstall moves no Claude Code install record, so refresh of a recorded plugin is the native update alone, and a native update failing outside the pending-publication wording stops the run.
- [two-listing-reads](tests/test_repository_installation.compliance.l1.py): ALWAYS: a persistent refresh run plans from exactly one install-record listing read at its start, reads the listing exactly once more after execution, and issues no retry against the agent's record store.
- [currency-from-listing](tests/test_repository_installation.compliance.l1.py): NEVER: the persistent recipe reports a record as current on the strength of an earlier run or of the marketplace cache; currency is established only from the listing the same run reads after execution.
- [head-read-failure](tests/test_repository_installation.compliance.l1.py): NEVER: a failed head read of the registered location stops the persistent run at that operation; the run performs every later operation, carries no target, plans no rewrite, and raises one blocking warning for every project- or local-scope record of a cataloged plugin it carries, the invocation checkout's own included.
- [no-zero-exit-off-target](tests/test_repository_installation.compliance.l1.py): NEVER: the persistent run exits zero while a project- or local-scope install record of a cataloged plugin in the closing listing lists a version other than the target.
- [invocation-cwd-only](tests/test_repository_installation.compliance.l1.py): NEVER: the persistent run executes an agent command whose working directory is a checkout other than the invocation checkout; the run-owned temporary project is no checkout.
- [temporary-project](tests/test_repository_installation.compliance.l1.py): ALWAYS: the uncached-target fetch runs in a temporary project the run creates outside every checkout and removes on every exit path, and the install-record replace drops every entry of that project before the closing listing read; a run that a later failed operation stops after a fetch drops those entries alone and rewrites no other record.

### Test.Compliance: install-record rewrite

- [atomic-rewrite](tests/test_repository_installation.compliance.l1.py): ALWAYS: the install-record file rewrite replaces the file atomically and preserves every entry and field it neither sets nor drops, including entries of other marketplaces.
- [rewrite-at-write-boundary](tests/test_repository_installation.compliance.l1.py): ALWAYS: the install-record file rewrite applies its planned entries to the document as that document stands at the write boundary: it reads the document once more immediately before the replace and applies the same planned set again when the store moved under its first read, so a record another agent session writes into the document between the writer's read and its replace survives the replacement with every field the plan does not set, while every planned entry still reaches the target; the writer holds no lock, waits for nothing, and reads the store no further.
- [renamed-id-entry](tests/test_repository_installation.compliance.l1.py): ALWAYS: a project- or local-scope record of a plugin id the catalog renames, held by a checkout other than the invocation checkout, leaves the install-record document as one entry of the successor plugin at the same scope and project path, pointing at the target install path, version, and commit, and the document keeps no entry of any retired id that maps to that successor; where a successor entry already held the address its own fields stand and the retired entries' fields are discarded, and otherwise the entry of the first retired id in the catalog's `renames` order supplies every field the refresh does not set.

### Test.Compliance: discovery and disposable homes

- [auth-mode-selection](tests/test_repository_installation.compliance.l1.py): ALWAYS: discovery selects subscription by default locally, requires an explicit authentication mode in CI, and requires the selected mode's credential without falling back to another mode.
- [write-through-check](tests/test_repository_installation.compliance.l1.py): ALWAYS: subscription discovery checks native file-store write-through compatibility before linking only the selected saved-login file into disposable state, then serializes participating uses and reports detected file, link, or account replacement without restoring an older copy.
- [personal-login-refused](tests/test_repository_installation.compliance.l1.py): NEVER: subscription discovery reads a saved login from an unset `CODEX_HOME`, from a `CODEX_HOME` that is `HOME` or `HOME/.codex` by filesystem identity, or from a saved login that is the personal one; it fails before any native command runs, so the personal Codex login never reaches a test run.
- [no-oauth-refresh](tests/test_repository_installation.compliance.l1.py): NEVER: subscription discovery implements OAuth refresh, migrates a credential store, or invokes login or logout against a home linked to the saved login; native refresh persists through the file link, and cleanup leaves its target intact.
- [no-credential-exposure](tests/test_repository_installation.compliance.l1.py): NEVER: discovery exposes initial or refreshed credentials in arguments, child credential variables, returned captures, or exceptions; API and workspace-token login receive their respective credential only through stdin in disposable state.
- [isolated-no-persistent](tests/test_repository_installation.compliance.l3.py): NEVER: isolated installation reads or mutates persistent marketplace registration, plugin caches, or agent definitions; subscription discovery may read and natively refresh only the selected saved-login file.
- [discovery-credential](tests/test_repository_installation.compliance.l1.py): NEVER: the fresh-session subagent-discovery probe continues without its credential or stores a captured stream carrying the credential substring; absence raises a loud error before any agent process runs, and capture-time scrubbing replaces every occurrence in stored streams and messages.
- [disposable-codex-config](tests/test_repository_installation.compliance.l1.py): ALWAYS: every disposable Codex home the harness provisions, the isolated installation's home, the subscription write-through preflight's temporary homes, and every other home a real-agent observation points `CODEX_HOME` at, holds a `config.toml` that declares no plugin before the first Codex command runs against it, on whatever Codex CLI the host installs; a Codex command the installed CLI refuses is reported with the refusal text the CLI printed, after credential scrubbing, never as another failure class, so the write-through preflight reports a refused login as that refusal rather than as a credential writer that cannot preserve the saved-login link.

### Test.Compliance: native acceptance harness

- [probe-row-producer](tests/test_native_profile_execution.compliance.l1.py): ALWAYS: for every native-profile probe row, the producer materializes the native definition, retains configuration, loading, and result artifacts, removes ambient model and effort overrides, passes only the selected harness credential, and invokes its native-child command exactly once; a failed row records its terminal condition without a retry, credential fallback, profile substitution, or alternate launch.
- [dispatch-only-trigger](tests/test_native_profile_acceptance_workflow.compliance.l1.py): NEVER: the native profile acceptance workflow declares a `pull_request`, `push`, or `schedule` trigger; `workflow_dispatch` is its only trigger, so a hosted run begins only when an operator with write access dispatches it.
- [hosted-recipes](tests/test_native_profile_acceptance_workflow.compliance.l1.py): ALWAYS: the native profile acceptance workflow runs `just verify-native-profile-execution` and `just verify-native-auditor-dispatch` on a hosted runner, gives each run exactly one Claude Code credential and the one Codex credential its explicit authentication mode selects, each through job environment from a repository secret and never through a run body, and uploads the artifact directory each recipe wrote.
- [pin-read](tests/test_native_profile_acceptance_workflow.compliance.l1.py): ALWAYS: the native profile acceptance workflow's step that reads the tool pins from the quality gate workflow, run against the committed quality gate workflow, yields exactly the value the quality gate job's environment declares for every pin the acceptance job's other steps consume and its own environment does not declare, and a quality gate workflow that formats a pin differently or omits one makes that step fail.
- [auditor-row-producer](tests/test_native_auditor_dispatch.compliance.l1.py): ALWAYS: for every auditor-dispatch row, the producer materializes the shipped auditor definition in a disposable state root, retains configuration, loading, and result artifacts, passes only the selected harness credential, and invokes its native dispatch exactly once; a failed row records its terminal condition without a retry, credential fallback, definition substitution, or alternate launch.
- [codex-probe-names](tests/test_native_acceptance_harness.compliance.l1.py): ALWAYS: every native-profile probe definition the native acceptance harness launches on Codex is named with only lowercase letters, digits, and underscores, and every auditor-dispatch row launches its shipped auditor by its unchanged native selector.
- [auditor-fixture-repository](tests/test_native_acceptance_harness.compliance.l1.py): ALWAYS: the auditor-dispatch harness supplies each row's fixture inside a git repository, so the dispatched auditor resolves the fixture's checkout.
- [unusable-row-fails](tests/test_native_acceptance_harness.compliance.l1.py): ALWAYS: the native acceptance harness records a profile row as failed when its result shows no child execution, and an auditor-dispatch row as failed when its result is a blocked diagnostic or carries no run token.

### Probe: release acceptance

- [native-profile-acceptance](probes/native-profile-acceptance/probe.md): The native profile acceptance workflow, dispatched once on a hosted runner, runs the twelve rows: the eight `<harness>-<profile>` rows, Claude Code and Codex each with the Standard, Strong, Executor, and Fast profiles, and the four auditor-dispatch rows, `skill-auditor` and `subagent-auditor` each on Claude Code and Codex. The protocol directory holds each row's configuration, loading, and result artifacts, the protocol links every artifact, and the Author's verdict names a row failed when its result artifact is unusable.
- [pinned-cli-options](probes/pinned-cli-options/probe.md): A hosted runner with the Claude Code and Codex releases `.github/workflows/check.yml` pins, and the native profile acceptance workflow dispatched once. Each of the twelve rows launches its parent session once. No parent session rejects a command-line option the harness passes, each of the eight profile rows retains one child execution, and each of the four auditor-dispatch rows retains a completed run with a run token. Covers `codex-probe-names`, `auditor-fixture-repository`, and `unusable-row-fails`.

### Audit: acceptance and record store

- harness-acceptance: Release acceptance is established independently for each supported harness and retains configuration, native loading, and one minimal isolated execution result for every profile of that harness [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) declares; evidence for one harness establishes no execution claim for another, and a combined acceptance claim requires complete evidence for every harness it names; each row derives its complete configuration from the central profile owner, uses disposable state, and makes one native subagent invocation; the retained artifacts distinguish definition loading, parent-session configuration, and the child invocation result; for Codex, the retained result includes one native parent-filtered app-server listing of active and archived spawned children, complete pagination, and one read of the sole child from disposable state, the read carrying the configured role, recorded model and effort, and completion, recorded configuration being no per-turn execution telemetry; an independent Auditor judges the actual artifacts and result; a missing credential, failed load, or unusable launch is reported without retry, credential fallback, profile substitution, or another launch mechanism.
- record-store-no-lock: A persistent refresh run takes no lock on the agent's record store and waits on none.
- override-list-stripped: The native-profile isolation filter strips every variable of the native-profile override list before the native child runs: `CLAUDE_CODE_EFFORT_LEVEL`, `CLAUDE_CODE_SUBAGENT_MODEL`, `ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, `ANTHROPIC_SMALL_FAST_MODEL`, and `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`, the variables that change the model or reasoning effort a profile's native configuration resolves to under [`spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/21-installation-architecture.adr.md`](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/21-installation-architecture.adr.md).
