# Issues: Prose Plugin

## Strong model selection for prose auditing has no recorded justification

`src/plugins/prose/agents/prose-auditor.md` selects the central Strong profile.
`src/plugins/prose/skills/audit-prose/SKILL.md` retains its invoking session's
configuration, as every skill does. `spx/43-prose.enabler/prose.md` declares the audit's behavior and
output contract but gives no requirement or rationale for a strong model, and
this node carries no comparative evidence establishing that the standard profile
cannot meet its quality requirements.

The shared profile policy permits an explicit Strong selection, but that
permission supplies no justification for this role's selection. The authoring
policy reconciliation is tracked in
`spx/43-instructions.enabler/21-subagents.enabler/ISSUES.md`.

**Required handling.** Establish whether prose auditing needs the strong profile
by comparing standard and strong profiles against the same audit cases and
quality criteria, with effort and cost recorded. Either document the requirement
and its evidence in the governing decision and spec, or select the standard
profile in the agent. A role's name or its existing assignment is
insufficient justification. Keep standard and strong as distinct model profiles
regardless of which profile this role selects.

**Disposition and revisit condition.** The operator requested tracking this
decision separately while the remaining model-policy interview proceeds. This
entry changes no model assignment. Revisit when the comparative audit evidence
is available, or when the operator explicitly decides the quality-versus-cost
trade-off; reconcile the general auditor policy in the same change.

The Change #76 configured-agent audit reconfirmed this gap as blocking under the
current central-profile standard: `instructions:subagent-auditor` finding
`f-002` found no governing selection or comparative evidence for `profile:
strong` on head `843ddd709b058970d414ec755cc10121ff6bb5ff`.

## The prose auditor has no enforced read-only runtime boundary

`src/plugins/prose/agents/prose-auditor.md` grants unrestricted `Bash` while
its prompt promises a read-only audit. The generated Codex definition omits
`sandbox_mode`, and the generated Claude definition retains the unrestricted
shell grant. A prompt prohibition therefore supplies no enforced mutation
boundary in either emitted configuration.

**Required handling**: identify the shell operations `prose:audit-prose`
actually requires, restrict the Claude grant to those operations, and declare
the corresponding read-only native boundary for Codex. Retain a minimal
isolated audit result for the exact emitted role.

**Evidence**: `instructions:subagent-auditor` finding `f-001` against
`src/plugins/prose/agents/prose-auditor.md` on Change #76 head
`843ddd709b058970d414ec755cc10121ff6bb5ff`.

## Eval evidence for the prose surface stays deferred

The style-adherence and structure-conformance evals for the prose surface remain unwritten by operator decision: the eval harness is under repair in a separate concurrent effort, and no spec node names that effort yet, so this entry is the owning record rather than a pointer. Revisit when the eval surface is operational.

`spx/15-spec-coverage.adr.md` places this node's deliverable in the `[eval]` category — the prose surface is LLM-driven behavior whose skills emit a structured verdict. Until that lane exists, every assertion here is verified by a dispatched verifier agent session.

## The three kind style layers use markdown headings

`/skill-standards` recommends pure XML structure for a skill's file set; `prose-standards/SKILL.md` complies while `references/documentation.md`, `references/copy.md`, and `references/interface.md` use markdown `#`/`##` headings. Converting the three reference files is a structural rewrite of each file, deferred as a separate concern because the chat-voice changeset touches their content, not their structure. Surfaced by the skill audit on the chat-voice branch.

## The documentation layer's Overrides section lists entries with no base rule behind them

Two Overrides entries trace to no base rule they relax: the bold row-key cell restates the base table pack's own permission, and the parentheses allowance names no base parenthesis ban. Reworking the section so every declared override cites the relaxed base rule, or reclassifies as additive kind guidance, is a layer-taxonomy change beyond the chat-voice changeset. Surfaced by the skill audit on the chat-voice branch.
