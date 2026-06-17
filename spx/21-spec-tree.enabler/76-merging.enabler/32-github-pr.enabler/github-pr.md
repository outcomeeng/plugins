# GitHub PR Transport

PROVIDES the GitHub-PR merge transport — the `/manage-github-pr` lifecycle orchestration that takes a ready changeset from intent to a merged pull request, invoked by `/merge` when it selects this transport
SO THAT a developer on either runtime
CAN take a change from intent to merge through the governed commit, PR, review, merge, and handoff protocols without choosing each internal protocol by hand, per `spx/15-merging.pdr.md`

## Assertions

### Scenarios

- Given `/manage-github-pr` invoked with arguments, when it runs, then it interprets the arguments as instructions and drives the lifecycle by invoking `/commit-changes`, `/open-pr`, and `/manage-pr` — autonomously by default, or presenting a pre-mutation confirmation through the runtime's structured-question tool and waiting first when the merge overlay opts into it ([review])
- Given `/manage-github-pr` invoked with no arguments and an existing changeset — uncommitted working-tree changes, or a branch ahead of its base — when it runs, then it derives intent from that changeset and drives the same lifecycle, presenting a pre-mutation confirmation first only when the merge overlay opts into it ([review])
- Given `/manage-github-pr` invoked with no arguments and a clean working tree on the base branch, when it runs, then it interviews the user through `/interview` to establish the change before any mutation ([review])
- Given a confirmed GitHub-PR changeset, when `/manage-github-pr` drives the lifecycle, then it runs `/commit-changes`, `/open-pr`, and `/manage-pr`; after merge, when in-scope parts of the user's stated goal remain it continues with them rather than closing, and it closes through `/handoff` (the skill deciding session-file creation, never a hardcoded `--no-session`) only when the session is genuinely over — the goal is met with no in-scope work remaining, or continuation by the agent is impossible ([review])
- Given `/manage-github-pr` is invoked with an existing PR number, PR URL, or branch that already has an open PR, when it runs, then it delegates PR-state work to `/manage-pr` instead of opening another PR ([review])

### Conformance

- The `/manage-github-pr` skill conforms to portable-skill packaging — a `SKILL.md` under `plugins/spec-tree/skills/manage-github-pr/`, user-invocable, shipped as a skill rather than a command, so it activates on both runtimes, per `spx/13-plugin-and-runtime-conventions.adr.md` ([test](tests/test_github_pr.conformance.l1.py))
- `/open-pr` conforms to internal-protocol packaging — `user-invocable: false`, hidden from direct invocation and loaded only by `/manage-github-pr`; it runs once per opening and is never an automation re-entry target, and no direct `/open-pr` command wrapper exists ([test](tests/test_github_pr.conformance.l1.py))
- `/manage-pr` is loaded by `/manage-github-pr` yet stays user-invocable rather than `user-invocable: false` — it is the direct open-PR management entry point for an existing PR number, PR URL, or branch that already has an open PR, per `spx/13-plugin-and-runtime-conventions.adr.md` ([test](tests/test_github_pr.conformance.l1.py))

### Compliance

- ALWAYS: the GitHub-PR transport's `/manage-github-pr` orchestration is selected by `/merge`, not by itself — `/manage-github-pr` assumes this transport and reads `spx/local/merging.md` only for the transport's configuration, never to decide whether a PR is the transport ([audit])
- ALWAYS: drive the lifecycle from a determined changeset without an up-front operator proposal by default; only when the merge overlay opts into a pre-mutation confirmation, present the changeset and intended lifecycle through the runtime's structured-question tool and obtain confirmation before the first mutating action — branch creation, commit, push, PR open, or merge — per `spx/15-merging.pdr.md` ([review])
- ALWAYS: GitHub-PR transport skills present `gh` payload input by supported harness environment and present GitHub PR check waiting as exactly `gh pr checks <pr-number> --watch --fail-fast --interval 30`, per `spx/15-agent-tools.pdr.md` ([audit])
- ALWAYS: drive the lifecycle by invoking the governing skills — `/apply` or the language coding skills for implementation, `/commit-changes`, `/open-pr`, and `/manage-pr` — never reimplementing their protocols ([review])
- NEVER: merge directly — the merge executes only through `/manage-pr`'s `MERGE_READINESS` ∧ `PRODUCTION_READINESS` authority, per `spx/15-merging.pdr.md` ([review])

## Eval Coverage Model

When this node uses eval evidence, the eval suite covers these conversation cases:

- Argument instruction mode: a user asks `/manage-github-pr` to implement and ship work, and the response drives the default lifecycle autonomously — or presents a pre-mutation confirmation first when the merge overlay opts into it.
- Existing changeset mode: a dirty working tree or branch ahead of base is treated as the thing to ship, and intent is derived from the diff and commits.
- Empty mode: a clean base branch starts with `/interview`, not branch creation, committing, pushing, PR opening, or merging.
- Existing open PR mode: the branch already has a PR, or the user passes a PR number or URL, and `/manage-github-pr` invokes the management protocol instead of opening a duplicate PR.
