---
name: author-change
description: >-
  ALWAYS invoke this skill when recording, refining, publishing, splitting,
  merging, or reframing an Outcome Engineering Change record, or when turning a
  request into one. NEVER use it to author a spec or review a code changeset.
argument-hint: "<record | publish | split | merge | reframe> <intent, Draft path, or #N | owner/repo#N | issue-url>"
allowed-tools: Read, Write, Edit, Grep, Glob, collaboration.spawn_agent, collaboration.wait_agent, Bash(git -C * rev-parse:*), Bash(git rev-parse:*), Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue comment:*), Bash(gh api graphql:*), Bash(gh api repos/*/issues/*/dependencies/blocked_by:*), Bash(gh api repos/*/issues/*/dependencies/blocked_by/*:*), Bash(gh api repos/*/issues/* --jq .id), Bash(gh api user --jq .login), Bash(spx draft create --kind change), Bash(spx draft list --kind change:*), Bash(python3 "${SKILL_DIR}/scripts/check_form.py":*), Bash(python3 "${SKILL_DIR}/scripts/publish.py":*), Bash(gh api repos/*/commits/* --jq .sha), Bash(id -un), Bash(hostname -s), Bash(printenv CODEX_THREAD_ID), request_user_input
---

<objective>
One Change record in the declared Change Store, written from a Change Draft that passed the form check and read back equal to it — or the Children of a split, the survivor of a merge, or the reframed record — with the result naming each failed rule, audit finding, or open question.
</objective>

<essential_principles>

- Use skill `product-tree:change-standards`. Its rules govern every Draft and publish by their slugs; read its `references/github-store.md` for every store read and write.
- Read `spx/local/changes.md` for the Change Store and the Product.
- Every record starts from a Change Draft in the spx draft store every worktree shares, which outlives the session and the worktree that wrote it. Keep conversation text, transcripts, and audit bookkeeping out of the Draft under `no-person`.
- Ask only about a choice that changes a Declarations line and that the request, the Product Tree, and the repository leave open, one question at a time through the structured-question tool. Every answer the Operator gives reaches a Declarations line under `operator-answers`. Use skill `product-tree:interview` for an open choice of scope, failure behavior, dependency, evidence, or rollout.
- Use skill `product-tree:manage-change`. It makes every Transition the steps below name; this skill writes no Maturity or Lifecycle after recording.

</essential_principles>

<intake>

Read `$ARGUMENTS` as the operation, one of `record`, `publish`, `split`, `merge`, and `reframe`, then its input: the intended Output for `record`, a Draft path or a Change reference otherwise. When `$ARGUMENTS` is empty, take one unambiguous active request from the conversation; when none exists, ask for the operation and its input through the structured-question tool and wait. An operation outside the five is refused, naming them.

</intake>

<draft>

Create every Change Draft with `spx draft create --kind change`, which names the Draft's one file before any Draft text exists, and write and edit the Draft only at the absolute `path` that command returns. For a new Change, write the Draft from `${SKILL_DIR}/templates/leaf.md`, or `${SKILL_DIR}/templates/parent.md` for a Parent, to that path with the file-write tool. For a stored record, write there its Draft composed under the composition rule of `<reads>` in `references/github-store.md`, keeping the stored record's `lastEditedAt`, or its `createdAt` when it carries none, as the read stamp. Pass no Draft text on standard input and write no payload file for a Draft; a command reads the Draft from its path. For resumption, find the Draft with `spx draft list --kind change`. NEVER delete a Draft.

Fill every key under `record-keys`, `draft-lifecycle`, and `draft-base`: `base` is the full head commit of the default branch the Declarations read, from `git rev-parse origin/<default>` after a fetch. Write the Declarations under `<declarations>` of the standards, one subsection per artifact under `subsection-coverage`, checking every cited fact against the checkout under `facts-checked`. Name no Index for a new artifact; the Applier assigns it under `index-assignment`.

A Proposed Change for another Product of the declared Change Store records from any checkout, under `proposed-no-checkout`: create its Draft from this checkout under `<draft>`, take its `base` from that Product's default branch with `gh api repos/<owner>/<repo>/commits/<default> --jq .sha`, and let it hold only its Statement of Intent, which the form check judges without reading this checkout.

</draft>

<form_check_gate>

Before every publish of a record below Applicable, and before every publish that writes the body of an Applicable record, run:

```bash
python3 "${SKILL_DIR}/scripts/check_form.py" --root <checkout-root> --draft <draft-path> [--issue <owner/repo#N> --read-edited-at <read stamp>] [--published <composed-stored-draft>]
```

Pass `--issue` and `--read-edited-at` for a publish that replaces a stored record, and `--published` for a Sliced record, the stored record composed into its own Draft under `<draft>`. Publish nothing while the check fails: repair each finding in the Draft, complete the sweep `${SKILL_DIR}/references/repair-sweep.md` states, and run the check again. An exit of 2 names the unusable argument or read; fix it and run again. The publish command of `<publish>` runs the same check on the exact Draft it writes, so a Draft changed after this check is checked again at the publish.

Before each publish at Framed or Sliced, trace each result the Verification part of the Statement of Intent names to the Declarations line that carries it, and repair the Draft for each result no line carries. Keep the trace out of the record.

</form_check_gate>

<testing>

`scripts/check_form.py` runs the form check `product-tree:change-standards` ships, through a `__file__`-relative path. It was run with these inputs, each output matching the expected one; no run writes a file:

| Input                                                                         | Expected output                                                                                  | Observed    |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ----------- |
| a Leaf Draft that passes the form check                                       | the form check's `pass` result, exit 0                                                           | as expected |
| a Draft that breaks form rules                                                | the form check's `fail` result, exit 1                                                           | as expected |
| `--root` a relative path                                                      | the form check's `unusable` result, exit 2                                                       | as expected |
| the entrypoint copied to a skill directory with no `change-standards` sibling | `error: the form check is absent at <path>; reinstall the product-tree plugin` on stderr, exit 2 | as expected |

`scripts/publish.py` runs the same form check, then writes through `gh`. A compliance test in the plugin's source repository covers it against a recording store: a Draft that fails the check writes nothing; a passing Draft writes the fields it holds and clears Parent and Predecessors when it leaves them out, and writes no Priority, Maturity or Lifecycle on a publish that replaces a record; recording writes Maturity and Lifecycle, Submitted for a Child too, and no Priority, and a Child Draft that records as Available fails `draft-lifecycle` and writes nothing; a Parent's Draft without `base` clears the Base field; and the native blockers follow the Draft.

</testing>

<publish>

Write the Draft to the store through the publish command, and through no other write:

```bash
python3 "${SKILL_DIR}/scripts/publish.py" --root <checkout-root> --draft <draft-path> --store <owner/repo> [--issue <owner/repo#N> --read-edited-at <read stamp>] [--published <composed-stored-draft>]
```

It runs the form check of `<form_check_gate>` on the exact Draft and writes nothing while the check fails, under `publish-checked`. On a pass it re-reads the edit stamp before the body write under `github-race`, creates the issue or edits its title and body from the Draft's `## Statement of Intent` line to its end, and writes the Product, Parent, Predecessors and Base fields and the native blockers from the Draft, clearing each of them the Draft empties or leaves out, under `github-clear`. It leaves every other field as the store holds it, and writes Maturity and Lifecycle only when recording, and writes no Priority, Value, or Investment, a Child's included. Its result names each write. Then, under `<write_discipline>`:

1. Run the option check of `<store_options>` for each single-select field the publish writes, before running the command.
2. When recording, set the holder: add the assignee, then post the `claim` comment under `<transition_comment>` that records this session and worktree.
3. Read the edit history under `<reads>`. When another writer's revision landed between the read and the write, compose a Draft from that revision, publish it through the same command to restore it, and count the publish as failed, as `github-race` states.
4. Read back the issue, its fields, and its blockers, and require each equal to the Draft.

A publish that wrote the body of an Applicable record then makes the `lower` Transition to Sliced through `product-tree:manage-change`, with the reason that the body changed, under `audit-binding`.

</publish>

<audit_dispatch>

For a Sliced Leaf, after a publish that writes its body and the readback, launch `product-tree_change-auditor` once through the native subagent capability with the task message `<owner>/<repo>#<N> <absolute checkout root>`, starting without authoring history or a suggested verdict. Read the verdict from the sealed run the result names. When the run is `approved` with no finding and its retained record carries the record's current Base, the holder advances the Leaf to Applicable through `product-tree:manage-change` with `advance Applicable <run-token>`. Every finding blocks under `audit-before-applicable`: repair the Draft, publish again through `<form_check_gate>` and `<publish>`, and launch the audit once more. NEVER audit the record in this conversation.

</audit_dispatch>

<operations>

- `record`: draft a new Change at Proposed and publish it. Every Change, a Child included, records as Submitted for its own Priority decision, with no Priority, Value, or Investment.
- `publish`: revise a stored record from its Draft and publish it. Keep `predecessors` and `parent` as stored; `base` moves only with a body write under `base-on-body`.
- `split`: below Applicable only, under `split`, record each Child from its own Draft with `parent` naming the source, then publish the source as a Parent: its body only the Statement of Intent and its Draft without `base`, so the publish clears its Base.
- `merge`: on the Operator's direction only, under `merge-direction`, append the absorbed Change to the survivor's `predecessors`, publish the survivor, and close the absorbed Change through `product-tree:manage-change` with `abandoned` and the survivor's reference, which closes the absorbed issue as a duplicate of the survivor's issue.
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
- A split left the source a Parent with no Base and every Child naming it; a merge appended the absorbed Change to the survivor's predecessors and closed it Abandoned as a duplicate of the survivor's issue; a reframe lowered the Change to Proposed.

</success_criteria>
