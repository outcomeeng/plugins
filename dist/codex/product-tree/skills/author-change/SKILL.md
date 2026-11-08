---
name: author-change
description: >-
  ALWAYS invoke this skill when recording, publishing, splitting, merging, or
  reframing an Outcome Engineering Change record, or when turning a request into
  one. NEVER use it to author a spec or review a code changeset.
argument-hint: "<intent for a new Change | existing Change reference and revision>"
allowed-tools: Read, Write, Edit, Grep, Bash(python3 "${SKILL_DIR}/scripts/author_change.py":*), Bash(gh api user --jq .login), Bash(git rev-parse --show-toplevel), Bash(printenv CODEX_THREAD_ID), Bash(whoami), Bash(hostname -s), request_user_input
---

<objective>
A Change record recorded, published, split, merged, or reframed in the Change Store in the record form and read back equal to the Change Draft it came from, or a stopped result that names the form check's findings, the revision that changed, or the read that failed.
</objective>

<required_reading>

Use skill `product-tree:change-standards`. It states the record, the Change Draft, and the form check this skill's script runs.

Read `spx/local/coordination.md`. It names the Change Store and the Product. A store it does not name is a blocked operation.

</required_reading>

<operations>

The script makes exactly these six operations. Each writes its record only after the form check passes the Draft.

| Operation | Request fields beyond the common ones                 | What it does                                                                                                                                                                                                                                                      |
| --------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `record`  | `draft_path`                                          | Writes a new record at Maturity Proposed, Lifecycle Submitted for a Change with no Parent and Available for a Child, the recorder as holder, and for a Leaf the head of the default branch as base. Recording is no Transition and posts no comment.              |
| `publish` | `number`, `draft_path`, `handoff` for a held Change   | Writes the title, the body, and each metadata key the Draft changes, and no part it leaves unchanged; a Draft that writes the body of an Applicable record first lowers the Change to Sliced through operate-change; reads the record back.                       |
| `reframe` | `number`, `draft_path`, `reason`, `handoff` when held | Edits the Change in place and lowers its Maturity to Proposed.                                                                                                                                                                                                    |
| `split`   | `number`, `children`: the Draft paths of the Children | Accepts only a Leaf below Applicable; records each Child with the split record as parent in the same Change Store; the split record then holds only its Statement of Intent, loses its base, and takes its Children's Product. Children of two Products block it. |
| `draft`   | `number`, `draft_path`                                | Writes a Change Draft from the stored record: its metadata except the holder, then its body.                                                                                                                                                                      |
| `merge`   | `number` of the survivor, `absorbed`, `reason`        | Closes the absorbed Change Abandoned and adds it to the survivor's predecessors.                                                                                                                                                                                  |

The common fields are `operation`, `store`, `checkout_root`, and, for `publish`, `reframe`, and `merge`, `identity`. Every other Transition of a Change belongs to `product-tree:operate-change`.

</operations>

<workflow>

1. **Resolve the request.** Read `$ARGUMENTS` as the complete request. When it is empty, use one unambiguous request from the conversation; otherwise ask for the intended Output or the Change reference and wait. Resolve whether the request records a new Change or revises, splits, merges, or reframes an existing one.
2. **Resolve the store and the checkout.** Take the store from `spx/local/coordination.md` and the checkout root from `git rev-parse --show-toplevel`. A reference to a Change in another store is refused.
3. **Obtain the Change Draft.** For an existing Change, run the `draft` operation to a file in the scratch directory the harness names for this session, under a file name unique to the agent and the Change; where the harness names no scratch directory, use the one the environment designates, such as `$RUNNER_TEMP` on a hosted runner. For a new Change, write the Draft there with the file-write tool. Edit that one file for every revision. Never remove it.
4. **Refine the Draft** under the rules in `<rules>`.
5. **Resolve the identity** for `publish`, `reframe`, and `merge`, which can make a Transition: the account from `gh api user --jq .login`, the session id verbatim from `printenv CODEX_THREAD_ID`, the worktree from `git rev-parse --show-toplevel`, and the machine as `whoami` and `hostname -s` joined by `@`. The harness token is `codex`. Pass them as `identity` with the keys `login`, `harness`, `session`, `machine`, and `worktree`. An empty value stops before any write. A Change this session holds needs a `handoff` object with `branch`, `head` as the full commit, `next` as the Declarations subsection heading, and `pull_request` when one exists.
6. **Run the operation.** Write the request as one JSON object with the file-write tool to a file in the same scratch directory, under a file name unique to the agent and the operation, then run:

   ```bash
   python3 "${SKILL_DIR}/scripts/author_change.py" < <request-file>
   ```

7. **Read the result.** The script writes one JSON result and exits `0` for `ok`, `1` for `failed`, `2` for `invalid-request`, and `3` for `blocked`.
   - `ok`: `writes` in order, and `number` or `numbers`.
   - `failed`: `detail`, `writes`, and the cause the result names. `findings` holds the form check's findings, and the publish wrote nothing: repair the Draft for every finding and run the operation again. A changed revision means the record changed since the script read it: run `draft` again, reconcile the new text into the Draft, and run again. A `mismatch` lists the values that read back differently; `restored` reports that the script put back a revision another writer wrote. Repair nothing in the store by hand, and make no later write.
   - `invalid-request`: `detail` names the field or the value to correct.
   - `blocked`: `read` and `detail` name the read that failed, the bound it filled, or the sibling skill that is absent. Report them verbatim and write nothing.
8. **Close out.** Return the issue URL, the operation, the status, the writes, and the findings verbatim. A recorded Change stays held by the recorder; `product-tree:release-change` releases it when work stops with continuation remaining.

</workflow>

<rules>

- store-outside: ALWAYS: take the Change Store of a Product from the parameter the Operator records outside the Product Tree, and move no Change between Change Stores.
- merge-direction: ALWAYS: merge two Changes only on the Operator's direction.
- same-passage: ALWAYS: of two open Changes that amend the same passage of a file, name the other as a blocking Change in the one that reaches Application second.
- path-repair: ALWAYS: when a Change deletes or moves a path, give each file that names that path its own subsection when it is of a kind a subsection holds, leave any other such file to the Applier as a Mechanical Repair or to a delegate, have a generated file repaired at its declared source and regenerated, and leave every surviving link to Validate.
- operator-answers: ALWAYS: put every answer the Operator gives in Refinement into a Declarations line, with each condition, exception, boundary, and expected outcome.
- first-intent: ALWAYS: edit a record in place, so the store's edit history keeps the first Statement of Intent readable.

</rules>

<success_criteria>

- The script published the Draft only after the form check returned `pass`, and a `failed` result with findings left the store unchanged.
- Every value of the record read back equal to the Draft, with the Maturity a lower wrote where the publish made one.
- A stopped result reports the writes that landed, the check or read that stopped it, and no repair by hand.

</success_criteria>
