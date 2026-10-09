---
name: subagent-standards
description: >-
  Configuration, configuration-subject, profile, capability, invocation, placement, and
  evidence standards for {{! term('configured_agents') !}}, with their rule catalog. Loaded by
  creator and auditor skills.
user-invocable: false
allowed-tools: Read, {{! tool('use_skill') !}}
---

{!% require_skill 'instructions:agent-prompt-standards' %!}

{!% require_skill 'instructions:skill-standards' %!}

<objective>
One set of authoring rules for {{! term('configured_agents') !}} and their rule catalog, under
which a definition's native configuration, permissions, task boundary, and result are
independently inspectable.
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

Every rule the sections above state carries exactly one row below, giving it one stable identifier and one severity and naming the section that states it. The stating section is authoritative for what the rule requires. Rules this skill defers to `/agent-prompt-standards` or `/skill-standards` carry their rows in those catalogs. The identifier, severity, finding-key, and closed-vocabulary rules for this catalog are the catalog contract `/skill-standards` states for every instructions rule catalog.

| Identifier                        | Severity | Rule                                                                                                                                                                                                                                                       | Stated in                 |
| --------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `role_focus`                      | debt     | A definition names one focused role and the conditions under which its owning skill invokes it.                                                                                                                                                            | `<configuration>`         |
| `wrapper_logic`                   | blocking | A wrapper whose behavior belongs to a skill names that skill, invokes it, and relays its declared result contract without copying its workflow.                                                                                                            | `<configuration>`         |
| `prompt_content_missing`          | debt     | The prompt defines the role, material constraints, workflow, and output expectations, in these or equivalent semantic tags.                                                                                                                                | `<configuration>`         |
| `harness_field_missing`           | blocking | A definition declares every field its harness requires.                                                                                                                                                                                                    | `<configuration>`         |
| `unsupported_configuration`       | blocking | A definition carries no configuration its harness does not support.                                                                                                                                                                                        | `<configuration>`         |
| `native_definition_format`        | blocking | A definition uses its harness's native format and fields.                                                                                                                                                                                                  | `<configuration>`         |
| `unneeded_operational_setting`    | debt     | A definition keeps an operational setting only when the role needs it.                                                                                                                                                                                     | `<configuration>`         |
| `governing_context_unresolved`    | blocking | A definition's execution boundary and evidence are judged only after its owning node and governing declarations are resolved through the tree.                                                                                                             | `<configuration>`         |
| `execution_boundary_mismatch`     | blocking | Native sandbox and approval fields agree with the governing context's execution-boundary declaration before the harness contract applies.                                                                                                                  | `<configuration>`         |
| `retired_configuration`           | debt     | A definition carries no retired schema, compatibility alias, or fallback configuration.                                                                                                                                                                    | `<configuration>`         |
| `generation_attribution`          | blocking | A definition is classified as a generation input or a native configuration from the committed generated-source declaration and declared generator, never from its filename.                                                                                | `<configuration_subject>` |
| `generated_surface_split`         | blocking | Template syntax and profile selection are judged at the generation input; native fields, permissions, and complete profile values are judged in each emitted definition against its harness's contract.                                                    | `<configuration_subject>` |
| `installed_copy_substitution`     | blocking | An installed copy never stands in for a declared output.                                                                                                                                                                                                   | `<configuration_subject>` |
| `generated_finding_resolution`    | debt     | A finding about generated content resolves to the relation's authored sources or generator, names the emitted artifact as evidence, and preserves the supplied target identity.                                                                            | `<configuration_subject>` |
| `generation_evidence_unavailable` | blocking | An unreadable declaration, ambiguous mapping, or absent required output leaves the audit incomplete, naming the unavailable evidence, with no artifact regenerated, installed, or edited.                                                                  | `<configuration_subject>` |
| `cross_harness_conformance`       | blocking | Each emitted definition is judged against its own harness's standard; another harness's schema never establishes its conformance, and an unavailable standard leaves that surface unjudged.                                                                | `<configuration_subject>` |
| `profile_selection`               | blocking | A definition selects exactly one central profile: Standard by default, and Strong, Executor, or Fast only by an explicit governing selection.                                                                                                              | `<profiles>`              |
| `inferred_profile`                | blocking | No profile is inferred from task difficulty, a role name, or an existing override.                                                                                                                                                                         | `<profiles>`              |
| `partial_profile_configuration`   | blocking | The selected profile's complete native configuration is taken as one unit, including the intentional absence of unsupported controls.                                                                                                                      | `<profiles>`              |
| `independent_model_control`       | blocking | No model identifier or reasoning control is authored independently, translated from another harness, added as a new profile, or substituted after a failure.                                                                                               | `<profiles>`              |
| `tool_grant_unjustified`          | debt     | Each tool grant connects to a required workflow step, and an inherited tool set carries a concrete justification.                                                                                                                                          | `<capabilities>`          |
| `step_lacks_capability`           | blocking | Every workflow step can run with the declared capabilities.                                                                                                                                                                                                | `<capabilities>`          |
| `prompt_only_restriction`         | blocking | A material restriction is enforced through native permission fields, never only through prompt text.                                                                                                                                                       | `<capabilities>`          |
| `undeclared_policy_inheritance`   | blocking | A definition that inherits the invoking session's execution policy has that inheritance declared with linked evidence in its governing context, never by a citation inside the definition or on judgment, and the verdict names the declaration form read. | `<capabilities>`          |
| `verifier_mutation_grant`         | blocking | A verifier's capabilities suffice to observe its target, and no mutation is granted solely to run an audit or review.                                                                                                                                      | `<capabilities>`          |
| `delegated_user_decision`         | blocking | User decisions stay in the invoking conversation; a configured role reports a missing decision with the evidence and blocked action its caller needs.                                                                                                      | `<capabilities>`          |
| `final_only_observation`          | debt     | A workflow preserves the progress and findings the harness exposes and assumes no final-only observation.                                                                                                                                                  | `<capabilities>`          |
| `invocation_authorization`        | blocking | A launch follows the standing authorization and mechanics the root harness instruction file declares, and waits for the operator's request where it declares none.                                                                                         | `<invocation>`            |
| `launch_decision_outside_caller`  | blocking | Launch timing, the exact configured role, and the target-only prompt belong to the calling skill.                                                                                                                                                          | `<invocation>`            |
| `inferred_launch`                 | blocking | No description, task pattern, available role, or apparent usefulness becomes a launch request.                                                                                                                                                             | `<invocation>`            |
| `caller_supplied_context`         | blocking | The invoked skill discovers its context independently from the supplied target.                                                                                                                                                                            | `<invocation>`            |
| `verifier_isolation`              | blocking | Every audit and review starts without authoring conversation, reasoning, summaries, a suggested verdict, or an author-written context packet, after accepted requirements are persisted.                                                                   | `<invocation>`            |
| `launch_retry_or_substitution`    | blocking | A launch is one call under the current native tool schema, and a failed launch or unusable result is analyzed and reported without retry, substitution, or a replacement audit.                                                                            | `<invocation>`            |
| `result_contract_altered`         | blocking | The invoked skill's result contract and finding-repair workflow are preserved.                                                                                                                                                                             | `<invocation>`            |
| `checkout_placement`              | debt     | A product-owned definition is written inside the invocation checkout by default.                                                                                                                                                                           | `<placement>`             |
| `unconfirmed_user_scope_write`    | blocking | A user-scope create, edit, or delete outside the checkout follows operator confirmation naming the absolute destination, one approval per write.                                                                                                           | `<placement>`             |
| `widened_scope`                   | blocking | A checkout-scoped request is never widened because the role could serve other products.                                                                                                                                                                    | `<placement>`             |
| `marketplace_delivery`            | blocking | A marketplace-owned definition is delivered through its owning plugin's build and installation workflow, with the plugin's invoked skills in the same scope.                                                                                               | `<placement>`             |
| `generated_definition_edit`       | blocking | A generated marketplace definition is never hand-edited.                                                                                                                                                                                                   | `<placement>`             |
| `prefix_ownership`                | blocking | Ownership of a definition is never inferred from a filename prefix.                                                                                                                                                                                        | `<placement>`             |
| `release_acceptance_evidence`     | blocking | A definition whose governing context declares release acceptance has retained per-harness, per-profile acceptance, and the verdict names the declaration and acceptance artifact read.                                                                     | `<evidence>`              |
| `invocation_evidence_missing`     | blocking | Every other definition retains the native configuration and actual result of a minimal isolated invocation after a configuration change, using the owning workflow's exact definition and target.                                                          | `<evidence>`              |
| `failure_boundary_conflation`     | blocking | A load failure, launch failure, unusable result, and valid rejected verdict are distinguished, and none supplies an approval.                                                                                                                              | `<evidence>`              |
| `unneeded_machinery`              | debt     | A definition requires no examples, logging, caching, or memory machinery the role does not need.                                                                                                                                                           | `<evidence>`              |

</rule_catalog>

<success_criteria>

- Native fields and complete profile agree with the selected role and its governing requirements.
- Tool capabilities cover the workflow's steps, and material restrictions are expressed in
  native permission fields, never only in prompt text.
- The role loads, starts through an explicit skill instruction, and returns its declared contract.
- Verification evidence comes from an isolated session with independently discovered requirements.
- Execution-boundary and invocation evidence are judged against the governing context's
  declarations, and the verdict names each declaration read.
- No rule in `<rule_catalog>` is violated, and every finding against these standards names
  one catalog identifier.

</success_criteria>
