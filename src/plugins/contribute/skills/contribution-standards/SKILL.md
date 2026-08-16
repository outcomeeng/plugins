---
name: contribution-standards
user-invocable: false
description: >-
  Contribution standards for changes and reports sent to a repository the operator does not control. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The invariants every artifact obeys on its way to a repository the operator does not control, independent of artifact type.
</objective>

<success_criteria>

- The base repository was named on every write rather than left to `gh`'s default.
- The operator's permission on it came from `viewerPermission`, not from a remote, an account name, or a successful push.
- Authorization for a base the operator does not control named that base in the turn the artifact was created.
- The contribution branch was cut from the base repository's default branch.
- Every outward-facing surface passed a prose review before it was sent.
- No outward-facing surface named Claude or its runtime.
- The artifact carries the evidence a maintainer needs to reproduce its claim without access to the operator's machine.

</success_criteria>

<terms>

| Term         | Meaning                                                                       |
| ------------ | ----------------------------------------------------------------------------- |
| **upstream** | The repository a fork came from. `gh` calls the same thing `parent`.          |
| **base**     | The repository receiving the contribution. `--repo`, `--base`.                |
| **head**     | The repository and branch the contribution comes from. `--head owner:branch`. |

Name the relationship as upstream where an operator reads it. Carry `base` and `head` in every command, because a relationship name identifies no repository.

A git remote is a local label. `origin` and `upstream` each point wherever the checkout was configured to point, so confirm what a remote resolves to before pushing or fetching through it.

</terms>

<resolution>

`/upstream` resolves the target once per contribution and emits an `<UPSTREAM_TARGET>` marker carrying `base`, `head`, `permission`, and `classification`. Read that marker. Invoke `/upstream` only when no marker is live — after a compaction, or as the first stage of a contribution.

One contribution is one arc: resolve, cut the branch, publish, answer review. Re-resolving per stage would repeat the fork search across every account and organization the operator holds, for an answer that has not changed.

Substitute every resolved value **literally** into later commands, written in this plugin's skills as a `<placeholder>`. Never carry a resolved value in a shell variable across steps: shell state does not persist between commands here, so a variable no step assigns silently expands to nothing and the command that names the empty string still runs. Within one command block a value the block itself resolves may be captured in a variable, because those lines share one shell; resolve a value the block has not yet produced in an earlier block.

Act on the classification:

| `classification`        | Meaning                                                            | Action                                                                |
| ----------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------- |
| `upstream-contribution` | `READ`, `TRIAGE`, or `NONE` on the base, and one head to push from | Continue under `<invariants>`, starting with authorization.           |
| `head-ambiguous`        | Several forks of the base across the operator's accounts           | STOP per `<invariants>` "Never choose the fork destination".          |
| `fork-absent`           | No fork of the base under any account the operator holds           | STOP per `<invariants>` "Never choose the fork destination".          |
| `controlled`            | `ADMIN`, `MAINTAIN`, or `WRITE` on the base                        | STOP. A repository the operator controls belongs to its own workflow. |
| `blocked`               | Permission unreadable, or `gh` unavailable or unauthenticated      | STOP and report the resolver's `detail` verbatim.                     |

**Verify `origin` before pushing or fetching through it.** The marker names the head repository; `origin` is a local label that may point somewhere else entirely. Before the first `git push` or `git fetch` that names `origin`, confirm it resolves to the resolved head, and stop when it does not:

```bash
gh repo view "$(git remote get-url origin)" --json nameWithOwner --jq '.nameWithOwner'
```

Fetch the base repository by URL, so only the head side needs this check.

</resolution>

<invariants>

**Name the base repository.** `gh` resolves a fork's base to its parent, so a command that names no repository says nothing about where its artifact lands. Pass `--repo <owner>/<name>` on every `gh pr create`, `gh issue create`, `gh issue comment`, and `gh pr comment`.

**Establish permission from the API.** `viewerPermission` on the resolved base is the only source. A git remote named `upstream` proves nothing, `gh api user` proves nothing, and a successful push proves nothing — the operator holds repositories across several organizations, and none of the three reports the permission governing this one.

**Require in-turn authorization for `READ`, `TRIAGE`, and `NONE`.** Resolve the target, name it back to the operator, and create nothing there until the operator authorizes that base in the same turn.

**Authorization covers the artifact and its revisions.** A push answering review updates the artifact the operator already authorized and needs no fresh authorization. A new pull request, a new issue, or a comment on an unrelated thread each require their own.

**Cut from the base repository's default branch.** Not the head repository's, which is behind by however long since the last sync. A contribution branch cut from a stale fork default carries unrelated divergence into the diff.

**Iterate by appending.** The operator cannot push to the base repository, so every revision is a push to the head branch, which updates the open artifact in place. NEVER force-push a branch a reviewer has already read.

**Conform to the base repository's conventions.** Locate them before writing code: the contributing guide, fixture and test-data READMEs, metadata schemas, the documents a change of this kind updates, and the commit style of recent history. A contribution shaped like the operator's own repository is rework for the maintainer.

**Run the base repository's own verification.** Its declared checks — the contributing guide's commands, the workflow files, the build and test targets — run locally and report success before the artifact opens. A check that cannot run locally is named in the body as unverified, with the reason. The maintainer's checks are the ones that decide the contribution; running them first spends review on substance.

**Outward-facing text is permanent.** The notification reaches every watcher when the artifact appears, and deleting the artifact does not recall it. Title, body, comments, and review replies each pass a prose review before they are sent. Where the prose plugin is installed, dispatch its `prose-auditor` thin agent through the runtime's agent-dispatch surface, so the verdict comes from a separate verifier agent session rather than the session that wrote the text; where it is not installed, review against `<outward_text>` and report that the review ran unassisted.

**Never name Claude or its runtime in the artifact.** Every outward-facing surface — issue and pull-request titles and bodies, comments, review replies, commit messages, and branch names — describes the work, never what produced it. A maintainer decides the contribution on its merits, and an authorship marker in a permanent public record raises a policy question the contribution never needed to raise. Exact tool names, quoted command output, and file paths keep their required spelling.

**Carry reproducible evidence.** A maintainer cannot see the operator's machine. A defect claim states the tool versions involved, the base commit it was observed against, the command that produced the observation, and at least one negative control showing the same method reporting the opposite result. A claim without a negative control cannot distinguish a real defect from a broken measurement.

**Never synthesize the condition being observed.** Evidence comes from the real thing. Forcing a narrow terminal with a multiplexer to stand in for a narrow application pane produces a screen that looks right and proves nothing: the multiplexer pads the unused width, adds its own status bar, and masks the foreground process. When the environment cannot be reproduced, state the claim as unverified and say why; never substitute a lookalike and report it as observed.

**The review loop runs on comments, not on API state.** Requesting a reviewer, dismissing a review, and clearing a changes-requested decision are maintainer-side actions. `gh pr edit --add-reviewer` fails on a base the operator does not control, and `reviewDecision` stays `CHANGES_REQUESTED` until the maintainer chooses to look again. A comment stating what changed is the re-request. Treat the permission failure as the expected path, never as an error to retry.

**Never choose the fork destination.** When no head repository exists, report the resolved base, the accounts and organizations that could hold the fork, and the exact `gh repo fork` command — then stop. `gh repo fork` defaults to the personal account, and an operator holding repositories across several organizations has a destination decision no resolution can make.

**Never wait on the artifact.** A management pass reads current state once, acts on it, and returns. A maintainer answers on their own schedule, so polling, watching, and sleeping accumulate cost against a signal that arrives when it arrives.

**Open as a draft when the contribution is unsolicited or its conventions are uncertain.** `--draft` costs nothing and says the shape is still open to direction.

</invariants>

<capability_scope>

A skill's `allowed-tools` enumerates the commands it can name before it runs. Three things these flows require cannot be named in advance, because they belong to a repository the operator does not control and are discovered from it:

- the base repository's declared checks, whatever its contributing guide, workflow files, and build targets name — `pytest`, `npm test`, `make`, `just`, or something this list has never heard of;
- the version probes and reproducing commands an evidence claim needs, which belong to the subject tool rather than to this plugin;
- editing the files a confirmed finding requires changing.

Each runs through the runtime's own per-call approval, outside the approval-free surface `allowed-tools` grants. Those narrow grants are that surface, never a prohibition on the work these steps mandate.

NEVER widen `allowed-tools` to a general execution or file-mutation grant to avoid those prompts. A grant broad enough to run whatever checks a base repository declares is broad enough to run anything, in a flow whose whole purpose is writing somewhere the operator does not control. When the runtime exposes no approval path at all, stop and report the exact command and the step requiring it; never skip a declared check and never report one as passed.

</capability_scope>

<outward_text>

Apply these when no prose plugin is installed. They are the subset of general prose craft that matters most in a maintainer's inbox.

- State the finding before the reasoning that produced it. A maintainer reads the first line and decides whether to read the rest.
- Name what changed, not what was attempted. "Rows are now assembled into logical rows before matching" beats "I tried several approaches."
- Quote the evidence rather than describing it. A four-line captured screen outperforms a paragraph about the screen.
- Cut every sentence about the contribution's own process — how long it took, how many attempts, what was learned.
- Never characterize the maintainer's review as correct or incorrect; report what the finding changed.

</outward_text>

<failure_modes>

**A multiplexer stood in for the real environment.** Claude forced a 36-column pty to reproduce a narrow-pane defect. The multiplexer padded the unused width with its own filler, added a status bar, and masked the foreground process, so the application's own roster command returned empty. The capture looked like evidence and was not a screen the product could ever render. Reproduce the condition in the real surface, or state the claim as unverified.

**A permission failure was retried as an error.** Claude ran `gh pr edit --add-reviewer` on a base the operator did not control, read `does not have the correct permissions to execute RequestReviewsByLogin`, and retried. The failure is structural on every `READ` base. Post the comment that states what changed and stop.

**A resolved default was mistaken for a named target.** Claude ran `gh pr create` in a fork checkout without `--repo`. `gh` resolved the base to the parent, so the command would have opened against an organization nobody named. Resolve the target first and pass it explicitly.

</failure_modes>
