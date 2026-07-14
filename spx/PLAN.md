# Agentic execution and coding-agent surface migration

This plan moves shared configured-agent semantics into the agentic-execution domain and runtime-specific conversion and installation ownership into coding-agent surfaces. Product truth remains in [`spx/outcomeeng.product.md`](outcomeeng.product.md) and the linked node specifications and decisions.

## Active scope

### Agentic-execution domain

- **Current:** New structure
- **Receiver:** [`spx/43-agentic-execution.enabler`](43-agentic-execution.enabler/agentic-execution.md), projected as the agentic-execution domain when the methodology admits domain suffixes
- **Action:** Invoke `decompose-next` on [`spx/43-agentic-execution.enabler`](43-agentic-execution.enabler/agentic-execution.md). Review the receiver, reach, and sibling index before authoring the configured-agent task-profile product decision record (PDR).
- **Prerequisite:** Retain the `.enabler` holding suffix until Spec Tree tooling admits `.domain`. Keep the target kind in the reviewed projection.
- **Verify:** Run the PDR audit, spec audit, `spx validation markdown`, and `spx spec status --format json`.

### Configured-agent classification

- **Current:** [`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md), [`spx/21-spec-tree.enabler/17-audit.adr.md`](21-spec-tree.enabler/17-audit.adr.md), and the [configured-agent definitions](../src/plugins/)
- **Receiver:** [`spx/43-agentic-execution.enabler`](43-agentic-execution.enabler/agentic-execution.md), projected as the agentic-execution domain when the methodology admits domain suffixes
- **Action:** Classify every configured agent as verification, implementation, or maintenance. Define explicit per-agent Claude Code and Codex model and effort selections. Update direct decision citations at semantic consumer boundaries.
- **Prerequisite:** The task-profile PDR governs semantics. Runtime renderers preserve explicit choices without cross-runtime inference.
- **Verify:** Run the PDR audit, affected spec audits, subagent audit, focused agent-conversion tests, and changeset review.

### Codex custom-agent conversion

- **Current:** [`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler`](18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/agents.md)
- **Receiver:** [`spx/68-coding-agents.enabler`](68-coding-agents.enabler/coding-agents.md); the future projection places custom-agent conversion under the Codex custom-agent surface
- **Action:** Invoke `decompose-next` on [`spx/68-coding-agents.enabler`](68-coding-agents.enabler/coding-agents.md) to project the Claude Code and Codex peer surfaces. Split Codex custom-agent conversion from installation.
- **Prerequisite:** Retain `.enabler` holding suffixes for every projected child. Assign target indices from consumer-side dependency evidence.
- **Verify:** Run spec audits, focused conversion tests, the implementation audit, and changeset review.

### Codex custom-agent installation

- **Current:** Installation behavior in [`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler`](18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/agents.md) and sync sequencing in [`spx/32-distribution.enabler/21-sync.enabler`](32-distribution.enabler/21-sync.enabler/sync.md)
- **Receiver:** [`spx/68-coding-agents.enabler`](68-coding-agents.enabler/coding-agents.md); the future projection places custom-agent installation under the Codex custom-agent surface
- **Action:** Move installation ownership beneath the Codex custom-agent surface. Sync retains marketplace sequencing and invokes installation.
- **Prerequisite:** Conversion precedes installation. Installation remains separate from marketplace sync orchestration.
- **Verify:** Run spec audits, focused installation and sync tests, the implementation audit, and changeset review.

## Temporary dependency inversions

### Verification branch

- **Current dependency:** [`spx/21-spec-tree.enabler/16-verification.enabler`](21-spec-tree.enabler/16-verification.enabler/verification.md)
- **Provider:** [`spx/43-agentic-execution.enabler`](43-agentic-execution.enabler/agentic-execution.md), projected as the agentic-execution domain when domain suffixes become available
- **Missing context:** The index-21 verification branch cannot inherit a later sibling specification as lower-index context.
- **Bridge:** Cite the task-profile PDR directly from the first semantic consumer specs and decisions.
- **Settlement:** Move verification-agent semantics beneath the target domain, or place the provider before its consumers in the modernized structure.

### Audit branch

- **Current dependency:** [`spx/21-spec-tree.enabler/17-audit.adr.md`](21-spec-tree.enabler/17-audit.adr.md) and [`spx/21-spec-tree.enabler/68-audit.enabler`](21-spec-tree.enabler/68-audit.enabler/audit.md)
- **Provider:** [`spx/43-agentic-execution.enabler`](43-agentic-execution.enabler/agentic-execution.md), projected as the agentic-execution domain when domain suffixes become available
- **Missing context:** Audit-specific configured-agent taxonomy precedes its shared semantic provider.
- **Bridge:** Keep audit composition in the audit decision and cite the task-profile PDR for shared task and model policy.
- **Settlement:** Audit-specific consumers retain only audit composition. Shared configured-agent semantics resolve through the target domain.

### Agent conversion

- **Current dependency:** [`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler`](18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/agents.md)
- **Provider:** [`spx/68-coding-agents.enabler`](68-coding-agents.enabler/coding-agents.md), projected as the coding-agents surface when surface suffixes become available
- **Missing context:** Conversion and installation behavior remains in an earlier build holding path.
- **Bridge:** Treat the current node as inventory. Change no ownership claim until the target child projection is reviewed.
- **Settlement:** Move conversion and installation declarations, evidence, and implementation beneath the Codex custom-agent surface.

## Parked scope

| Concern                            | Re-entry condition                                                                                                                                                         |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Native six-kind suffixes**       | Spec Tree tooling supports suffix admission, authoring, validation, contextualization, status projection, evidence discovery, rendering, and refactoring for all six kinds |
| **Claude Code subagent structure** | The `spx/68-coding-agents.enabler` child projection passes kind, containment, dependency-evidence, and context-visibility gates                                            |
| **Codex custom-agent structure**   | The `spx/68-coding-agents.enabler` child projection passes kind, containment, dependency-evidence, and context-visibility gates                                            |
| **Runtime model and effort**       | The configured-agent task-profile PDR is authored, audited, and aligned with its first semantic consumer specs                                                             |
| **Product-root semantic refactor** | A product-root projection classifies the remaining current root inventory into the six target kinds                                                                        |

## Verification route

For the configured-agent identity mapping and instruction-template changes described in [Active scope](#active-scope):

1. Format every changed Markdown file with `just fmt`.
2. Run the selected deterministic gate with `just check` on a clean committed head.
3. Audit the changed node specs through isolated spec-auditor agents and audit the configured-agent mapping evidence through the test-evidence-auditor agent.
4. Audit the changed instruction template through the skill-auditor agent and the committed changeset through the implementation-auditor agent.
5. Review the clean committed changeset through the changes-reviewer agent.
6. Run `just check-full` after the agentic gates converge because the slice changes generated catalog output and distribution build machinery.
7. Route the changeset through `/merge`.
