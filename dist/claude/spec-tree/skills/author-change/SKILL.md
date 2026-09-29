---
name: author-change
description: >-
  ALWAYS invoke this skill when creating, interviewing, or revising an Outcome
  Engineering Change record. NEVER use it to author a spec or review a code
  changeset.
argument-hint: "<local Change path and intent | existing Change reference and revision>"
allowed-tools: Read, Write, Edit, Grep, Glob, Skill, Agent, Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue create:*), Bash(gh issue edit:*), Bash(gh api graphql:*), Bash(gh api repos/*/issues/*:*), Bash(spx change draft create:*), Bash(spx change draft list:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run render:*), Bash(printf:*)
---

<objective>
A complete store-independent Change record authored locally, independently approved at its declared Maturity, persisted through the configured store, and read back equal.
</objective>

<essential_principles>

- Operate on one Change. Resolve new-versus-existing identity and the requested target Maturity before routing.
- Use skill `spec-tree:change-standards`. Invoke it with exactly the target Maturity. It loads the common contract and only that Maturity's cumulative Definition of Ready.
- Load `spx/local/coordination.md` when present for the Change store and Product. Store coordinates and revision selectors remain outside the record.
- Preserve an explicitly selected local working file inside the Product repository. Otherwise use `<local_draft>` to obtain an SPX-managed file. Every refinement and repair changes that one file.
- Keep provider conversations, transcripts, prompt copies, and received conversation input out of the Change record. Preserve established intent in Output, Value, Frame, and Activities.
- Ask only about a consequential operator-owned choice that supplied intent and repository truth leave unresolved. Ask one focused question at a time and state how its answer changes the record.
- Require the operator's attestation as input to `Framed`. When the operator is reachable, obtain it through the structured question. Otherwise stop with `attestation-required`, naming the exact judgment the operator must attest. Dispatch the configured `change-auditor` in an isolated verifier session after the candidate stabilizes. NEVER replace it with an in-conversation audit.
- Keep remote content unchanged until the complete local candidate passes audit. A local draft grants no remote claim or integration authority.

</essential_principles>

<local_draft>

Run from the selected Product repository. For a new file, send the complete candidate as literal stdin to `spx change draft create --input stdin`. Consume the returned `draftId`, absolute `path`, and normalized `relativePath`; never construct a storage path or identifier. Require path-component containment inside the selected repository before editing. A returned path outside it requires destination-specific operator authority naming the absolute path.

For resumption without an exact path, use `spx change draft list` and inspect only the descriptors needed to identify the candidate. An ambiguous match requires a focused identity question. Preserve an existing candidate until its relationship to the selected store record is established. Do not delete a draft automatically after publication.

Send record content as data through a quoted heredoc delimiter absent from the record or the harness's literal stdin facility. A programmatic one-line runner uses one physical `printf '%s\n' '<safely-quoted-content>' | <command>` line. NEVER interpolate record content into executable shell syntax or create a temporary payload file.

</local_draft>

<intake_and_triage>

Read `$ARGUMENTS` as the complete request. When it is empty, use one unambiguous active request from the conversation; otherwise ask for the intended Output or exact Change identity and wait.

Resolve these facts before routing:

1. New root, new successor, or revision of one existing Change. For a successor, resolve the complete predecessor set before drafting. For a revision, retain the canonical store reference outside the record.
2. Target Maturity: `Proposed`, `Framed`, `Sliced`, or `Executable`.
3. Intended Output and the established reason it is worth Build refinement.
4. Consequential choices still open after reading governing Decisions, specs, affected references, predecessor Changes, blockers, and the current record.

Draft directly when the Output is clear and consequential choices are resolved. Use skill `spec-tree:interview`. Invoke it only for unresolved scope, compatibility, failure behavior, dependency, evidence, rollout, recovery, monitoring, or resource-limit choices that change the Output or Frame. A problem with no chosen Output returns to operator judgment in discovery. The template supplies output shape and never acts as a questionnaire.

Never reopen a settled choice, infer silence as agreement, or demand beneficiaries, business value, research, or alternatives for a precise maintenance Change. Re-run triage when investigation exposes a new consequential choice.

</intake_and_triage>

<routing>

| Target Maturity | Workflow                                      |
| --------------- | --------------------------------------------- |
| `Proposed`      | `${CLAUDE_SKILL_DIR}/workflows/proposed.md`   |
| `Framed`        | `${CLAUDE_SKILL_DIR}/workflows/framed.md`     |
| `Sliced`        | `${CLAUDE_SKILL_DIR}/workflows/sliced.md`     |
| `Executable`    | `${CLAUDE_SKILL_DIR}/workflows/executable.md` |

Read exactly one maturity workflow and `${CLAUDE_SKILL_DIR}/templates/change.md`. The workflow handles both creation and revision at that level. A current record at a different Maturity is input to the selected workflow; its target Maturity controls the one Definition of Ready loaded.

</routing>

<revision_safety>

For an existing Change, read its complete current body, each field from its store home, holder, predecessor and blocker records needed for the revision, and latest Handoff when resuming execution. Import it into the selected draft once, composing the front matter from each field's home above the body. Preserve `refined_from` byte-for-byte unless creating a new successor; revisions never change it. Retain the inspected remote representation outside the record for the publication concurrency check.

A claim held by another holder blocks takeover. Terminal Lifecycle blocks ordinary resumption. A split or coalescence creates successor Changes as the Sliced workflow states and never rewrites an existing Change's `refined_from`. A Claimed holder writes a Handoff and releases the Change before lowering Maturity. Reconcile an existing local candidate with the store representation before overwriting either.

</revision_safety>

<audit_gate>

1. Stabilize and read back the complete local candidate. Inventory all six front-matter keys first, then all four ordered top-level body sections. Resolve contradictions and remove template guidance.
2. Dispatch `spec-tree:change-auditor` once through the native subagent capability with only the normalized repository-relative candidate path. Start without authoring history or a suggested verdict.
3. Preserve the candidate unchanged while the audit runs. Collect the same invocation until it returns one result: the `finish` result object, `OUTSIDE_CONTRACT`, or `BLOCKED`.
4. Judge a `finish` result from its own fields. Approval requires `run.terminalStatus: approved`, `run.sealed: true`, `run.findingCount: 0`, an empty `findings` array, and a `renderCommand` whose `--scope` equals the dispatched candidate path and whose `--run` equals `runToken`. `run.terminalStatus: rejected` is a completed rejection whose `findings` payloads are the repair input and needs no projection. An `OUTSIDE_CONTRACT` result, `BLOCKED` diagnostic, failed launch, or result missing any of these fields withholds publication.
5. Before accepting an approval, establish coverage and retained-input equality from the sealed run. Run each command below once from the repository root and read its stdout directly; NEVER redirect it to a file.
   - Run `renderCommand` exactly as the result names it. Require every run-level field of the rendered projection to equal the result's `run`, and require `auditScopeUnits` to hold exactly one root unit with no `parentUnitId` whose `subject` is the candidate path, plus one child naming that root for each common rule and each declared-Maturity Definition of Ready criterion that `spec-tree:change-standards` loads, each `audited` or `not-applicable`.
   - Run `spx verification run input` with the `--verification-type`, `--scope-type`, `--scope`, and `--run` values `renderCommand` carries. Require its `content` to equal the unchanged candidate byte for byte; the rendered projection carries no retained input.

   A failed command or any mismatch withholds publication.
6. For a completed rejection, sweep the complete candidate for the cited defect class, batch repairs, read affected sections together, and dispatch a new audit only after the repaired candidate stabilizes. Ask the operator when repair reopens judgment. Stop after three consecutive completed non-approvals at this gate and report the outstanding class.

Audit results remain in SPX and the conversation. NEVER write audit bookkeeping into the Change body, comments, or fields.

</audit_gate>

<persistence>

Publication requires unchanged local content approved by `<audit_gate>`, content authority for the target Maturity, and revision authority for an existing store record. Re-read the remote representation immediately before mutation and reconcile any intervening edit locally; re-audit a changed candidate.

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle` for the store rules: `store-binding` resolves the store and blocks an absent overlay or a store of another kind, `canonical-state` names each field's home and the commands that read and write it, and `inert-stdin` and `write-inspection` govern every text sent to the store. Use `gh` only, and resolve the issue, field, option, and blocker ids from live reads; hardcode none of them. Each front-matter field has one home, and nothing else in the store holds it:

| Record field   | Home in the store                                                                                                     |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| `title`        | The issue title                                                                                                       |
| `product`      | The issue field `Product`                                                                                             |
| `maturity`     | The issue field `Maturity`                                                                                            |
| `lifecycle`    | The issue field `Lifecycle`                                                                                           |
| `refined_from` | The text issue field `Predecessors`: the identities in order, separated by a comma and one space; no value for a root |
| `blocked_by`   | The issue's native dependencies                                                                                       |

The issue body is the approved local file from its `# Output` line to its end. Write in this order, recording each successful write:

1. Create the issue with `gh issue create --repo <store> --title '<title>' --body-file -`, or update it with `gh issue edit <N> --repo <store> --title '<title>' --body-file -`, the body on stdin.
2. Write `Product`, `Maturity`, and `Lifecycle` through the single-select write under `canonical-state`. For a new successor, write `Predecessors` through the text write. A revision never writes `Predecessors`; it requires the stored value to equal `refined_from` already.
3. Read the native blockers with `gh api repos/<store>/issues/<N>/dependencies/blocked_by`. Add each missing blocker with `gh api repos/<store>/issues/<N>/dependencies/blocked_by --method POST -F issue_id=<id>`, and remove each extra one with `gh api repos/<store>/issues/<N>/dependencies/blocked_by/<id> --method DELETE`, where `<id>` is the blocker's numeric id from `gh api repos/<owner>/<repo>/issues/<M> --jq .id`.

NEVER write front matter, a lineage line, or a `# Relationships` section into the body, write a field into a project, or publish a draft iteration.

After all writes, read the issue with `gh issue view <N> --repo <store> --json title,body,number,url`, its fields under `canonical-state`, and its blockers. Require:

- the issue title equals `title`;
- the issue body equals the approved local file from its `# Output` line;
- `Product`, `Maturity`, and `Lifecycle` equal `product`, `maturity`, and `lifecycle`;
- `Predecessors`, split at every comma followed by one space, equals `refined_from` in order, and carries no value for a root;
- the native blockers, as canonical identities, equal the set `blocked_by` names.

Any mismatch or partial write is a failed persistence result. Preserve the local file and canonical issue reference, report successful writes and the exact failed or unequal field, and resume from observed state without creating a duplicate or publishing unaudited content. Authentication failures stop without printing credentials.

</persistence>

<result>

Return the canonical Change reference, exact persisted Maturity and Lifecycle, whether the operation created or revised the Change, the equality result for every front-matter field, and the next Activity or unresolved operator question. Use skill `spec-tree:release-change`. Invoke it only when this session holds the Change (Lifecycle `Claimed`, with the winning Claim naming this session's assigned worktree root) and work stops or transfers with continuation remaining; a Change this session does not hold needs no release. Preserve any unaudited local candidate locally and leave the published Change unchanged.

</result>

<reference_index>

- `spec-tree:change-standards`: common record contract plus exactly one cumulative Definition of Ready.
- `${CLAUDE_SKILL_DIR}/templates/change.md`: store-independent six-field, four-section record template.

</reference_index>

<workflows_index>

- `${CLAUDE_SKILL_DIR}/workflows/proposed.md`
- `${CLAUDE_SKILL_DIR}/workflows/framed.md`
- `${CLAUDE_SKILL_DIR}/workflows/sliced.md`
- `${CLAUDE_SKILL_DIR}/workflows/executable.md`

</workflows_index>

<failure_modes>

**Conversation text entered the Change.** Claude copied received instructions into an Input section to preserve context. The record then depended on provider conversation and violated the methodology boundary. Preserve the proposal in Output and Value, and keep conversation text in provider context and store history.

**A field lived in two homes.** Claude published the front matter in the issue body and also set the issue fields, and left lineage as a body line. A Lifecycle skill later wrote only the field, so the two copies disagreed and readers took whichever they found first. Each field has one home in the store; the body starts at `# Output`.

</failure_modes>

<success_criteria>

- Exactly one local candidate and one configured-store Change represent the intended Output.
- The candidate satisfies the one cumulative Definition of Ready loaded for its declared Maturity and carries the required authority.
- Triage asks only questions whose answers change Output, Frame, Maturity, risk, or ownership.
- The complete unchanged record receives an independent approved audit before publication.
- Every front-matter field reads back equal from its one store home, and the issue body equals the approved file from its `# Output` line.
- The record contains no store-specific key, received conversation input, audit bookkeeping, or authoritative body restatement of front matter.
- Continuation depends only on the Change, repository references, and applicable Handoff.

</success_criteria>
