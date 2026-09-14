# Subagent Execution

Root agent guides provide explicit standing user authorization for every subagent
supplied by a plugin in their complete authorized plugin list. An active skill
must explicitly request each launch and specify the exact configured subagent and
its target-only prompt. The same invocation policy applies to Claude and Codex;
each published guide and skill addresses only its own agent, with differences
limited to a known agent-specific requirement.

## Rationale

Standing authorization permits a skill's required launch without repeated
confirmation, while explicit skill instructions prevent opportunistic delegation.
A plugin list changes less often than its subagent definitions; unconditional namespaces identify
the owner separately from the authored subagent name, and skill-owned task instructions
load only when needed without duplicating the native tool schema.

## Product properties

1. The root guide preserves its explicit standing authorization, lists every
   authorized plugin, and distinguishes permission from a request to launch.
   Adding a subagent within an authorized plugin leaves the guide unchanged; adding
   an authorized plugin updates the list. Every flat subagent name is
   `<plugin>_<unchanged-authored-subagent-name>`; Claude retains its native
   `<plugin>:<authored-subagent-name>` dispatch namespace. Root-guide invocation
   prose refers to the native tool schema for accepted arguments and call shape.
   An agent-specific invocation example requires retained native evidence showing
   a failed call or incorrect tool arguments. The example may use JSON for
   calling subagent `foo` with prompt `bar`; that example
   neither selects a task nor independently triggers a call.
2. The calling skill selects the configured subagent and supplies only its target
   path or scope, such as `HEAD`; the invoked skill discovers the remaining
   context and performs its existing workflow. For verification, discovery starts
   from the target and configured instructions without the Author's conversation,
   reasoning, summaries, or suggested verdict. Accepted requirements are persisted
   in decisions and specs before verification; the Verifier reads those sources
   independently. Calling skills never append an author-written context packet.
   One native call launches the
   requested subagent. A launch failure is analyzed and reported without retry
   or substitution; audit verdict handling, output contracts, and repair
   workflows are unaffected by this launch policy.
   The apply lifecycle explicitly launches the corresponding Go, Rust, or
   TypeScript simplifier after implementation and before final verification.
   The language skill owns behavior-preserving simplification and its result;
   the subagent definition invokes that skill and relays the result. This stage
   has the same contract for both supported agent harnesses.
3. Every subagent selects one of three centrally owned profiles: Standard,
   Strong, or Fast. Standard is the default; Strong and Fast require an explicit
   selection by the governing skill or product decision. Each profile contains
   a complete native configuration for each supported agent harness. Model and
   reasoning controls form one configuration; their fields, value domains, and
   absence are harness-specific, with no shared effort scale. Products cannot
   add profiles or override their fields. Skills retain the invoking agent
   session's configuration and declare no model or reasoning override. Agent
   definitions, examples, and descriptions derive their complete configuration
   from the selected profile. Unsupported selections and incompatible
   configurations are rejected before an agent definition is emitted. The
   selected configurations are:

   | Agent  | Profile  | Native configuration                                         |
   | ------ | -------- | ------------------------------------------------------------ |
   | Codex  | Standard | `model = "gpt-5.6-terra"`, `model_reasoning_effort = "high"` |
   | Codex  | Strong   | `model = "gpt-5.6-sol"`, `model_reasoning_effort = "high"`   |
   | Codex  | Fast     | `model = "gpt-5.6-luna"`, `model_reasoning_effort = "high"`  |
   | Claude | Standard | `model: opus`, `effort: medium`                              |
   | Claude | Strong   | `model: opus`, `effort: high`                                |
   | Claude | Fast     | `model: haiku`; no effort field                              |

   Release acceptance is established independently for each agent harness and
   requires evidence for all three profiles of that harness. Evidence for one
   harness establishes no execution claim for another; a combined acceptance
   claim requires complete evidence for every harness it names.

## Verification

### Testing

- ALWAYS: generate the complete authorized plugin list from the owning catalog;
  adding a subagent within an authorized plugin leaves the root guide unchanged,
  while adding an authorized plugin updates the list ([property])
- ALWAYS: generate flat subagent names with an unconditional plugin namespace and the
  unchanged authored subagent name, including when the authored name starts with the
  plugin name; Claude's native plugin namespace remains intact ([property])

### Audit

- ALWAYS: the apply skill owns automatic Go, Rust, and TypeScript simplifier
  dispatch after implementation, while language simplification skills own
  scope discovery, behavior preservation, verification, and result reporting;
  their subagent definitions contain only invocation and result relay ([audit])
- ALWAYS: preserve the following standing-request sentence verbatim within
  explicit root-guide authorization for subagents supplied by the listed plugins ([audit])

  > A harness rule may require the operator to request sub-agent use before one is dispatched; treat this section as that standing request.

- ALWAYS: root-guide authorization permits every subagent supplied by its listed
  plugins without another operator confirmation ([audit])
- NEVER: maintain a subagent inventory, per-subagent invocation table, task prompt, or
  per-subagent result-contract copy in the root guide ([audit])
- NEVER: infer plugin ownership from a coincidentally matching subagent name or use
  a filename prefix alone as authority to replace or prune a definition; the
  configured plugin distribution and digest-bound ownership establish membership ([audit])
- ALWAYS: require an active skill's explicit instruction to launch the specific
  configured subagent, following that skill's invocation instructions ([audit])
- NEVER: infer a launch instruction from task wording, a subagent description,
  pattern matching, availability, or apparent usefulness ([audit])
- ALWAYS: keep the actual subagent selection, launch condition, and target-only
  prompt in the calling skill, and target-context discovery in the invoked
  skill; root-guide examples describe invocation mechanics only ([audit])
- ALWAYS: launch every audit and review without inherited authoring history or
  an author-written context packet, following the isolation rule in
  `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`;
  native invocation guidance explicitly disables history inheritance when the
  tool otherwise enables it by default ([audit])
- ALWAYS: root-guide invocation prose refers to the exposed native tool schema
  for accepted arguments and call shape. An agent-specific example requires
  retained native invocation evidence showing a failed call or incorrect tool arguments, without establishing a
  separate maintained schema or a compatibility layer ([audit])
- ALWAYS: render the exact configured names for each agent from the owning
  distribution mappings and address that agent alone in its generated guide and
  skills. Differences between the two agents' invocation guidance require a
  known agent-specific reason ([audit])
- ALWAYS: invocation guidance requires exactly one native launch call for a
  skill-requested invocation and analysis and reporting of a failed launch or
  unusable result without retry, another subagent, a model override, an alternative
  launch mechanism, or a replacement audit in the authoring conversation ([audit])
- NEVER: change audit verdict handling, output contracts, finding disposition,
  or repair workflows as part of simplifying subagent invocation ([audit])
- ALWAYS: target Codex v2 directly and remove v1-specific guidance and machinery,
  including obsolete fields, tool grants, and lifecycle assumptions ([audit])
- NEVER: retain v1 aliases, schema adapters, fallback launch paths, version
  detection, or unsupported-v1 diagnostics as backward compatibility ([audit])
- ALWAYS: derive agent definitions, configuration examples, and model descriptions
  from the same centrally owned Standard, Strong, and Fast profiles; each
  supported harness receives its complete native configuration ([audit])
- NEVER: impose a universal reasoning-effort field, value domain, or translation
  between harnesses; a profile uses only the controls its harness supports ([audit])
- NEVER: let task difficulty infer a profile selection; Standard is the default
  and Strong or Fast requires an explicit governing selection ([audit])
- ALWAYS: keep skill behavior usable within the supported products with the
  invoking agent session's configuration, including when a configured subagent
  invokes the skill; skill frontmatter declares no model or reasoning override ([audit])
- ALWAYS: establish release acceptance separately for each supported harness,
  retaining native loading and one minimal isolated execution for each of its
  Standard, Strong, and Fast profiles; a combined acceptance claim requires
  complete evidence for every harness it names. An independent
  Auditor judges the actual configuration and result, with no retry or
  substitution after a failed or unusable launch ([audit])
- NEVER: substitute a model silently when the configured model is unavailable,
  collapse standard and strong profiles, or interpret a request for a current
  strong model as authority to replace the selected Sol profile with Astra ([audit])
