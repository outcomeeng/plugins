---
name: author-change
description: >-
  ALWAYS invoke this skill when creating, interviewing, or revising an Outcome
  Engineering Change record. NEVER use it to author a spec or review a code changeset.
argument-hint: "<local Change path and intent | existing Change reference and revision>"
allowed-tools: Read, Write, Edit, Grep, Glob, Skill, Agent, Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue create:*), Bash(gh issue edit:*), Bash(gh project field-list:*), Bash(gh project item-list:*), Bash(gh project item-add:*), Bash(gh project item-edit:*), Bash(spx change draft create:*), Bash(spx change draft list:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run render:*), Bash(printf:*)
---

<objective>
A request routed to local creation or revision of one Change, independently audited before publication at its established maturity.
</objective>

<essential_principles>

Invoke `spec-tree:change-standards` through the skill-composition surface before applying record rules. Load `spx/local/coordination.md` when present for the Change store, Product, project, and field mapping. Read only the selected Change, necessary relationships, and repository references; establish normal foundation and node context before reading product content.

Keep operator judgment in the main conversation. Delegate judgment of the authored record to the configured `change-auditor` role in a separate verifier session. NEVER invoke `audit-change` as an in-conversation replacement for that role.

The scope is one Change. Preserve an explicitly selected local working file inside the Product repository. Otherwise use `<local_draft>` to obtain an SPX-managed file. Preserve an existing file until its identity and revision authority are established. The working document is the authored artifact; SPX retains its complete contents as verification input without a separate payload file.

Handle missing store configuration or ambiguous target identity before any external write. Never infer claim authority from access to the store. An existing holder's claim must be respected. A local draft grants no remote claim. Drafting and repair write only the selected local file; publication occurs after the audit gate passes.

</essential_principles>

<local_draft>

Run from the selected Product repository. For a new working file, send the complete candidate as literal text to `spx change draft create --input stdin`. Consume the returned `draftId`, absolute `path`, and normalized `relativePath`; never construct a storage path or identifier. Resolve the selected Product repository and returned absolute path before editing, and require path-component containment of the returned path inside that repository. When the returned path resolves outside the selected repository, obtain destination-specific confirmation naming that exact absolute path before writing it. Edit the confirmed returned file directly for every refinement round. SPX owns storage and treats the document as opaque text; the shared standards own its metadata and Markdown format.

For resumption without an exact path, use `spx change draft list` to locate existing draft descriptors. Inspect only candidates needed to resolve identity. An ambiguous match requires one plain-text question; never overwrite or create a competing draft by assumption. Keep a selected file through audit, publication, interruption, and handoff. Do not automatically delete local work after publication.

Send content as data through stdin, using a quoted heredoc delimiter absent from the document or the tool's literal stdin facility. Never interpolate document text into executable shell syntax. A failed draft operation preserves its diagnostic and stops dependent work; never substitute a hand-created storage directory.

</local_draft>

<intake>

Read `$ARGUMENTS` as the complete request. When empty, use an unambiguous active request from the conversation; otherwise ask one plain-text question for the Change or intended Output and wait.

For a request already identifying creation or revision, route directly and apply `<triage>` before asking refinement questions. A problem without a chosen Output enters creation. For ambiguous Change identity, ask which Change the operator means. Never treat an unanswered question as agreement. Route requests to author Decisions or specs to `/author`, code implementation to `/apply`, and Handoff-only work to `/handoff`.

</intake>

<triage>

First identify what the request changes, the intended Output, and any consequential choices it leaves open. Inspect the relevant governing Decisions, specs, and affected references before asking the operator to resolve a choice. Reuse explicit answers from the request and existing Change; never ask for a generic problem statement, beneficiaries, or business value merely to fill the template.

| Request state                                  | Refinement                                                                                                                                                                                                   |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Output clear; consequential choices resolved   | Draft or revise directly without an interview. A precise internal file rename needs its affected references and constraints checked, not a beneficiary interview.                                            |
| Output clear; consequential choices unresolved | Invoke `/interview` only for choices that repository truth and supplied intent cannot settle. A public CLI rename can require a compatibility decision despite its small edit size.                          |
| Problem described; Output unchosen             | Invoke `/interview` to help formulate a proposed Output. Pause for the operator when proceeding requires prioritizing competing outcomes or deciding whether to pursue the work. Discovery owns that choice. |

Select questions by the unresolved choice: scope, compatibility, failure behavior, dependencies, required evidence, or operation such as rollout, recovery, monitoring, and resource limits. Ask in plain text, one at a time, explain the consequences, and wait for the answer. Do not reopen a resolved choice or treat silence as a decision. The template is an output format, never a questionnaire.

Triage controls refinement depth only. Preserve maturity requirements, operator attestation, independent verification, and publication authority on every route. A clear execution request does not by itself attest an unwritten Frame. Revisit triage when investigation exposes a consequential choice. Keep resulting specifications in the Change and its governing artifacts. Reusable investigation and rejected alternatives belong in knowledge when separately requested; NEVER require a runtime knowledge-bundle read or automatically write back to a knowledge bundle.

</triage>

<routing>

| Request                                         | Workflow                                         |
| ----------------------------------------------- | ------------------------------------------------ |
| Create a Change from an Output or problem       | `${CLAUDE_SKILL_DIR}/workflows/create-change.md` |
| Interview, refine, or revise an existing Change | `${CLAUDE_SKILL_DIR}/workflows/revise-change.md` |

Read the selected workflow completely. Both workflows use `${CLAUDE_SKILL_DIR}/templates/change.md` and return here for the shared audit gate.

</routing>

<audit_gate>

1. Stabilize the complete local candidate against the shared standards. Resolve contradictions across metadata and body, remove template guidance, and read the file back before requesting audit. Its metadata identifies the maturity being judged. Keep the remote record unchanged throughout local iteration.
2. Dispatch `spec-tree:change-auditor` through the native subagent capability with only the candidate's normalized repository-relative file path. Start without authoring history; the verifier independently reads the candidate's metadata, body, and governing references. Preserve the returned handle. SPX records the local file as the audit subject. If the role or its supported SPX recording contract is unavailable, report the exact failure and stop publication; never substitute another artifact classification, an in-conversation verdict, or a GitHub audit comment.
3. While verification runs, inspect still-unchecked relationships and continuation hazards in the current work. Preserve the candidate under audit unchanged. Collect the required final result through the native result-collection capability.
4. Inspect the returned SPX run token, retained input, and rendered projection. Only a complete `terminalStatus: approved` result over this file's unchanged metadata and body at the requested maturity passes. Any local edit invalidates that approval. After approval, proceed directly to publication; do not ask for a second confirmation of publication already authorized by this workflow.
5. For a completed rejection, inspect the cited rule and sweep the entire candidate for the same defect class. Batch repairs in the local file, re-read affected sections together, and obtain a new independent audit. Ask the operator in plain text when a repair reopens judgment; preserve the question until answered. A failed launch or unusable result stops the invocation with its exact diagnostic; never retry, substitute another verifier, or issue a replacement verdict. Preserve the local candidate when the gate remains blocked.
6. Stop after three consecutive rejected, unknown, or blocked results at this gate. Report the latest failure, the defect-class sweep, and why the repairs did not resolve it. Ask one plain-text question for the needed decision. NEVER advance maturity or claim the audit passed to end the loop.

Keep audit results in SPX and the current conversation. Update Change content only with the resulting refinement. Do not persist audit bookkeeping in its body or comments.

</audit_gate>

<publication>

Publication requires the unchanged local file's passing audit and the authority for its content and maturity. For a new Change, recheck duplicate identity before creation. For revision, compare the current remote body, native metadata, and holder with the version imported into the local file. Reconcile intervening edits locally and re-audit any changed candidate before publication. If the configured store cannot protect an update from concurrent writes, establish exclusive revision authority before writing; unresolved ownership blocks publication.

Use the configured store's native operations to create or update exactly one approved Change. Resolve actual field identifiers and option identifiers before mutation; never hardcode organization, repository, project, Product, or field IDs. On GitHub, map `title` to the issue title and `product`, `maturity`, and `lifecycle` to native project fields. Use `change_ref` only to select an existing issue. Retain immutable `refined_from` in a YAML metadata header at the start of the published issue body. Publish the Markdown body beginning at `# Output` after that retained metadata. Keep the mapped metadata and `change_ref` out of the issue body. Read the body, retained `refined_from`, and native fields back and compare them with the approved candidate. If a multi-step write fails, retain the local file and returned canonical reference, report the successful writes and remaining failed operation, and resume from observed state without creating a duplicate Change or publishing an unaudited revision.

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

<failure_modes>

**A Change omitted specifications settled in conversation.** Claude treated a record and a Handoff as sufficient while a fresh holder still needed the earlier discussion to identify the work. Check the complete Change against the shared continuation rule before audit; put durable intent in the Change and keep transient execution facts in the Handoff.

</failure_modes>

<success_criteria>

- The selected workflow produces exactly one coherent Change in the configured store.
- Its current content meets the shared standards at its declared maturity and retains operator-approved constraints.
- Triage selects direct drafting when consequential choices are resolved; interviews address only unresolved operator-owned choices and never manufacture value claims for routine maintenance.
- Drafting and every repair stay in one local working file. An independent SPX audit approves that unchanged file before publication; missing or unsuccessful verification blocks every candidate publication.
- Publication is confirmed by reading back the body, retained immutable lineage, and native metadata, with no duplicate record or verification bookkeeping added to the Change.
- Continuation depends only on the Change, repository references, and applicable Handoff.

</success_criteria>
