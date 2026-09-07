---
name: author-change
description: >-
  ALWAYS invoke this skill when creating, interviewing, or revising an Outcome
  Engineering Change record. NEVER use it to author a spec or review a code changeset.
argument-hint: "<local Change path and intent | existing Change reference and revision>"
allowed-tools: Read, Write, Edit, Grep, Glob, Skill, multi_agent_v1.spawn_agent, multi_agent_v1.wait_agent, multi_agent_v1.close_agent, Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue create:*), Bash(gh issue edit:*), Bash(gh project field-list:*), Bash(gh project item-list:*), Bash(gh project item-add:*), Bash(gh project item-edit:*), Bash(gh api:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run render:*), Bash(printf:*)
---

<objective>
A request routed to local creation or revision of one Change, independently audited before publication at its established maturity.
</objective>

<essential_principles>

Invoke `spec-tree:change-standards` through the skill-composition surface before applying record rules. Load `spx/local/coordination.md` when present for the Change store, Product, project, and field mapping. Read only the selected Change, necessary relationships, and repository references; establish normal foundation and node context before reading product content.

Keep operator judgment in the main conversation. Delegate judgment of the authored record to the configured `change-auditor` role in a separate verifier session. NEVER invoke `audit-change` as an in-conversation replacement for that role.

The scope is one Change. Resolve its local working-file path from the operator's request or the coordination configuration. Use a path inside the Product repository so SPX can select it by normalized repository-relative file scope. If neither supplies a path, ask one plain-text question and wait; never invent a storage directory or a new SPX command. Preserve an existing file until its identity and revision authority are established. This working document is the authored artifact, not a temporary command-payload file.

Handle missing store configuration or ambiguous target identity before any external write. Never infer claim authority from access to the store. An existing holder's claim must be respected. A local draft grants no remote claim. Drafting and repair write only the selected local file; publication occurs after the audit gate passes.

</essential_principles>

<intake>

Read `$ARGUMENTS` as the complete request. When empty, use an unambiguous active request from the conversation; otherwise ask one plain-text question for the Change or intended Output and wait.

For a request already identifying creation or revision, route directly. For ambiguity, ask which Change or Output the operator means. Never treat an unanswered question as agreement. Route requests to author Decisions or specs to `/author`, code implementation to `/apply`, and Handoff-only work to `/handoff`.

</intake>

<routing>

| Request                                         | Workflow                                         |
| ----------------------------------------------- | ------------------------------------------------ |
| Create a Change from an intended Output         | `${CLAUDE_SKILL_DIR}/workflows/create-change.md` |
| Interview, refine, or revise an existing Change | `${CLAUDE_SKILL_DIR}/workflows/revise-change.md` |

Read the selected workflow completely. Both workflows use `${CLAUDE_SKILL_DIR}/templates/change.md` and return here for the shared audit gate.

</routing>

<audit_gate>

1. Stabilize the complete local candidate against the shared standards. Resolve contradictions across metadata and body, remove template guidance, and read the file back before requesting audit. Its metadata identifies the maturity being judged. Keep the remote record unchanged throughout local iteration.
2. Dispatch the configured `change-auditor` with the Product repository, exact repository-relative local file path, candidate maturity, and the request fields its audit contract requires. Preserve the returned handle. SPX records the local file as the audit subject. If the role or its supported SPX recording contract is unavailable, report the exact failure and stop publication; never substitute another artifact classification, an in-conversation verdict, or a GitHub audit comment.
3. While verification runs, inspect still-unchecked relationships and continuation hazards in the current work. Preserve the candidate under audit unchanged. Collect the required final result and close the verifier session.
4. Inspect the returned SPX run token, retained input, and rendered projection. Only a complete `terminalStatus: approved` result over this file's unchanged metadata and body at the requested maturity passes. Any local edit invalidates that approval. After approval, proceed directly to publication; do not ask for a second confirmation of publication already authorized by this workflow.
5. For rejection, inspect the cited rule and sweep the entire candidate for the same defect class. Batch repairs in the local file, re-read affected sections together, and obtain a new independent audit. Ask the operator in plain text when a repair reopens judgment; preserve the question until answered. For a blocked run, repair the reported capability or request failure before redispatch. Preserve the local candidate when the gate remains blocked.
6. Stop after three consecutive rejected, unknown, or blocked results at this gate. Report the latest failure, the defect-class sweep, and why the repairs did not resolve it. Ask one plain-text question for the needed decision. NEVER advance maturity or claim the audit passed to end the loop.

Keep audit results in SPX and the current conversation. Update Change content only with the resulting refinement. Do not persist audit bookkeeping in its body or comments.

</audit_gate>

<publication>

Publication requires the unchanged local file's passing audit and the authority for its content and maturity. For a new Change, recheck duplicate identity before creation. For revision, compare the current remote body, native metadata, and holder with the version imported into the local file. Reconcile intervening edits locally and re-audit any changed candidate before publication. If the configured store cannot protect an update from concurrent writes, establish exclusive revision authority before writing; unresolved ownership blocks publication.

Use the configured store's native operations to create or update exactly one approved Change. Resolve actual field identifiers and option identifiers before mutation; never hardcode organization, repository, project, Product, or field IDs. On GitHub, publish the local Markdown body to the issue and map its metadata to the issue title and native project fields. Keep the local metadata header out of the issue body. Read both body and fields back and compare them with the approved candidate. If a multi-step write fails, retain the local file and returned canonical reference, report the successful writes and remaining failed operation, and resume from observed state without creating a duplicate Change or publishing an unaudited revision.

Treat record content as data when sending it through command input. Never evaluate shell syntax embedded in a Change. Keep publication confined to the selected Change and its configured project item. Authentication failures stop publication without printing credentials.

Return the canonical Change reference, current Maturity and Lifecycle, a concise account of the content revised, and the next Activity or unresolved operator question. When refinement work is ending or being delegated, invoke `/handoff` for the existing Change; that workflow owns claim release and transient continuation. A handoff must preserve an unaudited local candidate locally and leave the published Change content unchanged. Pass the last published record and a pointer to the retained local work, never the candidate body as remotely publishable content. A new draft with no published Change remains a local file when publication is blocked.

</publication>

<reference_index>

- `spec-tree:change-standards`: shared record requirements, explicitly loaded before either route.
- `${CLAUDE_SKILL_DIR}/templates/change.md`: maturity-aware Change body, read by either route.

</reference_index>

<workflows_index>

- `${CLAUDE_SKILL_DIR}/workflows/create-change.md`: one new Change.
- `${CLAUDE_SKILL_DIR}/workflows/revise-change.md`: one existing Change, preserving identity and lineage.

</workflows_index>

<success_criteria>

- The selected workflow produces exactly one coherent Change in the configured store.
- Its current content meets the shared standards at its declared maturity and retains operator-approved constraints.
- Drafting and every repair stay in one local working file. An independent SPX audit approves that unchanged file before publication; missing or unsuccessful verification blocks every candidate publication.
- Publication is confirmed by reading back the body and native metadata, with no duplicate record or verification bookkeeping added to the Change.
- Continuation depends only on the Change, repository references, and applicable Handoff.

</success_criteria>
