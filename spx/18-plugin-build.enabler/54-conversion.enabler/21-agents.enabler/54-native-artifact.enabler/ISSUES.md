# Issues

## Generated Codex verifiers lack a command-scoped persistence boundary

Classification: tracked repository-wide verifier debt. The current Change preserves the established generated-verifier shape and records this class for its own decision, specification, implementation, and installation lifecycle.

Evidence: `instructions:audit-subagent` rejected `src/plugins/spec-tree/agents/change-auditor.md` with this finding:

> Current: the `Bash` grant renders the Codex definition without a `sandbox_mode`; its generated instructions state that source tool allowlists are manual-review guidance (dist/codex/spec-tree/skills/spec-tree-plugin/agents/spec-tree_change-auditor.toml:5,60-64). Should be: an enforceable native capability boundary that permits only the owning audit workflow's required operations. Why it matters: prompt-level prohibitions cannot prevent arbitrary shell mutation, agent-CLI invocation, or nested-verifier dispatch in the emitted Codex role. Fix: provide an enforceable command-scoped capability boundary for the required audit persistence operations and withhold unrestricted shell access.

The same class covers `src/plugins/instructions/agents/skill-auditor.md` and `src/plugins/instructions/agents/subagent-auditor.md`. Both grant the `spx verification run` verbs their audit journal requires and declare no Codex `sandbox_mode`, because `read-only` blocks that journal's writes. Their generated definitions, `dist/codex/instructions/skills/instructions-plugin/agents/instructions_skill-auditor.toml` and `dist/codex/instructions/skills/instructions-plugin/agents/instructions_subagent-auditor.toml`, carry the Bash allowlist only as manual-review guidance. The CI changeset review of PR 620, comment `issuecomment-5974636968`, raised this instance at severity `DEBT`.

Evidence, `workspace-write` trials: each ran Codex CLI 0.162.1 with a disposable `CODEX_HOME`, a parent `codex exec --sandbox workspace-write -c approval_policy="never"` session in a linked worktree of this repository, and the shipped `spec-tree_pdr-auditor` definition, which declares `sandbox_mode = "workspace-write"`, auditing [`spx/15-audit-result-delivery.pdr.md`](spx/15-audit-result-delivery.pdr.md).

- Without a writable root, `spx verification run start` failed before run creation with `verification context write failed: EPERM: operation not permitted, open '/Users/shz/Code/outcomeeng/plugins/.spx/branch/detached-e7efe094b467-e7dc94d4/verification-context/contexts/context-fcafd703ed46183ccf7dde74c7748484bbe5f9347ca8a5fe7d8544e94a3bb736.json'`. The run store lies under the main checkout's `.spx/branch/`, outside the auditor's worktree.
- A `[sandbox_workspace_write]` table with `writable_roots` in the agent definition passed agent-file validation, which rejects unknown keys, and did not reach the child. Child session `01a14ab3-b6e2-7641-abea-fd1211866009` recorded a `workspace-write` policy with no writable roots, and run start failed with `EPERM` again. The trial edited a renamed copy of the definition, because an edited `spec-tree_pdr-auditor.toml` stops session start with a digest-mismatch collision.
- A Codex profile cannot carry the table: `--strict-config` refused it with `` unknown configuration field `profiles.trial-writable.sandbox_workspace_write` ``.
- A top-level `[sandbox_workspace_write]` table in the selected `CODEX_HOME`'s `config.toml`, with `writable_roots = ["/Users/shz/Code/outcomeeng/plugins/.spx/branch/detached-e7efe094b467-e7dc94d4"]`, reached the child. Child session `01a14ab7-fc03-7730-8025-3f0b81afeffb` recorded that root; `start`, six `scope add` calls, and `finish` exited 0; and run `2026-10-17_16-43-39-193-2bbd0b1cfb33` sealed `approved` with no findings. `finding add` did not run, because the audit raised no finding.
- The home-level table applies to every agent session that uses that `CODEX_HOME`, the parent session included, not to verifiers alone.
- The root that worked names one run-store key, and the key's name carries the checkout's head-commit prefix. How SPX derives the key for a checkout on a branch is untraced. The parent `.spx/branch/` holds every checkout's key, and those keys hold only verification data: `audit`, `review`, `verification-context`, `auditing`, and probe scratch. The `.spx/` above it also holds sessions, worktree claims, and reviews. Which root a configuration names — one key, `.spx/branch/`, or another — is open.

Impact: every generated Codex verifier whose governing workflow requires shell-backed persistence can execute arbitrary shell operations within its native sandbox. Agent instructions express a narrower role without enforcing command-level authority. An agent definition alone cannot give a verifier `workspace-write` persistence. The change-auditor's isolated Codex trial failed before run creation with `EPERM` while SPX opened `/Users/shz/Code/outcomeeng/plugins/.spx/branch/detached-7355b50081ab-2cd93af5/verification-context/contexts/context-457a5e208e7d815430e50fb3d0897f09d99c7c76eddf836161f4900e23a4dcda.json`, because the shared run store is outside the selected product worktree, and the trials above admit those writes only through a home-level writable root that widens every session of that home. The strongest agent-TOML-only setting that preserves required persistence is therefore `sandbox_mode = "danger-full-access"` with `approval_policy = "never"`; command containment still requires the settlement below.

Settlement condition: select and deliver either an owned companion rules artifact with complete generation, installation, ownership, collision, upgrade, and cleanup semantics, or a dedicated persistence tool available only to configured verifiers. Apply the selected mechanism to every generated Codex verifier and prove both required SPX persistence and rejection of mutation outside the boundary.

Further instance: `instructions:subagent-auditor` finding `f-001` (rule `capabilities/material-restriction-prompt-only`, severity `REJECT`) on `src/plugins/spec-tree/agents/change-auditor.md` line 6, in the subagent audit of head `73c02c3602897fcb5598b3122996e30b65d34537`: `tools: Bash(python3:*), Read, {{! tool('use_skill') !}}` grants `Bash(python3:*)`, which admits every `python3` command rather than the bundled runner alone, emitted as `tools: Bash(python3:*), Read, Skill` in `dist/claude/spec-tree/agents/change-auditor.md` and as manual-review guidance only in `dist/codex/spec-tree/skills/spec-tree-plugin/agents/spec-tree_change-auditor.toml`, so the wrapper's no-file rule and its runner-only command boundary exist only as prompt text; Change [outcomeeng/changes#162](https://github.com/outcomeeng/changes/issues/162) leaves this grant unchanged.

Proposed Change: `.spx/worktree/change-drafts/d000b94a-99d8-4527-82f4-64fea4fd477d.md` (`d000b94a-99d8-4527-82f4-64fea4fd477d`).

## DEBT [source-ownership]: scenario source vocabulary at line 45

Defect class: `source-ownership`.

Finding: `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-native-artifact.enabler/tests/test_native_artifact.scenario.l1.py:45` verifies the assertion “Given a plugin agent file with `name`, `description`, a profile selection, `skills`, and `tools` frontmatter, when agent conversion runs, then it emits a Codex custom-agent TOML file with `name`, `description`, the complete native configuration of the selected profile, source body, `skills.config` enablement plus skill guidance, target-supported web-search configuration, and developer-instruction guidance carrying the source tool allowlist.”

Evidence: the test hand-writes conversion-field vocabulary such as `name`, `description`, `profile`, `skills`, `tools`, `web_search`, `shell_environment_policy`, and `developer_instructions`; several have no imported production contract, so the assertion owns source vocabulary instead of consuming it.

Successor: [outcomeeng/changes#85](https://github.com/outcomeeng/changes/issues/85).

Revisit and settlement condition: Change #85 establishes production-owned conversion vocabulary and source-payload contracts, migrates every affected native-artifact test and imported harness use, and passes the applicable test-evidence audit.

## DEBT [source-ownership]: operational-setting vocabulary at line 91

Defect class: `source-ownership`.

Finding: `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-native-artifact.enabler/tests/test_native_artifact.scenario.l1.py:91` verifies the assertion “Given a plugin agent file selecting a central profile and declaring sandbox, nickname candidates, and MCP server configuration, when agent conversion runs, then it emits the selected profile's complete native model and reasoning configuration while preserving those independent operational settings, source body, and `skills.config` enablement plus skill guidance.”

Evidence: the test copies conversion-owned TOML and frontmatter keys including `sandbox_mode`, `nickname_candidates`, `mcp_servers`, `docs`, `command`, `args`, and `developer_instructions` into predicates rather than importing an owning source contract.

Successor: [outcomeeng/changes#85](https://github.com/outcomeeng/changes/issues/85).

Revisit and settlement condition: Change #85 establishes production-owned conversion vocabulary and source-payload contracts, migrates every affected native-artifact test and imported harness use, and passes the applicable test-evidence audit.

## DEBT [source-ownership]: mapping vocabulary at line 44

Defect class: `source-ownership`.

Finding: `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-native-artifact.enabler/tests/test_native_artifact.mapping.l1.py:44` verifies the assertion “Source agents with `skills` entries map to Codex `skills.include_instructions = true`; their entries map in source order to enabled `skills.config` entries and developer-instruction guidance that states enablement is not a spawn-time preload guarantee.”

Evidence: the mapping predicate indexes `converted.values` with a test-local `skills` key; the converter has no exported contract for that field, leaving conversion vocabulary owned by the assertion file.

Successor: [outcomeeng/changes#85](https://github.com/outcomeeng/changes/issues/85).

Revisit and settlement condition: Change #85 establishes production-owned conversion vocabulary and source-payload contracts, migrates every affected native-artifact test and imported harness use, and passes the applicable test-evidence audit.

## DEBT [source-ownership]: harness-owned source payload at line 177 `outcomeeng_testing/harnesses/agent_conversion.py`, `source_agent`, `source-ownership`

Defect class: `source-ownership`.

Finding: `outcomeeng_testing/harnesses/agent_conversion.py:177` supplies source payload to the assertion “Every central profile maps directly to its complete Codex-native configuration; an absent selection maps to Standard, with no model-alias or effort translation.”

Evidence: `source_agent()` supplies hand-authored source path, name, description, and body payload defaults to the profile mapping test; a harness cannot own arbitrary source-agent request data, and the mapping has no provenance-bearing source fixture or contract for them.

Successor: [outcomeeng/changes#85](https://github.com/outcomeeng/changes/issues/85).

Revisit and settlement condition: Change #85 establishes production-owned conversion vocabulary and source-payload contracts, migrates every affected native-artifact test and imported harness use, and passes the applicable test-evidence audit.

## DEBT [evidence]: approval-policy positive conversion path

Defect class: `evidence`.

Finding: the generally available `approval_policy` converter field has no positive scenario or mapping evidence.

Evidence: `outcomeeng/distribution/agents.py:259` reads and emits `approval_policy`, while the hosted review at [PR #583](https://github.com/outcomeeng/plugins/pull/583#issuecomment-5730664407) found no positive scenario or mapping that exercises this conversion path.

Impact: a supported positive conversion path remains uncovered, so deterministic verification does not establish that an authored `approval_policy` reaches the generated native artifact correctly.

Successor: [outcomeeng/changes#85](https://github.com/outcomeeng/changes/issues/85).

Revisit and settlement condition: Change #85 adds a positive scenario or mapping for `approval_policy`, records passing deterministic evidence for that path, and passes the applicable evidence audit.

## DEBT [evidence]: scenario test hand-writes conversion vocabulary (f-001)

Finding f-001 (REJECT, source ownership) at
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-native-artifact.enabler/tests/test_native_artifact.scenario.l1.py:45`:
the test hand-writes conversion vocabulary as string literals (`"name"`,
`"description"`, `"profile"`, `"skills"`, `"tools"`, `"web_search"`,
`"sandbox_mode"`, `"shell_environment_policy"`, `"set"`,
`"developer_instructions"`) while `outcomeeng/distribution/agents.py` exports
`AGENT_NAME_FIELD`, `AGENT_DESCRIPTION_FIELD`, `AGENT_TOOLS_FIELD`, and
`SANDBOX_MODE_FIELD`, and `outcomeeng/distribution/profiles.py` exports
`PROFILE_FIELD`. The remaining keys have no exported contract.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run
token; the same holds for f-002 through f-005 below.

**Resolution shape**: export the missing field constants from
`outcomeeng/distribution/agents.py` and import them, with the existing exports,
in the test.

**Evidence that the text lies outside the change.** `git diff -U0
origin/main...HEAD` reports no hunk in the cited tests,
`outcomeeng_testing/harnesses/agent_conversion.py`, or
`outcomeeng/distribution/agents.py`, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset only adds symbols to
`outcomeeng/distribution/profiles.py` (model prices and usage token classes);
no symbol the cited tests import (`PROFILE_FIELD`, the `agents.py` field
constants, the profile resolution) is renamed or altered. It also narrows the
configuration guard in `outcomeeng/validation/profile_configuration.py`, which
agent conversion does not call.

**Settlement condition**: every conversion key the test uses is imported from
the production owner, and no string literal for a conversion-owned key remains
in the test.

## DEBT [evidence]: operational-setting predicates copy conversion-owned keys (f-002)

Finding f-002 (REJECT, source ownership) at
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-native-artifact.enabler/tests/test_native_artifact.scenario.l1.py:91`:
the predicates copy conversion-owned keys as literals (`"sandbox_mode"`,
`"nickname_candidates"`, `"mcp_servers"`, `"docs"`, `"command"`, `"args"`,
`"developer_instructions"`, `"profile"`).

The audit is the verdict named under f-001, at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`.

**Resolution shape**: as f-001; export the missing field constants from
`outcomeeng/distribution/agents.py` and import them.

**Evidence that the text lies outside the change.** `git diff -U0
origin/main...HEAD` reports no hunk in the cited tests,
`outcomeeng_testing/harnesses/agent_conversion.py`, or
`outcomeeng/distribution/agents.py`, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset only adds symbols to
`outcomeeng/distribution/profiles.py` (model prices and usage token classes);
no symbol the cited tests import is renamed or altered. It also narrows the
configuration guard in `outcomeeng/validation/profile_configuration.py`, which
agent conversion does not call.

**Settlement condition**: the predicates at line 91 reference imported
constants only.

## DEBT [evidence]: mapping test indexes a test-local skills key (f-003)

Finding f-003 (REJECT, source ownership) at
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-native-artifact.enabler/tests/test_native_artifact.mapping.l1.py:44`:
the test indexes `converted.values["skills"]` with a test-local key.

The audit is the verdict named under f-001, at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`.

**Resolution shape**: add an exported constant for the key next to
`AGENT_SKILL_INCLUDE_INSTRUCTIONS_FIELD` in `outcomeeng/distribution/agents.py`
and import it in the test.

**Evidence that the text lies outside the change.** `git diff -U0
origin/main...HEAD` reports no hunk in the cited tests,
`outcomeeng_testing/harnesses/agent_conversion.py`, or
`outcomeeng/distribution/agents.py`, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset only adds symbols to
`outcomeeng/distribution/profiles.py` (model prices and usage token classes);
no symbol the cited tests import is renamed or altered. It also narrows the
configuration guard in `outcomeeng/validation/profile_configuration.py`, which
agent conversion does not call.

**Settlement condition**: the test reads the `skills` values through an
exported constant.

## DEBT [evidence]: harness supplies hand-authored source-agent defaults (f-004) `outcomeeng_testing/harnesses/agent_conversion.py`, `source_agent`, `evidence`

Finding f-004 (REJECT) at
`outcomeeng_testing/harnesses/agent_conversion.py:177`: `source_agent()`
supplies hand-authored defaults for source path, name, description, and body;
no whole-payload fixture or source contract gives them provenance.

The audit is the verdict named under f-001, at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`.

**Resolution shape**: replace the defaults with a whole-payload fixture or a
production source contract that carries their provenance.

**Evidence that the text lies outside the change.** `git diff -U0
origin/main...HEAD` reports no hunk in the cited tests,
`outcomeeng_testing/harnesses/agent_conversion.py`, or
`outcomeeng/distribution/agents.py`, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset only adds symbols to
`outcomeeng/distribution/profiles.py` (model prices and usage token classes);
no symbol the cited harness or tests import is renamed or altered. It also
narrows the configuration guard in
`outcomeeng/validation/profile_configuration.py`, which agent conversion does
not call.

**Settlement condition**: every default `source_agent()` supplies traces to a
fixture or contract that owns it.

## DEBT [evidence]: harness declares expected outputs (f-005, WARNING)

Finding f-005 (WARNING) in
`outcomeeng_testing/harnesses/agent_conversion.py`: the harness declares
`EXPECTED_PERMISSION_MODE_CORRESPONDENCE` and `EXPECTED_TOOL_CLASSIFICATION`,
expected outputs a harness must not own. No test in this node runs them; the
sibling execution-policy node is judged on them.

The audit is the verdict named under f-001, at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`.

**Resolution shape**: move the expected outputs into the tests that assert
them, or derive them from an independent oracle the tests own.

**Evidence that the text lies outside the change.** `git diff -U0
origin/main...HEAD` reports no hunk in the cited tests,
`outcomeeng_testing/harnesses/agent_conversion.py`, or
`outcomeeng/distribution/agents.py`, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset only adds symbols to
`outcomeeng/distribution/profiles.py` (model prices and usage token classes);
no symbol the cited harness or tests import is renamed or altered. It also
narrows the configuration guard in
`outcomeeng/validation/profile_configuration.py`, which agent conversion does
not call.

**Settlement condition**: the harness declares no expected output, and the
tests that judge those correspondences own them.
