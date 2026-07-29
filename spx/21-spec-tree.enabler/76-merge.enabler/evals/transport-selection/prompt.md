<!-- Prompt template for the transport-selection eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies /merge's transport selection and
     delegation from spx/21-spec-tree.enabler/76-merge.enabler/merge.md
     and spx/15-merging.pdr.md — given the changeset classification counts
     and the spx/local/merging.md overlay, which transport /merge selects,
     why, where it delegates, and whether it presents a pre-mutation
     confirmation before the first mutation. The three authority gates and
     the finding-disposition rule are transport-neutral and out of scope
     here; the local-completion-boundary eval covers the delivered-value
     boundary. -->

You are simulating Claude running `/merge` Step 2 (classify the changeset and select the transport) and Step 3 (dispatch) for a changeset destined for the repository's default branch.

`/merge` selects exactly one transport, in this precedence order:

1. **Overlay-declared transport.** When `spx/local/merging.md` declares an explicit `transport:` selector (`manage-github-pr` or `direct-push`), honor it. The overlay declaration wins over the changeset heuristic.
2. **Coordination-note-only changeset → direct-push.** When the changeset is coordination-note-only — its total changed-file count is greater than zero and its non-coordination-note count is zero (every changed path is a `PLAN.md` or `ISSUES.md`) — route to the direct-push transport.
3. **GitHub-PR transport (default).** Every other changeset routes to GitHub-PR — a mixed changeset (any non-note file present), an implementation/spec/decision/test/doc change, and an empty or not-yet-materialized changeset (total changed-file count zero) whose final file set is unknown.

Classify from the counts, never from the file preview: the preview is bounded and may be truncated, so a changeset with a non-coordination-note count greater than zero is never coordination-note-only regardless of what the preview shows. A total changed-file count of zero is never coordination-note-only — it defaults to GitHub-PR.

Then dispatch by the selected transport:

- **GitHub-PR** → delegate to `/manage-github-pr`, which owns the commit → open → manage → close lifecycle. `/merge` states the selection in prose and delegates; it never presents its own pre-mutation confirmation on this path (any confirmation is `/manage-github-pr`'s).
- **Direct-push** → `/merge` drives the direct-push lifecycle itself (through `/commit-changes` and the `changes-reviewer` review). On this path `/merge` presents a pre-mutation confirmation before the first mutation only when the overlay opts into one; otherwise it states the selection and proceeds autonomously.

Case id: substituted by the harness.

The selection input (JSON-encoded):

```json
{input_json}
```

Input fields:

- `overlay_transport_selector`: `"none"`, `"manage-github-pr"`, or `"direct-push"` — the explicit `transport:` selector in `spx/local/merging.md`, or `"none"` when absent.
- `overlay_pre_mutation_confirmation`: boolean — whether the overlay opts into a pre-mutation confirmation.
- `changeset`: `total_changed_files` and `non_coordination_note_files` counts over the full changed-file set (committed branch scope plus working tree), with a bounded `changed_paths_preview` and a `preview_truncated` flag.

Verdict schema — four fields, all mandatory:

- `selected_transport`: `"GITHUB_PR"` or `"DIRECT_PUSH"`.
- `selection_reason`: `"overlay-selector"`, `"coordination-note-only"`, or `"default"`.
- `delegation_target`: `"manage-github-pr"` (GitHub-PR path delegates to that skill) or `"direct-push-lifecycle"` (`/merge` drives the direct-push lifecycle inline).
- `pre_mutation_action`: `"PRESENT_CONFIRMATION"` or `"PROCEED_AUTONOMOUSLY"`.

Decision rules:

1. If `overlay_transport_selector` is not `"none"`, select that transport and report reason `"overlay-selector"`.
2. Else, if `changeset.total_changed_files` is greater than zero and `changeset.non_coordination_note_files` is zero, select `"DIRECT_PUSH"` and report reason `"coordination-note-only"`.
3. Else, select `"GITHUB_PR"` and report reason `"default"`.
4. Set `delegation_target` to `"manage-github-pr"` when `selected_transport` is `"GITHUB_PR"`, otherwise `"direct-push-lifecycle"`.
5. Set `pre_mutation_action` to `"PRESENT_CONFIRMATION"` only when `selected_transport` is `"DIRECT_PUSH"` and `overlay_pre_mutation_confirmation` is true; otherwise `"PROCEED_AUTONOMOUSLY"`.

Return only a parseable JSON document matching the schema.
