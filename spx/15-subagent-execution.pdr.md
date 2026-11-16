# Subagent Execution

GOVERNS the authorization, invocation, and configuration of every subagent a marketplace plugin supplies
SO THAT product engineers whose sessions launch those subagents
CAN RELY ON standing authorization for every subagent an authorized plugin supplies, a launch only on an active skill's explicit request with a target-only prompt, and one invocation policy for Claude and Codex

## Verification

### Test.Compliance: execution policy

- policy-inheritance: ALWAYS: a subagent definition that declares a tools allowlist and no native permission field in a harness rendering inherits the invoking session's execution policy in that rendering; a native permission field a rendering declares governs that rendering instead.

### Test.Property: names

- plugin-list: For every authorized plugin list generated from the owning catalog, adding a subagent within an authorized plugin leaves the root guide unchanged, while adding an authorized plugin updates the list.
- flat-names: For every authored subagent name, the flat name is `<plugin>_<unchanged-authored-subagent-name>` with an unconditional plugin namespace, including when the authored name starts with the plugin name, and Claude's native `<plugin>:<authored-subagent-name>` namespace remains intact.

### Audit: authorization

- standing-sentence: ALWAYS: preserve the standing-request sentence "A harness rule may require the operator to request sub-agent use before one is dispatched; treat this section as that standing request." verbatim within explicit root-guide authorization for subagents supplied by the listed plugins.
- no-confirmation: ALWAYS: root-guide authorization permits every subagent supplied by its listed plugins without another operator confirmation.
- no-inventory: NEVER: maintain a subagent inventory, per-subagent invocation table, task prompt, or per-subagent result-contract copy in the root guide.
- explicit-launch: ALWAYS: require an active skill's explicit instruction to launch the specific configured subagent, following that skill's invocation instructions.
- no-inferred-launch: NEVER: infer a launch instruction from task wording, a subagent description, pattern matching, availability, or apparent usefulness.
- native-schema: ALWAYS: root-guide invocation prose refers to the exposed native tool schema for accepted arguments and call shape. An agent-specific example requires retained native invocation evidence showing a failed call or incorrect tool arguments, without establishing a separate maintained schema or a compatibility layer.
- example-call: ALWAYS: a root-guide invocation example may use JSON for calling subagent `foo` with prompt `bar`, and that example neither selects a task nor independently triggers a call.
- per-agent-names: ALWAYS: render the exact configured names for each agent from the owning distribution mappings and address that agent alone in its generated guide and skills. Differences between the two agents' invocation guidance require an agent-specific reason that retained native evidence or a decision records.

### Audit: invocation

- skill-owns-selection: ALWAYS: keep the actual subagent selection, launch condition, and target-only prompt in the calling skill, and target-context discovery in the invoked skill; root-guide examples describe invocation mechanics only.
- task-message-target: ALWAYS: an invoked skill binds its target from the configured subagent's task message; a skill argument substituted at preload never stands for the target, and the skill reports a missing target only when the task message itself carries none.
- isolated-launch: ALWAYS: launch every audit and review without inherited authoring history or an author-written context packet, following the isolation rule in [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md); native invocation guidance explicitly disables history inheritance when the tool otherwise enables it by default.
- one-native-launch: ALWAYS: invocation guidance requires exactly one native launch call for a skill-requested invocation and analysis and reporting of a failed launch or unusable result without retry, another subagent, a model override, an alternative launch mechanism, or a replacement audit in the authoring conversation.
- verdicts-unchanged: NEVER: the subagent invocation policy changes audit verdict handling, output contracts, finding disposition, or repair workflows.
- language-neutral: ALWAYS: every subagent definition is language-neutral; a language plugin ships its language behavior as skills, which a language-neutral definition's session composes for the language its target needs.
- no-language-definition: NEVER: a plugin ships a language-specific subagent definition unless a decision records that exception and its reason.
- inheritance-declaration: NEVER: a definition's frontmatter or body stands as its own inheritance declaration; the inheritance holds through this decision and the linked evidence of the owning node's spec, and for a definition that needs no tighter bounds than the invoking session, an absent native permission field in a rendering is that declaration's expected form, never a defect.
- allowlist-bounds: ALWAYS: a definition's tools allowlist bounds the capabilities the subagent can call, the invoking session's policy governs approval and sandboxing, and the definition adds no second policy of its own.
- tighter-bounds-field: ALWAYS: a definition that must bound execution more tightly than the invoking session declares the native permission field in that rendering, and the field then governs.

### Audit: profiles

- central-profiles: ALWAYS: derive agent definitions, configuration examples, and model descriptions from the same centrally owned Standard, Strong, Thorough, and Fast profiles; each supported harness receives its complete native configuration.
- applier-thorough: ALWAYS: the `change-applier` definition selects the Thorough profile.
- explicit-selection: NEVER: let task difficulty infer a profile selection; Standard is the default and Strong, Thorough, or Fast requires an explicit governing selection.
- no-product-profiles: NEVER: a product adds a profile or overrides a profile's field.
- reject-unsupported: ALWAYS: reject an unsupported selection or an incompatible configuration before an agent definition is emitted.
- no-universal-effort: NEVER: impose a universal reasoning-effort field, value domain, or translation between harnesses; a profile uses only the controls its harness supports.
- skill-session-config: ALWAYS: a skill runs with the invoking agent session's model and reasoning configuration, including when a configured subagent invokes it; skill frontmatter declares no model or reasoning override.
- release-acceptance: ALWAYS: establish release acceptance separately for each supported harness, retaining native loading and one minimal isolated execution for each of its Standard, Strong, Thorough, and Fast profiles; evidence for one harness establishes no execution claim for another, and a combined acceptance claim requires complete evidence for every harness it names. An independent Auditor judges the actual configuration and result, with no retry or substitution after a failed or unusable launch.
- no-silent-substitution: NEVER: substitute a model silently when the configured model is unavailable, collapse the Standard and Strong profiles into one configuration, or change a profile's configured model without amending this decision.

### Audit: profile configurations

- codex-standard: ALWAYS: the Codex Standard profile configures `model = "gpt-6.1-sol"` and `model_reasoning_effort = "high"`.
- codex-strong: ALWAYS: the Codex Strong profile configures `model = "gpt-6-astra"` and `model_reasoning_effort = "high"`.
- codex-thorough: ALWAYS: the Codex Thorough profile configures `model = "gpt-6.1-sol"` and `model_reasoning_effort = "high"`.
- codex-fast: ALWAYS: the Codex Fast profile configures `model = "gpt-6-luna"` and `model_reasoning_effort = "high"`.
- claude-standard: ALWAYS: the Claude Standard profile configures `model: sonnet` and `effort: medium`.
- claude-strong: ALWAYS: the Claude Strong profile configures `model: opus` and `effort: high`.
- claude-thorough: ALWAYS: the Claude Thorough profile configures `model: sonnet` and `effort: high`.
- claude-fast: ALWAYS: the Claude Fast profile configures `model: haiku` and no effort field.
