# Agent Terminology

**Agent harness.** The repository-managed behavior around coding agents, including agent configuration, instruction files, plugin marketplaces, plugins, skills, invocation policy, and isolated execution state.

**Agent.** A selectable coding agent, such as Codex or Claude Code.

**Agent adapter.** The configured way the agent harness launches, resumes, observes, or communicates with one agent.

**Agent session.** One running or resumable interaction for one agent.

**Output.** What a Change is meant to produce: a decision, spec, or evidence evolution, a lower-layer reconciliation, or both.

**Change.** The methodology's mutable coordination object for one intended Output. A repository's coordination overlay realizes it where one is declared; the roles below hold whether or not that overlay is present.

**Activity.** One entry in a Change's mutable, ordered execution plan.

**Role.** What an agent session does for a Change; a session holds a role for that Change and may hold another in a different one. A role name is capitalized, so it stands apart from the everyday word. One round is one Author or Fixer pass together with every Verifier pass it triggers.

**Refiner.** The role of the Change's holder during refinement. The agent session in conversation with the operator holds it, realized by loading the refinement skill into that conversation; the role is never dispatched as a subagent and never loaded from an agent definition.

**Executor.** The role of the Change's holder during execution. The Executor sequences the Change's Activities, delegates production and verification, integrates the changeset, and escalates a reopened product or architecture judgment to the operator. The Executor produces no artifact.

**Author.** The role held by the agent session that produces the artifacts of one round: decisions, specs, verification artifacts, or implementation.

**Fixer.** The Author role in a later round on the same subject, held by an agent session independent of the round's Author. The Executor hands the Fixer the earlier round's artifacts and verdicts.

**Verifier.** The role held by the agent session that produces an Agentic verdict: an Auditor for audit, a Reviewer for review.

## Rationale

The terms agent harness, agent, agent adapter, and agent session stay separate so configuration, connection mechanics, and interaction identity do not collapse into one term.

The five roles name what a session does for a Change independently of which harness, agent, or adapter runs it, so one agent session can hold different roles in different Changes and a role can move between sessions without renaming either. The Refiner is the operator's conversation because refinement is an interview; a subagent cannot interview the operator. The Fixer is a separate role because an Author receiving a rejected verdict tends to relocate the defect instead of removing it, and a fresh session holding the artifacts and the verdicts judges the repair from the standard rather than from the choices that produced the subject. Field names in the SPX CLI's verification payloads — `producer`, `expectedProducer`, `recordedByRunDriver`, the run driver — are schema vocabulary for run provenance, and pattern words such as orchestrator or applier describe a shape of dispatch; neither is a role name.

## Product properties

1. Agent-facing decisions, specs, skills, and instructions use agent harness, agent, agent adapter, and agent session for their defined roles.
2. Agent configuration, invocation, observation, and resume behavior preserve the distinction between those four roles.
3. Product domains that configure, launch, resume, isolate, equip, or observe coding agents identify the specific role they govern.
4. Agent-facing decisions, specs, skills, and instructions name who refines, executes, produces, repairs, or verifies a Change with the capitalized role names Refiner, Executor, Author, Fixer, and Verifier, with Auditor and Reviewer as the two Verifier kinds.
5. The Refiner role is held by the operator's conversation, and the Fixer role is never held by the round's own Author.

## Verification

### Audit

- ALWAYS: decisions, specs, skills, and instructions that govern Codex, Claude Code, agent selection, agent configuration, agent adapters, agent sessions, plugin bootstrap, skill bootstrap, isolated agent execution, or agent observation identify whether they describe the agent harness, an agent, an agent adapter, or an agent session ([audit])
- ALWAYS: each product domain whose behavior configures, launches, resumes, isolates, equips, or observes coding agents states in its governing spec or decision whether it governs the agent harness, an agent, an agent adapter, or an agent session ([audit])
- NEVER: use unqualified agent for adapter implementation, session identity, plugin package, marketplace package, or the repository-managed agent harness when that specific role is meant ([audit])
- ALWAYS: decisions, specs, skills, and instructions that describe who refines, executes, produces, repairs, or verifies a Change name the role — Refiner, Executor, Author, Fixer, or Verifier, with Auditor and Reviewer as the Verifier kinds — capitalized ([audit])
- ALWAYS: the Refiner role is held by the agent session in conversation with the operator, realized by loading the refinement skill into that conversation, never by dispatching a subagent or loading an agent definition ([audit])
- NEVER: the agent session holding the Author role revises its own subject in a later round — the Fixer role is held by an agent session independent of the round's Author ([audit])
- NEVER: an SPX payload field name — `producer`, `expectedProducer`, `recordedByRunDriver`, the run driver — or a dispatch-pattern word such as orchestrator or applier stands in for a role name ([audit])
