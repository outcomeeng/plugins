# Agent Terminology

**Agent harness.** The repository-managed behavior around coding agents, including agent configuration, instruction files, plugin marketplaces, plugins, skills, invocation policy, and isolated execution state.

**Agent.** A selectable coding agent, such as Codex or Claude Code.

**Agent adapter.** The configured way the agent harness launches, resumes, observes, or communicates with one agent.

**Agent session.** One running or resumable interaction for one agent.

## Rationale

The terms agent harness, agent, agent adapter, and agent session stay separate so configuration, connection mechanics, and interaction identity do not collapse into one term.

## Product properties

1. Agent-facing decisions, specs, skills, and instructions use agent harness, agent, agent adapter, and agent session for their defined roles.
2. Agent configuration, invocation, observation, and resume behavior preserve the distinction between those four roles.
3. Product domains that configure, launch, resume, isolate, equip, or observe coding agents identify the specific role they govern.

## Verification

### Audit

- ALWAYS: decisions, specs, skills, and instructions that govern Codex, Claude Code, agent selection, agent configuration, agent adapters, agent sessions, plugin bootstrap, skill bootstrap, isolated agent execution, or agent observation identify whether they describe the agent harness, an agent, an agent adapter, or an agent session ([audit])
- ALWAYS: each product domain whose behavior configures, launches, resumes, isolates, equips, or observes coding agents states in its governing spec or decision whether it governs the agent harness, an agent, an agent adapter, or an agent session ([audit])
- NEVER: use unqualified agent for adapter implementation, session identity, plugin package, marketplace package, or the repository-managed agent harness when that specific role is meant ([audit])
