---
name: author-change
description: >-
  ALWAYS invoke this skill when recording, refining, publishing, splitting,
  merging, or reframing an Outcome Engineering Change record, or when turning a
  request into one. NEVER use it to author a spec or review a code changeset.
argument-hint: "<record | publish | split | merge | reframe> <intent, Draft path, or #N | owner/repo#N | issue-url>"
allowed-tools: Read, Write, Edit, Grep, Glob, collaboration.spawn_agent, collaboration.wait_agent, Bash(git -C * rev-parse:*), Bash(git rev-parse:*), Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue create:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh api graphql:*), Bash(gh api repos/*/issues/*/dependencies/blocked_by:*), Bash(gh api repos/*/issues/*/dependencies/blocked_by/*:*), Bash(gh api repos/*/issues/* --jq .id), Bash(gh api user --jq .login), Bash(spx change draft create:*), Bash(spx change draft list:*), Bash(python3 "${SKILL_DIR}/scripts/check_form.py":*), Bash(id -un), Bash(hostname -s), Bash(printenv CODEX_THREAD_ID), request_user_input
---

<objective>
One Change record in the declared Change Store, written from a Change Draft that passed the form check and read back equal to it — or the Children of a split, the survivor of a merge, or the reframed record — with the result naming each failed rule, audit finding, or open question.
</objective>

<essential_principles>

- Use skill `product-tree:change-standards`. Its rules govern every Draft and publish by their slugs; read its `references/github-store.md` for every store read and write.
- Read `spx/local/coordination.md` for the Change Store and the Product.
- Every record starts from a Change Draft in the Product's checkout. Keep conversation text, transcripts, and audit bookkeeping out of the Draft under `no-person`.
- Ask only about a choice that changes a Declarations line and that the request, the Product Tree, and the repository leave open, one question at a time through the structured-question tool. Every answer the Operator gives reaches a Declarations line under `operator-answers`. Use skill `product-tree:interview` for an open choice of scope, failure behavior, dependency, evidence, or rollout.
- Make every Transition through `product-tree:manage-change`; this skill writes no Maturity or Lifecycle after recording.

</essential_principles>

<draft>

For a new Change, write the Draft from `${SKILL_DIR}/templates/leaf.md`, or `${SKILL_DIR}/templates/parent.md` for a Parent, to a payload file in the scratch directory the harness names for the session, and retain it with `spx change draft create --input stdin < <payload-file>`; take the returned absolute `path` and edit only that file. For a stored record, compose its Draft under the composition rule of `<reads>` in `references/github-store.md`, keeping the stored record's `lastEditedAt`, or its `createdAt` when it carries none, as the read stamp. For resumption, find the Draft with `spx change draft list`. NEVER delete a Draft.

Fill every key under `record-keys`, `draft-lifecycle`, and `draft-base`: `base` is the full head commit of the default branch the Declarations read, from `git rev-parse origin/<default>` after a fetch. Write the Declarations under `<declarations>` of the standards, one subsection per artifact under `subsection-coverage`, checking every cited fact against the checkout under `facts-checked`. Name no Index for a new artifact; the Applier assigns it under `index-assignment`.

</draft>

<form_check_gate>

Before every publish of a record below Applicable, and before every publish that writes the body of an Applicable record, run:

```bash
python3 "${SKILL_DIR}/scripts/check_form.py" --root <checkout-root> --draft <draft-path> [--issue <owner/repo#N> --read-edited-at <read stamp>] [--published <composed-stored-draft>]
```

Pass `--issue` and `--read-edited-at` for a publish that replaces a stored record, and `--published` for a Sliced record, the stored record composed into a payload file. Publish nothing while the check fails: repair each finding in the Draft, complete the sweep `${SKILL_DIR}/references/repair-sweep.md` states, and run the check again. An exit of 2 names the unusable argument or read; fix it and run again.

Before each publish at Framed or Sliced, trace each result the Verification part of the Statement of Intent names to the Declarations line that carries it, and repair the Draft for each result no line carries. Keep the trace out of the record.

</form_check_gate>

<publish>

Write the Draft to the store in this order, under `<write_discipline>`, and record each write:

1. Run the option check of `<store_options>` for every field this publish writes.
2. Re-read the record's edit stamp immediately before the body write under `github-race`; a stamp that differs from the read stamp stops the publish as failed under `stale-revision`.
3. Create the issue, or edit its title and body, from the Draft: the title from `title`, the body from the Draft's `## Statement of Intent` line to its end, never the front matter.
4. Write each field the publish changes to its home under `github-store`: Product, Parent, Predecessors, Base, and, for a Child, Priority; Maturity and Lifecycle only when recording. Clear the Base field when a split makes the record a Parent.
5. Bring the native blockers to the Draft's `blockers`, adding each missing and removing each extra one.
6. When recording, set the holder: add the assignee, then post the `claim` comment under `<transition_comment>` that records this session and worktree.
7. Read the edit history under `<reads>`: restore a revision another writer wrote between the read and the write, and count the publish as failed, as `github-race` states.
8. Read back the issue, its fields, and its blockers, and require each equal to the Draft.

A publish that wrote the body of an Applicable record then makes the `lower` Transition to Sliced through `product-tree:manage-change`, with the reason that the body changed, under `audit-binding`.

</publish>

<audit_dispatch>

For a Sliced Leaf, after a publish that writes its body and the readback, launch `product-tree_change-auditor` once through the native subagent capability with the task message `<owner>/<repo>#<N> <absolute checkout root>`, starting without authoring history or a suggested verdict. Read the verdict from the sealed run the result names. When the run is `approved` with no finding and its retained record carries the record's current Base, the holder advances the Leaf to Applicable through `product-tree:manage-change` with `advance Applicable <run-token>`. Every finding blocks under `audit-before-applicable`: repair the Draft, publish again through `<form_check_gate>` and `<publish>`, and launch the audit once more. NEVER audit the record in this conversation.

</audit_dispatch>

<operations>

- `record`: draft a new Change at Proposed and publish it. A Change with no Parent records as Submitted for its Priority decision; a Child records as Available with its Parent's Priority.
- `publish`: revise a stored record from its Draft and publish it. Keep `predecessors` and `parent` as stored; `base` moves only with a body write under `base-on-body`.
- `split`: below Applicable only, under `split`, record each Child from its own Draft with `parent` naming the source, then publish the source as a Parent: its body only the Statement of Intent, its Base cleared.
- `merge`: on the Operator's direction only, under `merge-direction`, append the absorbed Change to the survivor's `predecessors`, publish the survivor, and close the absorbed Change through `product-tree:manage-change` with `abandoned`.
- `reframe`: edit the record in place, publish it, and make the `lower` Transition to Proposed through `product-tree:manage-change`.

</operations>

<result>

Return the Change reference, the operation, the Maturity and Lifecycle read back, each form-check finding and audit finding with its rule slug, and each question no Declarations line can settle without the Operator, with its best answer. A failed publish returns the writes that landed, the failed write or unequal field, and the Draft path, and leaves the Draft in place.

</result>

<reference_index>

- `${SKILL_DIR}/templates/leaf.md` and `${SKILL_DIR}/templates/parent.md`: the Draft forms of a Leaf and a Parent.
- `${SKILL_DIR}/references/repair-sweep.md`: the sweep table of one repair batch.

</reference_index>

<failure_modes>

**A field lived in two homes.** Claude published the front matter in the issue body and also set the issue fields. A Transition later wrote only the field, so the two copies disagreed and readers took whichever they found first. The body starts at `## Statement of Intent`, and each field has one home.

**Authority was typed into the body.** Claude wrote an attestation line and an accountable-person line into a record after the Operator agreed in conversation. Any writer of the body can type such lines, so they proved nothing. The Operator's moves are Transitions, logged by their comments, and no body line stands in for one.

</failure_modes>

<success_criteria>

- Every publish followed a passing form check on the exact Draft it wrote, and a Framed or Sliced publish traced each Verification result to a Declarations line.
- The issue title, body, fields, and blockers read back equal to the Draft, with the body from `## Statement of Intent` and no front matter.
- A Sliced Leaf reached Applicable only through an audit run sealed `approved` with no finding on its current body and Base.
- A split left the source a Parent with no Base and every Child naming it; a merge appended the absorbed Change to the survivor's predecessors and closed it Abandoned; a reframe lowered the Change to Proposed.

</success_criteria>
