# Issues

## Generated Codex verifiers lack a command-scoped persistence boundary

Classification: tracked repository-wide verifier debt. The current Change preserves the established generated-verifier shape and records this class for its own decision, specification, implementation, and installation lifecycle.

Evidence: `instructions:audit-subagent` rejected `src/plugins/spec-tree/agents/change-auditor.md` with this finding:

> Current: the `Bash` grant renders the Codex definition without a `sandbox_mode`; its generated instructions state that source tool allowlists are manual-review guidance (dist/codex/spec-tree/skills/spec-tree-plugin/agents/spec-tree_change-auditor.toml:5,60-64). Should be: an enforceable native capability boundary that permits only the owning audit workflow's required operations. Why it matters: prompt-level prohibitions cannot prevent arbitrary shell mutation, agent-CLI invocation, or nested-verifier dispatch in the emitted Codex role. Fix: provide an enforceable command-scoped capability boundary for the required audit persistence operations and withhold unrestricted shell access.

Impact: every generated Codex verifier whose governing workflow requires shell-backed persistence can execute arbitrary shell operations within its native sandbox. Agent instructions express a narrower role without enforcing command-level authority. The change-auditor cannot use `workspace-write` as a partial mitigation: its isolated Codex trial failed before run creation with `EPERM` while SPX opened `/Users/shz/Code/outcomeeng/plugins/.spx/branch/detached-7355b50081ab-2cd93af5/verification-context/contexts/context-457a5e208e7d815430e50fb3d0897f09d99c7c76eddf836161f4900e23a4dcda.json`, because the shared run store is outside the selected product worktree. The strongest agent-TOML-only setting that preserves required persistence is therefore `sandbox_mode = "danger-full-access"` with `approval_policy = "never"`; command containment still requires the settlement below.

Settlement condition: select and deliver either an owned companion rules artifact with complete generation, installation, ownership, collision, upgrade, and cleanup semantics, or a dedicated persistence tool available only to configured verifiers. Apply the selected mechanism to every generated Codex verifier and prove both required SPX persistence and rejection of mutation outside the boundary.

Proposed Change: `.spx/worktree/change-drafts/d000b94a-99d8-4527-82f4-64fea4fd477d.md` (`d000b94a-99d8-4527-82f4-64fea4fd477d`).

## DEBT [evidence]: approval-policy positive conversion path

Defect class: `evidence`.

Finding: the generally available `approval_policy` converter field has no positive scenario or mapping evidence.

Evidence: `outcomeeng/distribution/agents.py:259` reads and emits `approval_policy`, while the hosted review at [PR #583](https://github.com/outcomeeng/plugins/pull/583#issuecomment-5730664407) found no positive scenario or mapping that exercises this conversion path.

Impact: a supported positive conversion path remains uncovered, so deterministic verification does not establish that an authored `approval_policy` reaches the generated native artifact correctly.

Successor: [outcomeeng/changes#85](https://github.com/outcomeeng/changes/issues/85).

Revisit and settlement condition: Change #85 adds a positive scenario or mapping for `approval_policy`, records passing deterministic evidence for that path, and passes the applicable evidence audit.
