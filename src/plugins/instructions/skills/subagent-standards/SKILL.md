---
name: subagent-standards
description: >-
  Configuration, configuration-subject, profile, capability, invocation, placement, and
  evidence standards for {{! term('configured_agents') !}}. Loaded by creator and auditor skills.
user-invocable: false
allowed-tools: Read, {{! tool('use_skill') !}}
---

{!% require_skill 'instructions:agent-prompt-standards' %!}

<objective>
One set of authoring rules for {{! term('configured_agents') !}} whose native configuration,
permissions, task boundary, and result are independently inspectable.
</objective>

<configuration>

- ALWAYS: name one focused role and describe the conditions under which its owning skill invokes it.
- ALWAYS: keep a wrapper thin when its behavior belongs to a skill: name that skill, invoke it,
  and relay its declared result contract without copying its workflow into the wrapper.
- ALWAYS: define the role, material constraints, workflow, and output expectations in the
  {{! term('configured_agent_prompt') !}}. Equivalent semantic tags satisfy the same
  requirement, so never read an absent tag as missing functionality when equivalent
  content exists.
- ALWAYS: use the voice, constraint-language, and anti-pattern rules from
  `/agent-prompt-standards`.
- ALWAYS: declare every field required by the current harness and reject unsupported configuration.
- ALWAYS: resolve a definition's governing context before judging its execution boundary
  or its evidence: the owning node is the node whose linked test or audit assertion names
  the definition — several matching nodes resolve to their lowest common ancestor — and a
  governing declaration is an assertion in that node's spec or a decision on the path from
  the root that reaches the node by index.
- ALWAYS: judge native sandbox and approval fields against the governing context's
  execution-boundary declaration before applying the harness contract.
- NEVER: preserve a retired schema, compatibility alias, or fallback configuration.

{!% if target == 'codex' %!}
Use a native TOML definition with `name`, `description`, and
`{{! field('configured_agent_prompt') !}}`. Keep operational settings such as
`sandbox_mode`, `mcp_servers`, and `nickname_candidates` only when the role needs them.
{!% else %!}
Use a native Markdown definition with YAML `name` and `description` frontmatter
and its system prompt in the body. Keep operational settings such as `tools`,
`disallowedTools`, `permissionMode`, and `skills` only when the role needs them.
{!% endif %!}

</configuration>

<configuration_subject>

- ALWAYS: distinguish an authored generation input from a native configuration through
  the product's committed generated-source declaration and declared generator.
  A directly authored native definition is judged in its native format.
- ALWAYS: for one authored configuration input, derive its exact emitted definitions
  from that declared mapping. Judge template syntax and profile selection at the source;
  judge native fields, permissions, and complete profile values in each emitted definition
  against the receiving harness's contract. These outputs are evidence for that one input.
- NEVER: require native fields or literal profile values inside a generation input,
  infer generated attribution from filenames, or substitute an installed copy for a
  declared output.
- ALWAYS: resolve findings about generated content to the relation's authored sources
  or generator, naming the emitted artifact as evidence. Preserve the supplied target
  identity in the verdict.
- ALWAYS: treat an unreadable declaration, ambiguous mapping, or absent required output
  as an incomplete audit when the target participates in generation. Identify the exact
  unavailable evidence; do not regenerate, install, or edit artifacts during the audit.
- ALWAYS: apply the standards appropriate to each emitted harness. An unavailable
  required harness standard leaves that surface unjudged; another harness's schema
  cannot establish its conformance.

</configuration_subject>

<profiles>

- ALWAYS: select exactly one central profile. Standard is the default. Strong, Executor,
  and Fast require an explicit selection by the governing skill or product decision.
- NEVER: infer a different profile from task difficulty, a role name, or an existing override.
- ALWAYS: obtain the selected profile's complete native configuration as one unit,
  including the intentional absence of unsupported controls.
- NEVER: author model identifiers or individual reasoning controls independently,
  translate another harness's values, extend the profile set, or substitute after a failure.
- ALWAYS: let a skill retain its invoking session's configuration, including when a
  {{! term('configured_agent') !}} invokes it; `/skill-standards` owns the rule that skill
  frontmatter carries no model or reasoning override.

| Profile  | Native configuration                    |
| -------- | --------------------------------------- |
| Standard | {{! profile_description('standard') !}} |
| Strong   | {{! profile_description('strong') !}}   |
| Executor | {{! profile_description('executor') !}} |
| Fast     | {{! profile_description('fast') !}}     |

</profiles>

<capabilities>

- ALWAYS: connect each tool grant to a required workflow step and verify that every
  step can run with the declared capabilities. An inherited tool set requires a concrete justification.
- NEVER: treat a prompt-level restriction as an enforced permission boundary.
- ALWAYS: admit a definition that inherits the invoking session's execution policy when its
  governing context declares that inheritance with linked evidence. Read the declaration
  where `<configuration>` locates the governing context, name in the verdict which form was
  read, and judge the declaration's presence; an absent native sandbox field does not
  invalidate declared inheritance.
- NEVER: accept a citation inside a definition's frontmatter or body as the inheritance
  declaration, or admit undeclared inheritance on a judgment that the definition needs the
  invoking policy — a definition whose governing context declares nothing stays a finding.
- ALWAYS: make a verifier's observation capabilities sufficient to inspect its target;
  do not grant mutation solely to run an audit or review.
- ALWAYS: keep user decisions in the invoking conversation. A configured role reports a
  missing decision with the evidence and blocked action its caller needs.
- ALWAYS: preserve progress and findings that the native harness exposes. No workflow
  assumes that only a final result can be observed.

</capabilities>

<invocation>

- ALWAYS: apply the standing authorization and invocation mechanics the repository's root
  harness instruction file declares; when it declares none, a launch waits for the
  operator's request.
- ALWAYS: leave launch timing, the exact configured role, and the target-only prompt to
  the calling skill.
- NEVER: turn a description, task pattern, available role, or apparent usefulness into a launch request.
- ALWAYS: let the invoked skill independently discover context from the supplied target.
- ALWAYS: start every audit and review without authoring conversation, reasoning,
  summaries, or a suggested verdict. Persist accepted requirements in decisions and specs first.
- NEVER: append an author-written context packet or transfer authoring history to a verifier.
- ALWAYS: follow the current native tool schema for launch parameters and collection.
  Make one launch call; analyze and report a failed launch or unusable result without retry,
  substitution, or a replacement audit in the authoring conversation.
- ALWAYS: preserve the invoked skill's result contract and finding-repair workflow.

{!% if target == 'codex' %!}
The root harness instruction file is the repository's `AGENTS.md`.
{!% else %!}
The root harness instruction file is the repository's `CLAUDE.md`.
{!% endif %!}

</invocation>

<placement>

- ALWAYS: write product-owned definitions inside the invocation checkout by default.
- ALWAYS: obtain operator confirmation naming the absolute destination before a
  user-scope create, edit, or delete outside that checkout. One approval covers one write.
- NEVER: widen a checkout-scoped request because the role could serve other products.
- ALWAYS: deliver marketplace-owned definitions through their owning plugin's build
  and installation workflow, with the plugin's invoked skills in the same scope.
- NEVER: hand-edit a generated marketplace definition or infer ownership from a filename prefix.

</placement>

<evidence>

- ALWAYS: accept a retained per-harness, per-profile release acceptance — native loading
  and one minimal isolated execution for every declared profile — as the invocation
  evidence of a definition whose governing context declares that acceptance; name the
  declaration and the acceptance artifact read.
- ALWAYS: for every other definition, retain the native configuration and actual result of
  a minimal isolated invocation after a configuration change, using the owning workflow's
  exact definition and target.
- ALWAYS: distinguish a load failure, launch failure, unusable result, and valid rejected
  verdict. Each has a different failing boundary; none supplies an approval.
- NEVER: require examples, logging, caching, or memory machinery that the role does not need.

</evidence>

<rule_catalog>

Each row names one rule this skill states and gives it a stable ID; the section column is the rule's authority. An ID never changes meaning, and a retired ID is never reused. An audit finding on a {{! term('configured_agent') !}} configuration names one ID from this catalog or from the `/agent-prompt-standards` `<rule_catalog>`, carries that rule's severity, and lists every location in its file that breaks the rule.

| Rule ID                          | Severity | Section                   | Rule                                                                                                                 |
| -------------------------------- | -------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `focused-role`                   | blocking | `<configuration>`         | The definition names one focused role and the conditions under which its owning skill invokes it                     |
| `thin-wrapper`                   | blocking | `<configuration>`         | A wrapper names its skill, invokes it, and relays its result contract without copying its workflow                   |
| `prompt-sections`                | debt     | `<configuration>`         | The prompt defines role, constraints, workflow, and output expectations, by any equivalent tag                       |
| `harness-fields`                 | blocking | `<configuration>`         | Every field the harness requires is declared, and no unsupported field is                                            |
| `governing-context-resolved`     | blocking | `<configuration>`         | The governing context is resolved before the execution boundary or evidence is judged                                |
| `execution-boundary-judged`      | blocking | `<configuration>`         | Sandbox and approval fields agree with the governing context's execution-boundary declaration                        |
| `no-retired-schema`              | blocking | `<configuration>`         | No retired schema, compatibility alias, or fallback configuration remains                                            |
| `generation-classified`          | blocking | `<configuration_subject>` | An authored generation input and a native definition are told apart through the declared generator                   |
| `emitted-definitions-judged`     | blocking | `<configuration_subject>` | Template syntax and profile selection are judged at the source, native fields in each emitted output                 |
| `no-native-fields-in-input`      | blocking | `<configuration_subject>` | A generation input carries no native field or literal profile value                                                  |
| `generated-findings-to-source`   | debt     | `<configuration_subject>` | A finding on generated content resolves to its authored source or generator                                          |
| `generation-evidence-complete`   | blocking | `<configuration_subject>` | A participating target's declaration, mapping, and required outputs are readable and present                         |
| `per-harness-standards`          | blocking | `<configuration_subject>` | Each emitted harness is judged by its own harness standard                                                           |
| `one-central-profile`            | blocking | `<profiles>`              | Exactly one central profile is selected, Standard unless a governing selection names another                         |
| `no-inferred-profile`            | blocking | `<profiles>`              | No profile is inferred from task difficulty, role name, or an existing override                                      |
| `complete-profile-configuration` | blocking | `<profiles>`              | The selected profile's complete native configuration is taken as one unit                                            |
| `no-independent-model-fields`    | blocking | `<profiles>`              | No model identifier or reasoning control is authored independently, translated, or substituted                       |
| `grants-match-workflow`          | blocking | `<capabilities>`          | Each tool grant serves a workflow step, and every step runs with the declared grants                                 |
| `no-prompt-only-boundary`        | blocking | `<capabilities>`          | A material restriction is a native permission field, never prompt text alone                                         |
| `inheritance-declared`           | blocking | `<capabilities>`          | Inherited execution policy rests on a governing declaration with linked evidence, never a citation in the definition |
| `verifier-read-only`             | blocking | `<capabilities>`          | A verifier observes its target and is granted no mutation for the audit                                              |
| `user-decisions-reported`        | debt     | `<capabilities>`          | A missing user decision returns with its evidence and blocked action                                                 |
| `progress-preserved`             | debt     | `<capabilities>`          | Progress and findings the harness exposes are preserved                                                              |
| `standing-authorization-applied` | blocking | `<invocation>`            | Launch follows the root harness instruction file's authorization and mechanics                                       |
| `no-inferred-launch`             | blocking | `<invocation>`            | Launch timing, role, and target-only prompt come from the calling skill, never a description or pattern              |
| `independent-discovery`          | blocking | `<invocation>`            | An audit or review starts without authoring history or a context packet and discovers its context                    |
| `one-native-launch`              | blocking | `<invocation>`            | One native launch call; a failed launch or unusable result is reported without retry or substitution                 |
| `result-contract-preserved`      | blocking | `<invocation>`            | The invoked skill's result contract and finding-repair workflow are preserved                                        |
| `checkout-placement`             | blocking | `<placement>`             | A definition is written in the checkout, and a user-scope write is confirmed with its absolute destination           |
| `marketplace-delivery`           | blocking | `<placement>`             | A marketplace definition ships through its plugin's build and installation, never a hand edit                        |
| `invocation-evidence`            | blocking | `<evidence>`              | A declared release acceptance or a retained minimal isolated invocation backs the definition                         |
| `failure-boundaries-distinct`    | debt     | `<evidence>`              | Load failure, launch failure, unusable result, and rejected verdict stay distinct                                    |
| `no-unneeded-machinery`          | debt     | `<evidence>`              | No example, logging, caching, or memory machinery the role does not need is required                                 |

</rule_catalog>

<success_criteria>

- Native fields and complete profile agree with the selected role and its governing requirements.
- Tool capabilities cover the workflow's steps, and material restrictions are expressed in
  native permission fields, never only in prompt text.
- The role loads, starts through an explicit skill instruction, and returns its declared contract.
- Verification evidence comes from an isolated session with independently discovered requirements.
- Execution-boundary and invocation evidence are judged against the governing context's
  declarations, and the verdict names each declaration read.

</success_criteria>
