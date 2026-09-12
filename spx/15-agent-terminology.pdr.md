# Agent Terminology

**Agent harness.** The repository-managed behavior around coding agents, including agent configuration, instruction files, plugin marketplaces, plugins, skills, invocation policy, and isolated execution state.

**Agent.** A selectable coding agent, such as Codex or Claude Code.

**Agent adapter.** The configured way the agent harness launches, resumes, observes, or communicates with one agent.

**Agent session.** One running or resumable interaction for one agent.

**Subagent.** An agent session spawned by another agent session to perform delegated work.

**Subagent definition.** The named configuration that declares how a subagent is invoked and instructed. Installation places definitions; discovery reports the subagent names available for invocation; spawning creates agent sessions.

**Prohibited terminology.**

Authored terminology names the specific concept. The following words and phrases are prohibited for the meanings listed; the replacement follows the subject being described.

**Role** retains its methodology-defined meaning: what an agent session does for a Change. The prohibition concerns using role as a synonym for a subagent, its definition, or its invocation name. It does not prohibit assigning a Role to an agent session.

| Prohibited wording                  | Intended meaning                                                       | Required wording                                                                           |
| ----------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `runtime`, `coding-agent runtime`   | Codex, Claude Code, or another selectable coding agent                 | **agent**                                                                                  |
| `runtime`, `runtime environment`    | Repository-managed configuration, invocation policy, or isolated state | **agent harness**                                                                          |
| `runtime adapter`                   | The mechanism for launching or communicating with an agent             | **agent adapter**                                                                          |
| `runtime`, `runtime instance`       | One running or resumable interaction                                   | **agent session**                                                                          |
| `per-runtime`, `runtime-specific`   | Variation by selected coding agent                                     | **per-agent**, **agent-specific**                                                          |
| `role`, `agent role`, `custom role` | A named installed configuration available for delegated invocation     | **subagent definition**; use **subagent name** when referring to its invocation identifier |
| `role discovery`, `role registry`   | Available subagent names or the registry that exposes them             | **subagent discovery**, **subagent registry**                                              |
| `role`                              | A spawned interaction performing delegated work                        | **subagent** or **agent session**, according to the subject                                |

Exact external API fields, command names, filesystem paths, and attributed quotations preserve their required spelling. Surrounding explanations use the vocabulary above; an external identifier does not establish a synonym in product terminology.

`runtime` remains valid for execution-time behavior or an execution environment such as Python when no agent concept is meant.

**Output.** What a Change is meant to produce: a decision, spec, or evidence evolution, a lower-layer reconciliation, or both.

**Change.** The methodology's mutable coordination object for one intended Output. A repository's coordination overlay realizes it where one is declared; the roles below hold whether or not that overlay is present.

**Activity.** One entry in a Change's mutable, ordered execution plan.

**Role.** What an agent session does for a Change; a session holds a role for that Change and may hold another in a different one. A role name is capitalized, so it stands apart from the everyday word. One round is one Author or Fixer pass together with every Verifier pass it triggers.

A Role does not identify a subagent definition. When Author and Fixer are called through a subagent definition, the same definition serves both Roles.

**Refiner.** The role of the Change's holder during refinement. The agent session in conversation with the operator holds it, realized by loading into that conversation the refinement skills the Change's Maturity routes to; the role is never dispatched as a subagent and never loaded from an agent definition.

**Executor.** The role of the Change's holder during execution. The Executor sequences the Change's Activities, delegates production and verification, integrates the changeset, and escalates a reopened product or architecture judgment to the operator. The Executor produces no artifact.

**Author.** The role held by the agent session that produces the artifacts of one round: decisions, specs, verification artifacts, or implementation.

**Fixer.** The Author role in a later round on the same subject.

When an agent calls both the Author and the Fixer, they must use separate agent sessions.

When the operator calls the Author, the same session must also act as the Fixer whenever the operator requests, for as many rounds as necessary.

**Verifier.** The role held by the agent session that produces an agentic verdict: an Auditor for audit, a Reviewer for review.

## Rationale

The terms agent harness, agent, agent adapter, and agent session stay separate so configuration, connection mechanics, and interaction identity do not collapse into one term. Subagent definitions and spawned subagents also stay distinct: discovering an installed configuration proves its availability for invocation, while execution requires a spawned agent session. The prohibited-terminology table makes each ambiguous term's replacement explicit.

The five roles name what a session does for a Change independently of which harness, agent, or adapter runs it. Separate sessions reduce attachment to earlier choices when an agent calls both production and repair; operator-requested repair preserves the operator's control over repeated rounds in the same session.

The Refiner is the operator's conversation because refinement is an interview. Field names in the SPX CLI's verification payloads — `producer`, `expectedProducer`, `recordedByRunDriver`, the run driver — are schema vocabulary for run provenance, and pattern words such as orchestrator or applier describe a shape of dispatch; neither is a role name.

## Product properties

1. Agent-facing decisions, specs, skills, and instructions use agent harness, agent, agent adapter, agent session, subagent, and subagent definition for their defined meanings; product domains identify which concept they govern and preserve those distinctions in configuration, invocation, observation, and resume behavior.
2. Agent-facing decisions, specs, skills, and instructions name who refines, executes, produces, repairs, or verifies a Change with the capitalized Role names Refiner, Executor, Author, Fixer, and Verifier, with Auditor and Reviewer as the two Verifier kinds; the Refiner is held by the operator's conversation.
3. Author and Fixer session selection follows who calls them: an agent calling both uses separate sessions; an operator calling the Author can require that same session to perform any number of repair rounds.

## Verification

### Audit

- ALWAYS: decisions, specs, skills, and instructions that govern Codex, Claude Code, agent selection, agent configuration, agent adapters, agent sessions, plugin bootstrap, skill bootstrap, isolated agent execution, or agent observation identify whether they describe the agent harness, an agent, an agent adapter, or an agent session ([audit])
- ALWAYS: each product domain whose behavior configures, launches, resumes, isolates, equips, or observes coding agents states in its governing spec or decision whether it governs the agent harness, an agent, an agent adapter, or an agent session ([audit])
- NEVER: use unqualified agent for adapter implementation, session identity, plugin package, marketplace package, or the repository-managed agent harness when that specific concept is meant ([audit])
- ALWAYS: authored agent terminology follows the prohibited-terminology table, choosing the replacement from the subject's meaning and preserving exact external identifiers and attributed quotations only where their spelling is required ([audit])
- NEVER: conflate discovery of a subagent definition with execution of an agent session ([audit])
- NEVER: introduce a separate Fixer subagent definition solely to represent the Fixer Role ([audit])
- ALWAYS: decisions, specs, skills, and instructions that describe who refines, executes, produces, repairs, or verifies a Change name the role — Refiner, Executor, Author, Fixer, or Verifier, with Auditor and Reviewer as the Verifier kinds — capitalized ([audit])
- ALWAYS: the Refiner role is held by the agent session in conversation with the operator, realized by loading into that conversation the refinement skills the Change's Maturity routes to, never by dispatching a subagent or loading an agent definition ([audit])
- ALWAYS: when an agent calls both the Author and the Fixer, they use separate agent sessions ([audit])
- ALWAYS: when the operator calls the Author, the same session also acts as the Fixer whenever the operator requests, for as many rounds as necessary ([audit])
- NEVER: an SPX payload field name — `producer`, `expectedProducer`, `recordedByRunDriver`, the run driver — or a dispatch-pattern word such as orchestrator or applier stands in for a role name ([audit])
