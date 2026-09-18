# Issues

## Generated Codex verifiers lack a command-scoped persistence boundary

Classification: tracked repository-wide verifier debt. The current Change preserves the established generated-verifier shape and records this class for its own decision, specification, implementation, and installation lifecycle.

Evidence: `instructions:audit-subagent` rejected `src/plugins/spec-tree/agents/change-auditor.md` with this finding:

> Current: the `Bash` grant renders the Codex definition without a `sandbox_mode`; its generated instructions state that source tool allowlists are manual-review guidance (dist/codex/spec-tree/skills/spec-tree-plugin/agents/spec-tree_change-auditor.toml:5,60-64). Should be: an enforceable native capability boundary that permits only the owning audit workflow's required operations. Why it matters: prompt-level prohibitions cannot prevent arbitrary shell mutation, agent-CLI invocation, or nested-verifier dispatch in the emitted Codex role. Fix: provide an enforceable command-scoped capability boundary for the required audit persistence operations and withhold unrestricted shell access.

Impact: every generated Codex verifier whose governing workflow requires shell-backed persistence can execute arbitrary shell operations within its native sandbox. Agent instructions express a narrower role without enforcing command-level authority. The change-auditor cannot use `workspace-write` as a partial mitigation: its isolated Codex trial failed before run creation with `EPERM` while SPX opened `/Users/shz/Code/outcomeeng/plugins/.spx/branch/detached-7355b50081ab-2cd93af5/verification-context/contexts/context-457a5e208e7d815430e50fb3d0897f09d99c7c76eddf836161f4900e23a4dcda.json`, because the shared run store is outside the selected product worktree. The strongest agent-TOML-only setting that preserves required persistence is therefore `sandbox_mode = "danger-full-access"` with `approval_policy = "never"`; command containment still requires the settlement below.

Settlement condition: select and deliver either an owned companion rules artifact with complete generation, installation, ownership, collision, upgrade, and cleanup semantics, or a dedicated persistence tool available only to configured verifiers. Apply the selected mechanism to every generated Codex verifier and prove both required SPX persistence and rejection of mutation outside the boundary.

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

## DEBT [source-ownership]: harness-owned source payload at line 177

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
