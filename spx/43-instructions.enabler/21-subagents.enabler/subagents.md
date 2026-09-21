# Subagents

PROVIDES the meta-skills that create, standardize, and audit subagent configurations
SO THAT plugin authors
CAN produce configured agents that load and return reliable verdicts in every agent harness the marketplace targets

The subagents-about-subagents cluster is three peers with distinct roles:

- `/create-subagent` routes subagent creation and editing.
- `/subagent-standards` owns the canonical rules — configuration fields, tool grants, model selection, context isolation, and the invocation contract. Loaded by the other two.
- `/audit-subagent` evaluates one subagent configuration against `/subagent-standards` and `/agent-prompt-standards`, producing structured verdicts without modifying files.

## Assertions

### Compliance

- ALWAYS: subagent configuration guidance specifies a target path or scope as the
  complete task prompt and delegates context discovery to the owning skill while
  preserving its output contract, per `spx/15-subagent-execution.pdr.md`; guidance
  judges native sandbox and approval fields against the governing context's
  execution-boundary declaration before applying the harness contract ([audit]).
- ALWAYS: `/subagent-standards` admits a definition that inherits the invoking
  session's execution policy when its governing context declares that inheritance
  with linked evidence: an assertion in the owning node's spec, or a decision on
  the path from the root that reaches the node by index. The auditor resolves the
  owning node through the tree as the node whose linked test or audit assertion
  names the definition, names which declaration it read, and judges its presence;
  an absent native sandbox field does not invalidate declared inheritance ([audit]).
- NEVER: `/subagent-standards` accepts a citation inside a definition's frontmatter
  or body as the inheritance declaration, or admits undeclared inheritance on the
  auditor's judgment that the definition needs the invoking policy ([audit]).
- ALWAYS: `/subagent-standards` accepts retained per-harness, per-profile release
  acceptance as invocation evidence when the owning node's spec or a decision on
  the path from the root that reaches it by index declares that acceptance:
  native loading and one minimal isolated execution for every declared profile,
  as `spx/15-subagent-execution.pdr.md` requires. Every other definition retains
  its exact-definition minimal isolated invocation. The auditor names the
  declaration and acceptance artifact it read ([audit]).
- ALWAYS: subagent invocation guidance requires plugin authorization and an active
  skill's explicit call request, uses the native tool schema, and requires analysis
  and reporting of a failed launch or unusable result without retry or substitution ([audit]).
- ALWAYS: configuration guidance selects one central Standard, Strong, or Fast
  profile declared in `spx/15-subagent-execution.pdr.md` and obtains the complete
  native configuration together; Standard is the default, Strong and Fast
  require explicit governing selection, and independent model or reasoning
  overrides and product-defined profiles are forbidden ([audit]).
- ALWAYS: `/subagent-standards` owns every rule `/audit-subagent` enforces — standards and enforcement stay in one place so drift cannot open between them ([audit])
- ALWAYS: `/create-subagent` and `/audit-subagent` load `/subagent-standards` before doing any authoring or evaluation work — prevents memory-based assessment ([audit])
- ALWAYS: `/audit-subagent` judges exactly one subagent configuration per invocation, and auditing several configurations dispatches one invocation per configuration ([audit])
- ALWAYS: `/create-subagent` writes a configuration to the invocation checkout by default, and reaches a user-scope destination outside it — creating, editing, or deleting — only after operator confirmation naming the absolute destination, one approval covering one write ([audit])
- NEVER: `/create-subagent` widens an approved checkout-scope write to user scope on its own judgment that the configured agent suits other projects — that destination applies to every project on the machine and no repository reviews it ([audit])
- NEVER: restate `/subagent-standards` or `/agent-prompt-standards` rules inside `/create-subagent` or `/audit-subagent` — a single source of truth prevents drift between standard and enforcer ([audit])
