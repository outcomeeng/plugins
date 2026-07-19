---
name: merge
description: >-
  ALWAYS invoke this skill when the user asks to ship, integrate, or merge a changeset into the default branch on origin, or runs /merge.
  NEVER select a merge transport or drive a changeset to the default branch on origin without this skill.
argument-hint: "[instructions describing the change, or empty to use the current changeset]"
allowed-tools: Skill,{!% if target == 'claude' %!} Agent,{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}}, {{! tool('close_agent') !}},{!% endif %!} {{! tool('ask_user') !}}, Bash(git branch:*), Bash(git status:*), Bash(git symbolic-ref:*), Bash(git rev-parse:*), Bash(git diff:*), Bash(git push:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/classify_changeset.py":*), Bash(echo:*), Read
---

<objective>
A changeset reaches the default branch on origin through exactly one merge transport.
</objective>

<context>
Live repository state for transport selection, read at invocation.

**Arguments:** `$ARGUMENTS`

**Current branch:**
!`git branch --show-current || echo '(not a git repo)'`

**Working tree:** inspected by the Step 2 classifier, which owns complete changeset enumeration.

**Transport specialization:** resolved by /merging-standards in Step 1 after the Spec Tree foundation is live.

The changeset classification is computed in Step 2 by the classification script, not in this block — base-ref and committed branch-scope derivation route through the canonical `scope-changeset` primitives rather than inline git.

</context>

<transport_selection>
Select exactly one transport, in this precedence order:

1. **Contract-declared transport.** When /merging-standards `transport_selection_contract` carries an override, honor it (`manage-github-pr` or `direct-push`). The resolved override wins over the changeset heuristic.
2. **Coordination-note-only changeset -> direct-push.** When every changed path (working tree plus commits ahead of base) is a coordination note — a `PLAN.md` or `ISSUES.md` — route to the direct-push transport. Coordination notes carry no product truth, no spec assertion, and no implementation; the repository commits them directly so collaborators see the coordination state immediately.
3. **GitHub-PR transport (default).** Every other changeset — any spec, decision, implementation, test, doc, or mixed change, and any not-yet-materialized instructed change whose final file set is unknown — routes to the GitHub-PR transport.

The classification is produced by the classification script (Step 2), which derives the base ref and committed branch scope through the canonical `changeset_scope` primitives (`detect_base_ref`, `branch_scope`) and adds the uncommitted working-tree paths — never re-implementing base-ref or diff derivation inline, per the `scope-changeset` skill's contract. It emits counts over the full changed-file set: a changeset is coordination-note-only exactly when the total changed-file count is greater than zero and the non-coordination-note count is zero. The file preview the script prints is bounded for orientation only — classify from the counts, never the preview, since the preview may be truncated and a changeset with any non-note file is never coordination-note-only regardless of size. An empty or not-yet-materialized changeset (total zero) is never coordination-note-only — it defaults to GitHub-PR, where `/manage-github-pr` establishes the change.

The transport binds the gate predicates (which verification establishes `VERIFICATION_READINESS`, which review attests `MERGE_READINESS`, which checks are required, and which deploy or release actions exist) without adding, removing, reordering, or renaming a gate or changing the finding-disposition rule, per /merging-standards `<authority_gates>`.
</transport_selection>

<workflow>

**Step 1 — Load foundation and vocabulary.** If `<SPEC_TREE_FOUNDATION>` is absent, invoke `/understand` first. Invoke `/merging-standards` for the shared gate vocabulary, action tokens, and every named contract in `<resolved_contracts>`. Record the resolved contracts and apply their defaults when a field is absent. NEVER reconstruct transport or merge behavior from incidental repository docs, and NEVER edit a generated guide (`{{! file('root_guide') !}}`) to change it.

**Step 2 — Select the transport.** Compute the changeset classification by running the classification script, which routes base-ref and committed branch-scope derivation through the canonical `changeset_scope` primitives:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/classify_changeset.py"
```

It prints the total and non-coordination-note counts over the full changed-file set (committed branch scope plus working tree) and a bounded file preview. Apply `<transport_selection>` against those counts and the override in `transport_selection_contract`. Name the selected transport and the policy reason: contract override, coordination-note-only, or default GitHub PR. Do not expose raw file counts unless the count is itself the decision boundary the operator needs to inspect.

**Step 3 — Dispatch.**

- **GitHub-PR transport** -> invoke `/manage-github-pr` with `$ARGUMENTS` verbatim. `/manage-github-pr` owns the GitHub-PR lifecycle end to end: its own mode detection, the pre-mutation-confirmation pass (opt-in, off by default), and the commit -> open -> manage -> close protocols. /merge adds nothing to that flow and never reimplements it. Before delegating, state the selected transport, the policy reason, and that `/manage-github-pr` owns the next mutation and closeout. Any pre-mutation confirmation `/manage-github-pr` presents is the single confirmation for this path.
- **Direct-push transport** -> drive the direct-push lifecycle in `<direct_push_lifecycle>`.

**Step 4 — Continue or close.** Reaching merged state ends the transport, not necessarily the session. When in-scope parts of the user's stated goal remain, the transport continues with them rather than closing; it closes through `/handoff` only when the session is complete — the goal is met with no in-scope work remaining, or continuation by Claude is impossible (per live `/understand` `<closing_protocol>` and the `/handoff` precondition). Do not emit an independent merge receipt after the transport returns. The final operator-facing closeout comes from `/handoff` or from continuing the remaining governed work.

</workflow>

<script_testing>

`scripts/classify_changeset.py` is covered by the merging node's scenario evidence before release:

- A branch with one base-merged path, one branch path, and one working-tree path reports only the latter two in the complete changed-path set.
- A coordination note under a path containing spaces remains unquoted and classifies as coordination-only.
- An unconfigured remote default branch exits nonzero with `error: merge changeset classification failed` and no traceback.
- Duplicate committed and working-tree paths count once; only exact `PLAN.md` and `ISSUES.md` basenames classify as coordination notes.

</script_testing>

<direct_push_lifecycle>
The direct-push transport publishes a verified changeset straight to the default branch on origin with no pull request, under the same four gates as every transport, with the review predicate bound to the local review since no CI review exists, per /merging-standards `<authority_gates>`. The resolved `direct_push_contract`, `verification_contract`, and `delivery_phase_contract` bind its project-specific commands and predicates.

**Step D1 — State the plan; apply the confirmation contract.** When `pre_mutation_confirmation_contract.required=false`, state the plan in prose and proceed autonomously. Normal harness approval for a consumer-defined command remains a tool-security boundary and resumes the same governed step after approval. The plan names the changeset, the selected direct-push transport, the destination ref on origin, the commit, push, deploy, and release actions, and the verification and review gates that must hold before the push. When `required=true`, present that plan through the runtime's structured-question tool and obtain confirmation before any mutating action — never commit or push before that confirmation.

After the plan or required confirmation, run every command in `safety_contract.pre_mutation_checks` immediately before Step D2's commit or branch mutation. A failed check stops before the direct-push lifecycle changes the checkout.

**Step D2 — Commit.** Invoke `/commit-changes`. Branch hygiene from /merging-standards `<branch_hygiene>` does not apply unchanged here — direct-push publishes to the default branch on origin, so the working changeset is committed according to `direct_push_contract.checkout_strategy`.

**Step D3 — Establish `VERIFICATION_READINESS`.** All predicates per /merging-standards `<authority_gates>`:

- *Deterministic verification passes* — run `verification_contract`'s touched-scope deterministic commands per /merging-standards `<local_deterministic_scope>`. Fix failures and re-run until green.
- *Evidence-auditor predicates pass* — dispatch `test-evidence-auditor` for changed `[test]` assertions, linked tests, or imported test-infrastructure artifacts, and `eval-evidence-auditor` for changed `[eval]` assertions, eval artifacts, or producer artifacts for eval-backed assertions. Handle rejected, failing, or unknown verdicts per /merging-standards `<auditor_verdicts>`, then re-run deterministic verification and the relevant auditor until the evidence predicate is clean.
- *Local review converged* — run the `changes-reviewer` agent per /merging-standards `<local_review_invocation>`: let it resolve its own scope (the worktree it runs in and the diff), with no interpretive scope, severity pre-filter, or emphasis steering. Act on its findings by validity and phase per `<review_classification>`; iterate to convergence. This local review is the direct-push transport's `MERGE_READINESS` review predicate — it is the only review the transport has.
- *Terminal full deterministic gate passes when required* — when `verification_contract` carries a terminal full command, commit the converged subject, require a clean worktree, and run it once after every applicable evidence auditor and the local review converge on that exact head. Never run it concurrently with another heavy command. A later change invalidates the result, reopens every affected agentic predicate, and requires the full gate again only after those predicates reconverge.

**Step D4 — Base-sync, then merge (push to the default branch on origin).** Before publishing, base-sync per /merging-standards `<base_sync>`: fetch `origin/<default>` and, if the changeset is behind it, rebase onto it automatically from observable git state — never asking the operator — then re-establish `VERIFICATION_READINESS` on the rebased tree before the push, scoped by the `/sync-base` `preservation` proof and `verification_contract.governance_surfaces` so an unrelated base movement does not force a full re-run. A rebase conflict that cannot be resolved autonomously stops with `/sync-base`'s structured `conflict` report and active rebase state; a `dirty_tree` outcome is committed through `/commit-changes` then re-synced, never surfaced as a conflict. With `VERIFICATION_READINESS` held on the tree the push will publish, `MERGE_READINESS` for direct-push holds when the converged local review reports no unresolved valid `BLOCKING` or `DEBT` finding and every check in `direct_push_contract.required_checks` is terminal-green. Once it holds, run every applicable `safety_contract` preflight immediately before publishing with `direct_push_contract.push_command`, preserving the explicit destination ref from /merging-standards `<push_semantics>`. The transport never opens a pull request and never waits on a CI review.

**Step D5 — Deploy, release, then continue or close.** Run every declared deploy and release action under `DEPLOYMENT_READINESS` and `RELEASE_READINESS`. Preserve direct-push merge facts for closeout: default branch, pushed full HEAD SHA, deploy and release results, and release-source worktree state when the declared release or marketplace refresh used one. If in-scope parts of the user's stated goal remain, continue with them — a push to the default branch on origin is not a license to stop. Invoke `/handoff` plain only when the session is complete — the goal is met with no in-scope work remaining, or continuation by Claude is impossible (per live `/understand` `<closing_protocol>` and the `/handoff` precondition); `/handoff` computes the branch-state closeout record from /merging-standards `<branch_state_closeout>`, runs its safe cleanup policy using its own closeout tool surface, decides session-file creation per continuation state, includes **Remaining Branches**, and never receives `--no-session` on the user's behalf. Do not emit an independent merge receipt, push receipt, or sync receipt in place of that operator-useful closeout.

</direct_push_lifecycle>

<constraints>

- MUST select exactly one transport per `<transport_selection>` and delegate to that transport's skills — never run two transports, never reimplement a transport's internal protocol inline. The GitHub-PR lifecycle is `/manage-github-pr`'s; the direct-push lifecycle invokes `/commit-changes`, `/merging-standards`, and the `changes-reviewer` review.
- MUST keep the four gates and the finding-disposition rule transport-neutral — /merge selects the transport and binds nothing about the gates. A transport binds only the gate predicates, per /merging-standards `<authority_gates>`.
- MUST honor every named /merging-standards contract: a `transport_selection_contract` override wins over the changeset heuristic, while transport-specific commands and delivery declarations remain inputs to the selected transport.
- MUST treat the narrow Bash grants in frontmatter as the approval-free execution surface, never as a prohibition on consumer-defined commands the harness approves per call; run commands from `{{! file('root_guide') !}}` or `project_command_contract` through that normal tool-approval path when they fall outside the grants; when the harness exposes no approval path for a required command, emit `MERGE_BLOCKED:project-command-approval-unavailable` with the command and contract name; never skip the command, widen `allowed-tools` during execution, or add repository-specific grants to this portable skill.
- MUST proceed autonomously from the determined changeset when `pre_mutation_confirmation_contract.required=false`, handling any required harness tool approval as a security boundary that resumes the governed step; when `required=true`, the direct-push path presents the confirmation here and the GitHub-PR path delegates its single confirmation to `/manage-github-pr`.
- NEVER merge directly outside a transport's authority — the direct-push push executes only under `MERGE_READINESS`, and the GitHub-PR merge executes only through `/manage-pr`'s gates.
- NEVER surface a `dirty_tree` base-sync outcome as a rebase conflict — commit the working changes through `/commit-changes`, then re-run `/sync-base`; never stash.
- MUST drive every transport in the assigned worktree per /merging-standards `<assigned_cwd_worktree_discipline>` — never cross into a sibling worktree, never create a worktree, never stash; a branch-state conflict is resolved by branching in the assigned worktree and continuing.

</constraints>

<failure_modes>

**Mis-selected the transport from a mixed changeset.** Claude read a changeset that touched a `PLAN.md` plus a spec or implementation file as coordination-note-only and routed it to direct-push, bypassing the PR review. Coordination-note-only holds only when *every* changed path is a `PLAN.md` / `ISSUES.md`; one non-note file makes the whole changeset GitHub-PR. Re-read the full changed-file set before classifying — never sample.

**Routed a not-yet-materialized instructed change to direct-push.** Claude classified an instructed change whose files do not exist yet — an empty or unknown changeset — as coordination-note-only, which is wrong. An empty or not-yet-materialized changeset defaults to GitHub-PR, where `/manage-github-pr` establishes the change and re-evaluation happens against the real diff.

**Double confirmation.** Claude presented /merge's own pre-mutation confirmation and then `/manage-github-pr` presented another. For the GitHub-PR path, `/manage-github-pr` owns the single confirmation when `pre_mutation_confirmation_contract.required=true` — /merge states the transport selection in prose and delegates without a structured question. /merge presents the structured confirmation only on the direct-push path it executes itself.

</failure_modes>

<success_criteria>

- Exactly one transport was selected per `<transport_selection>`, with the reason named (contract override, coordination-note-only, or default).
- A coordination-note-only changeset routed to direct-push; every other changeset routed to GitHub-PR unless `transport_selection_contract` carried an override.
- The GitHub-PR path delegated to `/manage-github-pr` without reimplementing its lifecycle; the direct-push path drove `<direct_push_lifecycle>` invoking the governing skills.
- The flow proceeded autonomously when `pre_mutation_confirmation_contract.required=false`; when `required=true`, a proposal was presented through the runtime's structured-question tool and confirmed before the first mutation.
- The four gates and the finding-disposition rule stayed transport-neutral; only the predicate bindings differed by transport.
- The changeset reached the default branch on origin through the selected transport's authority, then continued any remaining in-scope work or closed through `/handoff` plain; the flow stopped only at an explicit gate surfaced to the user.

</success_criteria>
