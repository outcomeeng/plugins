---
name: author-change
description: >-
  ALWAYS invoke this skill when creating, refining, or revising an Outcome
  Engineering Change record, or when turning a request into one. NEVER use it
  to author a spec or review a code changeset.
argument-hint: "<local Change path and intent | existing Change reference and revision>"
allowed-tools: Read, Write, Edit, Grep, Glob, collaboration.spawn_agent, collaboration.wait_agent, Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue create:*), Bash(gh issue edit:*), Bash(gh api graphql:*), Bash(gh api repos/*/issues/*/dependencies/blocked_by:*), Bash(gh api repos/*/issues/*/dependencies/blocked_by/*:*), Bash(gh api repos/*/issues/* --jq .id), Bash(spx change draft create:*), Bash(spx change draft list:*), Bash(spx verification run input:*), Bash(spx verification run render:*), Bash(printf:*), request_user_input
---

<objective>
A complete store-independent Change record in the Intent form, authored locally, independently approved at its declared Maturity, persisted through the configured store, and read back equal, or the successor Changes and the `Refined` sources of a split or coalescence under the Sliced workflow; or the `authority-required` result, which leaves the candidate and the store record unchanged.
</objective>

<essential_principles>

- Operate on one Change, except in the Sliced workflow's split or coalescence, which claims its source Changes and authors their successors. Resolve new-versus-existing identity and the requested target Maturity before routing.
- Use skill `spec-tree:change-standards` once per purpose. Invoke it with exactly the target Maturity for drafting and the audit gate; it loads the common record contract and only that Maturity's cumulative Definition of Ready. Invoke it with `Lifecycle` for revision safety, the authority gate, and persistence; it loads the Lifecycle rules. The one-Maturity rule governs the Definitions of Ready alone.
- Load `spx/local/coordination.md` when present for the Change store and Product. Store coordinates and revision selectors remain outside the record.
- Preserve an explicitly selected local working file inside the Product repository. Otherwise use `<local_draft>` to obtain an SPX-managed file. Every refinement and repair changes that one file.
- Keep provider conversations, transcripts, prompt copies, and received conversation input out of the Change record. Preserve established intent in the Intent and the sections the Maturity adds.
- Ask only about a consequential operator-owned choice that supplied intent and repository truth leave unresolved. Ask one focused question at a time through the structured-question tool and state how its answer changes the record.
- Write no body authority line, as `body-authority` requires. The store's field-change events and confirmation comments carry every authority event; advance Maturity only under `<authority_gate>`.
- Audit every stabilized candidate under `<audit_gate>` before publication.
- Keep remote content unchanged until the complete local candidate passes audit, except the Maturity lowering `<revision_safety>` states. A local draft grants no remote claim or integration authority.

</essential_principles>

<local_draft>

Run from the selected Product repository. For a new file, send the complete candidate as literal stdin to `spx change draft create --input stdin`. Consume the returned `draftId`, absolute `path`, and normalized `relativePath`; never construct a storage path or identifier. Require path-component containment inside the selected repository before editing. A returned path outside it requires destination-specific operator authority naming the absolute path.

For resumption without an exact path, use `spx change draft list` and inspect only the descriptors needed to identify the candidate. An ambiguous match requires a focused identity question. Preserve an existing candidate until its relationship to the selected store record is established. NEVER delete a draft automatically after publication.

Send record content as data through a quoted heredoc delimiter absent from the record or the harness's literal stdin facility. A programmatic one-line runner uses one physical `printf '%s\n' '<safely-quoted-content>' | <command>` line. NEVER interpolate record content into executable shell syntax or create a temporary payload file; the exceptions are the single-quoted arguments `inert-stdin` admits: the `--title` that `<persistence>` writes and the search argument of the Proposed workflow's store search.

</local_draft>

<intake_and_triage>

Read `$ARGUMENTS` as the complete request. When it is empty, use one unambiguous active request from the conversation; otherwise ask for the intended Output or exact Change identity and wait.

Resolve these facts before routing:

1. New root, new successor, or revision of one existing Change. For a successor, resolve the complete predecessor set before drafting. For a revision, retain the canonical store reference outside the record.
2. Target Maturity: `Proposed`, `Framed`, `Sliced`, or `Executable`.
3. Intended Output and the established reason it is worth refinement.
4. Consequential choices still open after reading governing Decisions, specs, affected references, predecessor Changes, blockers, and the current record.

Draft directly when the Output is clear and consequential choices are resolved. Use skill `spec-tree:interview`. Invoke it only for unresolved scope, compatibility, failure behavior, dependency, evidence, rollout, recovery, monitoring, or resource-limit choices that change the Output or its Decisions. A problem with no chosen Output returns to operator judgment in discovery. The template supplies output shape and never acts as a questionnaire.

Never reopen a settled choice, infer silence as agreement, or demand beneficiaries, business value, research, or alternatives for a precise maintenance Change. Re-run triage when investigation exposes a new consequential choice.

</intake_and_triage>

<routing>

| Target Maturity | Workflow                               |
| --------------- | -------------------------------------- |
| `Proposed`      | `${SKILL_DIR}/workflows/proposed.md`   |
| `Framed`        | `${SKILL_DIR}/workflows/framed.md`     |
| `Sliced`        | `${SKILL_DIR}/workflows/sliced.md`     |
| `Executable`    | `${SKILL_DIR}/workflows/executable.md` |

Read exactly one maturity workflow and `${SKILL_DIR}/templates/change.md`. The workflow handles both creation and revision at that level. A current record at a different Maturity is input to the selected workflow; its target Maturity controls the one Definition of Ready loaded.

</routing>

<revision_safety>

For an existing Change, read its complete current body, each field from its store home, holder, predecessor and blocker records needed for the revision, and latest Handoff when resuming execution. Import it into the selected draft once, composing the front matter from each field's home above the body. Preserve `refined_from` byte-for-byte unless creating a new successor; revisions never change it. Retain the inspected remote representation outside the record for the publication concurrency check.

A claim held by another holder blocks takeover. Terminal Lifecycle blocks ordinary resumption. A split or coalescence creates successor Changes as the Sliced workflow states and never rewrites an existing Change's `refined_from`. A published record whose body opens with `# Output` takes the Intent form at this revision under `compatibility-boundary`: author the new record from the proposal it carries, and never convert the old body in place. Reconcile an existing local candidate with the store representation before overwriting either.

Maturity moves backward only under `maturity-and-authority`. A Claimed holder writes a Handoff and releases the Change before lowering Maturity. When the newest move out of `Submitted` carries a `Rejection:` naming `Framed` or `Sliced` and `Maturity` still holds that level, lower it one level before any further refinement: Use skill `spec-tree:change-standards`, invoke it with `Lifecycle`, and write the lower value through the single-select write under `canonical-state`; a rejection at `Proposed` leaves `Proposed` without the priority decision.

</revision_safety>

<authority_gate>

Maturity advances past `Proposed`, `Framed`, and `Sliced` only when the store shows the Product's Maintainer's move of the Change out of `Submitted` at the Maturity it leaves. A new Change is persisted at `Proposed`; a drafting or execution request supplies no authority.

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`, which `<persistence>` also loads. Read the authority for the Maturity the Change currently holds under `authority-read`, and report each authority found with its actor, time, and deciding comment lines verbatim. When the store shows none, stop with `authority-required`, naming that Maturity and the move the store lacks. Leave the candidate and the store record unchanged. A body line never stands in for the move.

The Refiner persists the record at the Maturity it reached. This skill never writes `Submitted` itself: its `<result>` composes `/release-change` with its `submit` result for the session that holds the Change at `Proposed`, `Framed`, or `Sliced`, and that skill writes `Submitted` after this skill persists the record. Persisting never claims a Change: a new Change is persisted `Available` and stays unsubmitted until a session claims it, and a revision keeps the Lifecycle the store holds. Only the Sliced workflow claims Changes, the sources it splits or coalesces. The Product's Maintainer's confirmation or rejection ends `Submitted` as `confirmation-record` states; an `Executable` record is never submitted.

</authority_gate>

<audit_gate>

1. Stabilize and read back the complete local candidate. Inventory all six front-matter keys first, then the body's level-two sections against `record-shape`. Resolve contradictions and remove template guidance.
2. Dispatch `spec-tree_change-auditor` once through the native subagent capability with only the normalized repository-relative candidate path. Start without authoring history or a suggested verdict. NEVER replace the dispatch with an in-conversation audit.
3. Preserve the candidate unchanged while the audit runs. Collect the same invocation until it returns one result: the `finish` result object, `OUTSIDE_CONTRACT`, or `BLOCKED`.
4. Judge a `finish` result from its own fields. Approval requires `run.terminalStatus: approved`, `run.sealed: true`, `run.findingCount: 0`, an empty `findings` array, and a `renderCommand` whose `--scope` equals the dispatched candidate path and whose `--run` equals `runToken`. `run.terminalStatus: rejected` is a completed rejection whose `findings` payloads are the repair input and needs no projection, with one exception: a sealed rejected run whose `findings` array is non-empty, holds no `blocking` finding, and carries every finding at severity `debt` is a debt-only rejection of a revision. Treat it as an approval for publication, subject to step 5, and count it toward neither step 6's two dispatches nor the rejections that end the gate; every other rejection stays a rejection. An `OUTSIDE_CONTRACT` result, `BLOCKED` diagnostic, failed launch, or result missing any of these fields withholds publication.
5. Before accepting an approval or a debt-only rejection, establish coverage and retained-input equality from the sealed run. Run each command below once from the repository root and read its stdout directly; NEVER redirect it to a file.
   - Run `renderCommand` exactly as the result names it. Require every run-level field of the rendered projection to equal the result's `run`, and require `auditScopeUnits` to hold exactly one root unit with no `parentUnitId` whose `subject` is the candidate path, plus one child naming that root for each common rule and each declared-Maturity Definition of Ready criterion that `spec-tree:change-standards` loads, each `audited` or `not-applicable`.
   - Run `spx verification run input` with the `--verification-type`, `--scope-type`, `--scope`, and `--run` values `renderCommand` carries. Require its `content` to equal the unchanged candidate byte for byte; the rendered projection carries no retained input.

   A failed command or any mismatch withholds publication.
6. Dispatch the auditor at most twice on one candidate, counting every dispatch this gate makes for it, the re-audit `<persistence>` requires included. After a first completed rejection, sweep the complete candidate for the cited defect class, batch repairs, read affected sections together, and dispatch the second audit only after the repaired candidate stabilizes. Ask the operator when repair reopens judgment. After the second rejection, end with publication withheld and report the outstanding defect class; NEVER dispatch a third audit on that candidate. When the `<persistence>` re-read changes the candidate after the second dispatch, withhold publication and report the intervening edit and the outstanding state.

Audit results remain in SPX and the conversation. NEVER write audit bookkeeping into the Change body, comments, or fields.

</audit_gate>

<persistence>

Publication requires unchanged local content approved by `<audit_gate>`, the authority `<authority_gate>` names for the target Maturity, and revision authority for an existing store record. Re-read the remote representation immediately before mutation and reconcile any intervening edit locally; re-audit a changed candidate only while step 6 of `<audit_gate>` leaves a dispatch.

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle` for the store rules: `store-binding` resolves the store and blocks an absent overlay or a store of another kind, `canonical-state` names each front-matter field's one home, the commands that read and write each field, and the bounded blocker read, and `inert-stdin` and `write-inspection` govern every text sent to the store. Use `gh` only, and resolve the issue, field, option, and blocker ids from live reads; hardcode none of them. Nothing else in the store holds a field that `canonical-state` assigns a home.

The issue body is the approved local file from its `## Intent` line to its end. Write in this order, recording each successful write:

1. Create the issue with `gh issue create --repo <store> --title '<title>' --body-file -`, or update it with `gh issue edit <N> --repo <store> --title '<title>' --body-file -`, the body on stdin and the title as the one single-quoted argument `inert-stdin` states, a literal apostrophe written as `'"'"'`.
2. Write `Product`, `Maturity`, and `Lifecycle` through the single-select write under `canonical-state`. For a new successor, write `Predecessors` through the text write. A revision never writes `Predecessors`; it requires the stored value to equal `refined_from` already.
3. Read the native blockers under `canonical-state`; a blocked read stops the persistence before any blocker write. Add each missing blocker with `gh api repos/<store>/issues/<N>/dependencies/blocked_by --method POST -F issue_id=<id>`, and remove each extra one with `gh api repos/<store>/issues/<N>/dependencies/blocked_by/<id> --method DELETE`, where `<id>` is the blocker's numeric id from `gh api repos/<owner>/<repo>/issues/<M> --jq .id`.

NEVER write front matter, a lineage line, or a `# Relationships` section into the body, write a field into a project, or publish a draft iteration.

After all writes, read the issue with `gh issue view <N> --repo <store> --json title,body,number,url`, its fields under `canonical-state`, and its blockers under `canonical-state`. Require:

- the issue title equals `title`;
- the issue body equals the approved local file from its `## Intent` line;
- `Product`, `Maturity`, and `Lifecycle` equal `product`, `maturity`, and `lifecycle`;
- `Predecessors`, split at every comma followed by one space, equals `refined_from` in order, and carries no value for a root;
- the native blockers, as canonical identities, equal the set `blocked_by` names.

Any mismatch or partial write is a failed persistence result. Preserve the local file and canonical issue reference, report successful writes and the exact failed or unequal field, and resume from observed state without creating a duplicate or publishing unaudited content. Authentication failures stop without printing credentials.

</persistence>

<result>

Return the canonical Change reference, exact persisted Maturity and Lifecycle, whether the operation created or revised the Change, the equality result for every front-matter field, and the next Activity or unresolved operator question. A stop at `<authority_gate>` returns the result `authority-required` instead, naming the Maturity the Change holds and the move the store lacks.

Use skill `spec-tree:release-change`. Invoke it only when this session holds the Change (Lifecycle `Claimed`, with the winning Claim naming this session's assigned worktree root) and work stops or transfers with continuation remaining; a Change this session does not hold needs no release. Invoke it with `submit` when the persisted record is at `Proposed`, `Framed`, or `Sliced` and waits for the Product's Maintainer's confirmation. Preserve any unaudited local candidate locally and leave the published Change unchanged.

</result>

<reference_index>

- `spec-tree:change-standards`: common record contract plus exactly one cumulative Definition of Ready, or the Lifecycle store rules.
- `${SKILL_DIR}/templates/change.md`: store-independent six-field, Intent-form record template.

</reference_index>

<workflows_index>

- `${SKILL_DIR}/workflows/proposed.md`
- `${SKILL_DIR}/workflows/framed.md`
- `${SKILL_DIR}/workflows/sliced.md`
- `${SKILL_DIR}/workflows/executable.md`

</workflows_index>

<failure_modes>

**Conversation text entered the Change.** Claude copied received instructions into an Input section to preserve context. The record then depended on provider conversation and violated the methodology boundary. Preserve the proposal in the Intent, and keep conversation text in provider context and store history.

**A field lived in two homes.** Claude published the front matter in the issue body and also set the issue fields, and left lineage as a body line. A Lifecycle skill later wrote only the field, so the two copies disagreed and readers took whichever they found first. Each field has one home in the store; the body starts at `## Intent`.

**Authority was typed into the body.** Claude wrote an `Intent attestation:` line and an `Accountable person:` line into a record after the operator agreed in conversation. Any writer of the body can type such lines, so they proved nothing and no audit could tell a forged line from a real one. The Product's Maintainer's move out of `Submitted` in the store carries the authority, with its actor and time.

</failure_modes>

<success_criteria>

- Exactly one local candidate and one configured-store Change represent the intended Output, except in a split or coalescence, whose Sliced workflow states its own success criteria.
- An `authority-required` stop left the candidate and the store record unchanged and named the Maturity the Change holds and the move the store lacks.
- The candidate satisfies the one cumulative Definition of Ready loaded for its declared Maturity, and its Maturity above `Proposed` rests on the store's authority for the level it left.
- Triage asks only questions whose answers change the Output, its Decisions, Maturity, risk, or ownership.
- The complete unchanged record receives an independent approved audit before publication.
- Every front-matter field reads back equal from its one store home, and the issue body equals the approved file from its `## Intent` line.
- The record contains no store-specific key, received conversation input, audit bookkeeping, body authority line, or authoritative body restatement of front matter.
- A session with no conversation history resumes from the stored Change, its repository references, and its newest Handoff alone.

</success_criteria>
