---
name: incorporate-correction
description: >-
  ALWAYS invoke this skill when receiving an operator correction to behavior,
  reasoning, workflow, or instructions, including a repeated correction or
  a failure to follow an existing rule.
argument-hint: "[correction and incident reference]"
allowed-tools: Read, Glob, Grep, Write, Edit, Skill, AskUserQuestion
---

<objective>

An applied correction with an evidence-supported diagnosis, dispositions for affected earlier decisions and work, and any reusable instruction repair tracked through publication.

</objective>

<intake>

Read `$ARGUMENTS` as the correction and incident reference. When empty, use the latest operator correction in the active conversation. When neither supplies a correction, request the missing incident and change nothing on an inferred complaint.

Preserve the operator's meaning, the specific behavior corrected, the expected behavior, and an inspectable source reference. Read only the conversation and artifacts needed to establish that incident, within the authorized access scope. Keep private incident details out of published instructions unless they are necessary and authorized.

</intake>

<workflow>

<step name="apply_current_correction">

Apply the corrected understanding to current work immediately. Stop actions that would repeat the corrected failure. Continue work that can safely proceed while preparing the durable repair; skill publication is not a blanket prerequisite for continuing corrected work.

When the correction concerns repeated planning, permission requests, or process discussion in place of delivery, identify and complete the next authorized artifact-producing action. Return the artifact with its actual evidence and remaining limits. Prepare the instruction repair alongside that work; explaining the diagnosis alone does not apply this correction.

Distinguish a reusable behavioral correction from a changed product requirement, a one-time exception, or a factual correction local to one artifact. Preserve explicit limits on scope. Route product truth changes through their owning workflow. A local correction with no reusable lesson needs a supported disposition, without inventing a general rule.

When the correction leaves competing interpretations that change the next action, prepare the evidence and ask the operator to settle that choice. Continue independent work. Never silently generalize an unresolved interpretation into standing instructions.

</step>

<step name="diagnose_instruction_failure">

Locate the instruction that governs the corrected behavior. Resolve both its durable source and the version available during the incident; distinguish source content from generated installations. Inspect the actual trigger, routing, required context, decision point, and available evidence of loading.

When the rule already exists, investigate why it failed before adding wording:

| Evidence                                                        | Repair target                                                               |
| --------------------------------------------------------------- | --------------------------------------------------------------------------- |
| The needed behavior has no governing instruction                | Add the reusable rule to the skill that owns that behavior.                 |
| The rule exists, but the invocation route omitted it            | Repair activation, composition, or the required read at the decision point. |
| The source is corrected, but the active installation is older   | Use the owning distribution workflow; establish which version was loaded.   |
| Competing instructions prescribe different actions              | Resolve authority and repair the conflicting lower instruction.             |
| The instruction leaves the relevant condition or action unclear | Make that condition and its required action explicit.                       |
| The loaded rule is clear, but the behavior violates it          | Identify the skipped decision or check and repair the workflow there.       |

Separate observed facts from hypotheses. An absent loading receipt alone does not prove that a rule was never loaded. When the cause remains unknown, preserve the uncertainty and collect the evidence needed to distinguish the plausible causes. Never claim that repeating a rule fixes an unexplained failure.

Inspect previous occurrences only as needed to establish recurrence and the same failure mechanism. Finding the rule in a file does not complete the diagnosis.

</step>

<step name="trace_and_repair_consequences">

Trace the corrected assumption through earlier decisions, directions, and work that relied on it. Start with the incident's records and follow evidenced dependencies, including affected Changes, their Parents and children, Handoffs, and resulting artifacts. Extend the trace across products when those dependencies cross products. Include completed work when its result still depends on the corrected assumption. A shared keyword alone does not establish a dependency.

For each affected decision or work item, establish whether the corrected understanding leaves it valid, requires a repair, or reopens a judgment. Preserve the supporting evidence and any unresolved reach of the trace. Apply authorized repairs through the owning workflow; route work held by another position through its responsible holder. Return reopened judgments to their owner. A correction alone grants no authority to rewrite another holder's work, reverse an integration, or erase a recorded decision.

Prevent further dependent work from repeating the corrected error while its disposition is unresolved. Continue independent work. Prepare the instruction repair alongside consequence repair; completion of either does not establish completion of the other. Keep outstanding consequences in their owning work records with the next action and revisit condition.

</step>

<step name="prepare_owning_repair">

Prepare a concrete repair in the same turn when the correction reveals a reusable lesson. Put it in the skill or instruction that owns the failed behavior. Repair a route in the routing instruction that failed to load the behavior; keep the invoked capability independent of its callers. Use shared standards when the rule is already owned there. Avoid copying a general rule into every affected skill.

For skill-bundle repairs:

Use skill `instructions:create-skill`.

Supply the incident evidence, supported diagnosis, expected behavior, and exact authorized source target. Consume its returned paths, checks, and unresolved requirements. For a custom agent definition instead:

Use skill `instructions:create-subagent`.

Let the owning authoring workflow select its required standards and checks.

Resolve write authority before editing. Existing operator authorization governs its named scope; a correction grants no general permission to edit home configuration, another checkout, or generated plugin caches. If the durable source is unavailable or requires an unresolved authorization, prepare the exact proposed repair in authorized scratch space and retain the blocked destination and next action.

Keep the reusable trigger, decision, required action, and applicable boundaries. Include a concrete failure example only when it teaches the prevention and is supported by the incident. Keep dated conversation history and publication progress in the owning work record rather than the skill body.

In a Change-governed repository, use the owning Change workflow to carry the repair. Reuse an applicable held Change where its intent covers the repair; otherwise follow the proposal workflow. Never substitute an operating note for the required Change or treat this skill as integration authority.

</step>

<step name="establish_effect_and_publish">

Verify the repair through the owning workflow's deterministic checks, fresh-context exercise, and independent review requirements. Use a case that exposes the original failure and a nearby case where the new rule must not change behavior. For a loading failure, establish that the right skill is invoked at the relevant decision point; a text-only check cannot prove that result. Report unavailable evidence explicitly.

Continue through the authorized publication and distribution workflow. Record source revision, publication result, and loaded version where observable. Never count an edited source file as proof that an existing session has loaded the repair. Preserve the correction's active operational effect while distribution remains pending.

If publication waits on an operator decision or an external dependency, retain the exact repair, current state, next action, and revisit condition in the owning continuation record. Continue independent work. Report prepared, verified, published, and loaded separately, using evidence for each state.

</step>

</workflow>

<result_contract>

Return the corrected behavior and its scope; the incident reference; the diagnosis with supporting evidence and remaining uncertainty; affected earlier decisions and work with their dispositions; the owning source and repair location, or the reason no reusable repair applies; verification and publication results; and any unresolved dependency with its next action. Reuse the owning workflow's record rather than creating another work queue.

</result_contract>

<failure_handling>

- Missing incident evidence: apply the explicit correction, preserve the diagnostic limit, and request only evidence needed for the repair.
- Inaccessible or unauthorized source: retain a concrete proposed repair in authorized scratch and name the destination that prevents publication.
- Failed verification: retain the failure evidence and repair through the owning authoring workflow; keep safe corrected work moving.
- Interrupted repair: resume from the recorded source revision and next action, checking whether publication already occurred before repeating it.
- A further operator correction to the repair: apply it and revise the diagnosis and patch; retain the original incident's provenance.

</failure_handling>

<success_criteria>

- Current work follows the operator's correction within its stated scope.
- Earlier decisions and work that depend on the corrected assumption have evidenced dispositions; unresolved consequences and limits of the trace remain visible in their owning records.
- The diagnosis distinguishes a missing instruction from a loading, distribution, conflict, clarity, or execution failure, with uncertainty exposed where evidence is insufficient.
- A reusable lesson has a concrete repair in its owning instruction; a one-time correction does not become an unsupported standing rule.
- The repair's evidence addresses the original failure and an adjacent behavior that must remain valid.
- Publication and active loading are reported only to the extent established by evidence; an unfinished repair has an actionable continuation.
- Work that can safely proceed continues while the repair moves through its owning workflow.

</success_criteria>
