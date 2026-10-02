# Agent Terminology

**Agent harness.** The repository-managed behavior around coding agents, including agent configuration, instruction files, plugin marketplaces, plugins, skills, invocation policy, and isolated execution state.

**Agent.** A selectable coding agent, such as Codex or Claude Code.

**Agent adapter.** The configured way the agent harness launches, resumes, observes, or communicates with one agent.

**Agent session.** One running or resumable interaction for one agent.

**Subagent.** An agent session spawned by another agent session to perform delegated work.

**Subagent definition.** The named configuration that declares how a subagent is invoked and instructed. Installation places definitions; discovery reports the subagent names available for invocation; spawning creates agent sessions.

**Prohibited terminology.**

Authored terminology, including implementation identifiers, docstrings, and operator-visible strings, names the specific concept. The following words and phrases are prohibited for the meanings listed; the replacement follows the subject being described.

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

**Change, Output, and Activity.** The chapter `versions/4.0/methodology/change/changes.md` of `outcomeeng/methodology` is the home of what a Change, an Output, and an Activity are; the roles below use those terms as that chapter defines them and hold whether or not a repository declares a coordination overlay.

**Role.** What an agent session does for a Change; a session holds a role for that Change and may hold another in a different one. A role name is capitalized, so it stands apart from the everyday word. One round is one Author or Fixer pass together with every Verifier pass it triggers.

A Role does not identify a subagent definition. A configured Verifier names a subagent definition serving the Verifier Role; its task is the assigned verification work. When Author and Fixer are called through a subagent definition, the same definition serves both Roles.

**Refiner.** The role of the Change's holder during refinement. The agent session in conversation with the operator holds it, realized by loading into that conversation the refinement skills the Change's Maturity routes to; the role is never dispatched as a subagent and never loaded from an agent definition.

**Executor.** The role of the Change's holder during execution. The Executor sequences the Change's Activities, delegates production and verification, integrates the changeset, and escalates a reopened product or architecture judgment to the operator. The Executor produces no artifact.

**Author.** The role held by the agent session that produces the artifacts of one round: decisions, specs, verification artifacts, or implementation.

**Fixer.** The Author role in a later round on the same subject.

When an agent calls both the Author and the Fixer, they must use separate agent sessions.

When the operator calls the Author, the same session must also act as the Fixer whenever the operator requests, for as many rounds as necessary.

**Verifier.** The role held by the agent session that produces an agentic verdict: an Auditor for audit, a Reviewer for review.

**Position.** Standing authority the operator grants an agent session over a scope, lasting across Changes, where a role is held within one Change. The operator grants each position as a durable record naming the product, the position, and the worktree root where the position runs. One session holds one position, in one worktree root; a session no grant names holds no position and works in roles only.

A position title is a capitalized word naming a kind of position in every product, such as Director, Maintainer, or Orchestrator. A position name identifies one granted position and takes the form `{Product} {Position}`, the product followed by the position title, such as `Plugins Maintainer` or `Methodology Director`; the operator stands outside that form. Text that states what a position carries in every product uses the bare title; text that identifies or addresses one granted position, its holder, or its grant uses the position name. Position titles and position names stay distinct from role names, so a position never implies that its holder does one thing only.

The set of positions is open. The operator holds product judgment and attests each Frame. The **Director** coordinates across products and confirms Slices under the operator's delegation; the operator remains the accountable person for every Slice the Director confirms. A **Maintainer** refines its product's Changes and, on the Director's order, launches Executors only for a product without an Orchestrator. The **Orchestrator** launches the Executor for each Change the Maintainer hands it at Executable, on the Director's order, and runs Executors to delivery. A grant may name any further position, which holds the authority its grant names.

A position holder may take any role except the Verifier, such as the Author, or the Fixer of a round another session authored. Each role it takes keeps every rule that role carries; the position neither widens nor relaxes any of them, and it never acts as a Verifier. The generated router of every repository states the positions content, so every consumer repository carries it.

## Rationale

The terms agent harness, agent, agent adapter, and agent session stay separate so configuration, connection mechanics, and interaction identity do not collapse into one term. Subagent definitions and spawned subagents also stay distinct: discovering an installed configuration proves its availability for invocation, while execution requires a spawned agent session. The prohibited-terminology table makes each ambiguous term's replacement explicit.

The five roles name what a session does for a Change independently of which harness, agent, or adapter runs it. Separate sessions reduce attachment to earlier choices when an agent calls both production and repair; operator-requested repair preserves the operator's control over repeated rounds in the same session.

Positions name who holds standing authority across Changes, so the operator addresses a session by what it does in which product rather than by an identity a mail store or harness assigns. Keeping position names apart from role names lets one holder take several roles in turn without either vocabulary absorbing the other, and barring a position holder from the Verifier role keeps every agentic verdict free of the authority that directs the work it judges.

The Refiner is the operator's conversation because refinement is an interview. Field names in the SPX CLI's verification payloads — `producer`, `expectedProducer`, `recordedByRunDriver`, the run driver — are schema vocabulary for run provenance, and lowercase pattern words such as orchestrator or applier describe a shape of dispatch; neither is a role name, and the capitalized Orchestrator names a position.

## Product properties

1. Agent-facing decisions, specs, skills, and instructions use agent harness, agent, agent adapter, agent session, subagent, and subagent definition for their defined meanings; product domains identify which concept they govern and preserve those distinctions in configuration, invocation, observation, and resume behavior.
2. Agent-facing decisions, specs, skills, and instructions name who refines, executes, produces, repairs, or verifies a Change with the capitalized Role names Refiner, Executor, Author, Fixer, and Verifier, with Auditor and Reviewer as the two Verifier kinds; the Refiner is held by the operator's conversation. They name standing authority across Changes as a position the operator grants: a capitalized position title, such as Director, Maintainer, or Orchestrator, for what a position carries in every product, and a position name of the form `{Product} {Position}` for one granted position, both distinct from every role name, each granted position held by one session in one worktree root.
3. Author and Fixer session selection follows who calls them: an agent calling both uses separate sessions; an operator calling the Author can require that same session to perform any number of repair rounds. A position holder may take any role except the Verifier, and every rule of a role it takes holds unchanged.

## Verification

- ALWAYS: decisions, specs, skills, and instructions that describe standing authority over a scope across Changes name it as a position the operator grants
- ALWAYS: text that identifies or addresses one granted position, its holder, or its grant names it by its position name of the form `{Product} {Position}`, such as `Plugins Maintainer`, and text that states what a position carries in every product names it by its bare capitalized position title, such as Director, Maintainer, or Orchestrator
- NEVER: a position title or position name stands in for a role name, or a role name for a position title or position name
- ALWAYS: one agent session holds at most one position, in the one worktree root its grant names, and a session no grant names holds no position and works in roles only
- NEVER: a position widens or relaxes any rule of a role its holder takes, including the separate-session rule for an Author and a Fixer an agent calls
- NEVER: a position holder acts as a Verifier
- ALWAYS: the generated router of every repository states the operator's authority, the Director, Maintainer, and Orchestrator position titles with the authority each holds, and that a grant may name any further position, which holds the authority its grant names

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
