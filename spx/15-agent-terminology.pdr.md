# Agent Terminology

DEFINES agent harness AS the repository-managed behavior around coding agents, including agent configuration, instruction files, plugin marketplaces, plugins, skills, invocation policy, and isolated execution state
DEFINES agent AS a selectable coding agent, such as Codex or Claude Code
DEFINES agent adapter AS the configured way the agent harness launches, resumes, observes, or communicates with one agent
DEFINES agent session AS one running or resumable interaction for one agent
DEFINES subagent AS an agent session spawned by another agent session to perform delegated work
DEFINES subagent definition AS the named configuration that declares how a subagent is invoked and instructed; installation places definitions, discovery reports the subagent names available for invocation, and spawning creates agent sessions
DEFINES Change, Output, Leaf, and Parent AS the terms `versions/4.0/methodology/change-graph/change-graph.md` of `outcomeeng/methodology` defines, holding whether or not a repository declares its Change Store in `spx/local/changes.md`
DEFINES Role AS what an agent session does for a Change; a session holds a Role for that Change and may hold another in a different one, and a Role name is capitalized
DEFINES round AS one Author or Fixer pass together with every Verifier pass it triggers
DEFINES Refiner AS the Role of the Change's holder during refinement
DEFINES Applier AS the Role of the Change's holder during Application, which takes a Leaf's Declarations subsections in Application order, delegates production and verification, integrates the Changeset, and escalates a reopened product or architecture judgment to the operator
DEFINES mechanical repair AS a fix of a finding that changes no behavior or decision: a path or link, a typo, a wording the finding states, or a renamed identifier, never decision-record text
DEFINES Author AS the Role of the agent session that produces the artifacts of one round: decisions, specs, verification artifacts, or implementation
DEFINES Fixer AS the Author Role in a later round on the same subject
DEFINES Verifier AS the Role of the agent session that produces an agentic verdict: an Auditor for audit, a Reviewer for review
DEFINES Position AS authority over a scope that its holder keeps across Changes, as `versions/4.0/methodology/orchestration/orchestration.md` of `outcomeeng/methodology` defines it
DEFINES overseer AS the holder of the Position of the next higher rank present, which monitors, orders, and stops the Positions it oversees, as `versions/4.0/methodology/orchestration/orchestration.md` of `outcomeeng/methodology` states
DEFINES Chain of Positions AS the ranks a question passes up, each to the next higher rank that holds its context, in the rank order of `versions/4.0/methodology/orchestration/orchestration.md` of `outcomeeng/methodology`

GOVERNS the names agent-facing decisions, specs, skills, and instructions give coding agents, their sessions, and the Roles and Positions that act on Changes
SO THAT product engineers and agent sessions reading them
CAN RELY ON one name per concept, each meaning what this decision and the methodology chapters it cites define

## Verification

### Audit: mechanical repair

- applier-mechanical-only: ALWAYS: the Applier produces no artifact other than a mechanical repair, which fixes a finding, changes no behavior or decision, and never covers decision-record text; the Applier makes it directly with no Fixer round, and every other repair goes to a Fixer
- repair-no-round: ALWAYS: a mechanical repair is no round, and the Applier that makes it holds neither the Author nor the Fixer Role

### Audit: agent concepts

- harness-concept-named: ALWAYS: decisions, specs, skills, and instructions that govern Codex, Claude Code, agent selection, agent configuration, agent adapters, agent sessions, plugin bootstrap, skill bootstrap, isolated agent execution, or agent observation identify whether they describe the agent harness, an agent, an agent adapter, or an agent session
- domain-states-concept: ALWAYS: each product domain whose behavior configures, launches, resumes, isolates, equips, or observes coding agents states in its governing spec or decision whether it governs the agent harness, an agent, an agent adapter, or an agent session, and keeps that concept distinct in configuration, invocation, observation, and resume behavior
- no-unqualified-agent: NEVER: use unqualified agent for adapter implementation, session identity, plugin package, marketplace package, or the repository-managed agent harness when that specific concept is meant
- discovery-not-execution: NEVER: conflate discovery of a subagent definition with execution of an agent session
- external-spelling: ALWAYS: exact external API fields, command names, filesystem paths, and attributed quotations keep their required spelling, while the surrounding text uses this decision's vocabulary, and an external identifier establishes no synonym in product terminology
- runtime-execution: ALWAYS: `runtime` names execution-time behavior or an execution environment such as Python only where no agent concept is meant

### Audit: prohibited terminology

- prohibited-by-meaning: ALWAYS: authored terminology, including implementation identifiers, docstrings, and operator-visible strings, takes the required wording below for each prohibited meaning, chosen from the subject's meaning
- runtime-agent: NEVER: `runtime` or `coding-agent runtime` names Codex, Claude Code, or another selectable coding agent; the name is agent
- runtime-harness: NEVER: `runtime` or `runtime environment` names repository-managed configuration, invocation policy, or isolated state; the name is agent harness
- runtime-adapter: NEVER: `runtime adapter` names the mechanism for launching or communicating with an agent; the name is agent adapter
- runtime-session: NEVER: `runtime` or `runtime instance` names one running or resumable interaction; the name is agent session
- per-runtime: NEVER: `per-runtime` or `runtime-specific` names variation by selected coding agent; the names are per-agent and agent-specific
- role-definition: NEVER: `role`, `agent role`, or `custom role` names a named installed configuration available for delegated invocation; the name is subagent definition, and subagent name for its invocation identifier
- role-registry: NEVER: `role discovery` or `role registry` names the available subagent names or the registry that exposes them; the names are subagent discovery and subagent registry
- role-session: NEVER: `role` names a spawned interaction performing delegated work; the name is subagent or agent session, as the subject requires

### Audit: Roles and Positions

- role-names: ALWAYS: decisions, specs, skills, and instructions that describe who refines, applies, produces, repairs, or verifies a Change name the Role — Refiner, Applier, Author, Fixer, or Verifier, with Auditor and Reviewer as the Verifier kinds — capitalized
- role-not-subagent: NEVER: a Role identifies a subagent definition; a configured Verifier names a subagent definition serving the Verifier Role, and when Author and Fixer are called through a subagent definition, the same definition serves both Roles
- refiner-conversation: ALWAYS: the Refiner Role is held by the agent session in conversation with the operator, realized by loading into that conversation the refinement skills the Change's Maturity routes to, never by dispatching a subagent or loading an agent definition
- separate-sessions: ALWAYS: the Author and the Fixer use separate agent sessions, whoever calls them
- no-fixer-definition: NEVER: introduce a separate Fixer subagent definition solely to represent the Fixer Role
- no-payload-role: NEVER: an SPX payload field name — `producer`, `expectedProducer`, `recordedByRunDriver`, the run driver — or a dispatch-pattern word such as orchestrator stands in for a Role name
- position-term: ALWAYS: decisions, specs, skills, and instructions call authority over a scope that its holder keeps across Changes a Position, the holder of the next higher rank present that monitors, orders, and stops it its overseer, and the route a question takes to the next higher rank that holds its context the Chain of Positions, and never use Position for a Role
- no-principal: NEVER: decisions, specs, skills, and instructions name a principal for an overseer or for the rank a question passes to up the Chain of Positions
