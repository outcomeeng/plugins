# GitHub PR Transport

PROVIDES the GitHub-PR merge transport — the `/manage-github-pr` lifecycle orchestration that takes a ready changeset from intent through pull-request publication, merge, declared deploy, declared release, and close, invoked by `/merge` when it selects this transport
SO THAT a developer on either runtime
CAN take a change through the governed commit, PR, verification, preview, merge, deploy, release, and handoff protocols without choosing each internal protocol by hand, per `spx/15-merging.pdr.md`

## Assertions

### Scenarios

- Given `/manage-github-pr` invoked with arguments, when it runs, then it interprets the arguments as instructions and drives the lifecycle by invoking `/commit-changes`, `/open-pr`, and `/manage-pr` — autonomously by default, or presenting a pre-mutation confirmation through the runtime's structured-question tool and waiting first when the merge overlay opts into it ([audit])
- Given `/manage-github-pr` invoked with no arguments and an existing changeset — uncommitted working-tree changes, or a branch ahead of its base — when it runs, then it derives intent from that changeset and drives the same lifecycle, presenting a pre-mutation confirmation first only when the merge overlay opts into it ([audit])
- Given `/manage-github-pr` invoked with no arguments and a clean working tree on the base branch, when it runs, then it interviews the user through `/interview` to establish the change before any mutation ([audit])
- Given a confirmed GitHub-PR changeset, when `/manage-github-pr` drives the lifecycle, then it runs `/commit-changes`, `/open-pr`, and `/manage-pr`; after merge it continues through any declared deploy and release phases before close, carries the branch-state closeout record and Remaining Branches groups into `/handoff`, and when in-scope parts of the user's stated goal remain it continues with them rather than closing; it closes through `/handoff` plain (the skill deciding session-file creation, never a hardcoded `--no-session`) only when the session is over — the goal is met with no in-scope work remaining, or continuation by the agent is impossible — and `/handoff` supplies the operator-useful final closeout rather than a merge receipt ([audit])
- Given `/manage-github-pr` is invoked with an existing PR number, PR URL, or branch that already has an open PR, when it runs, then it delegates PR-state work to `/manage-pr` instead of opening another PR ([audit])

### Compliance

- ALWAYS: `/manage-github-pr` ships as a user-invocable `SKILL.md` under `plugins/spec-tree/skills/manage-github-pr/`, with no command wrapper, so it activates on both runtimes per `spx/13-plugin-and-runtime-conventions.adr.md` ([audit])
- ALWAYS: `/open-pr` ships as an internal `SKILL.md` under `plugins/spec-tree/skills/open-pr/`, with no direct command wrapper ([audit])
- ALWAYS: `/manage-github-pr` remains user-invocable as the GitHub PR transport entry point ([audit])
- ALWAYS: `/open-pr` remains an internal protocol with `user-invocable: false`, loaded only by `/manage-github-pr`, run once per opening, and never used as an automation re-entry target ([audit])
- ALWAYS: `/manage-pr` is loaded by `/manage-github-pr` and remains user-invocable as the direct management entry point for an existing PR number, PR URL, or branch with an open PR ([audit])
- ALWAYS: the GitHub-PR transport's `/manage-github-pr` orchestration is selected by `/merge`, not by itself — `/manage-github-pr` assumes this transport and reads `spx/local/merging.md` only for the transport's configuration, never to decide whether a PR is the transport ([audit])
- ALWAYS: drive the lifecycle from a determined changeset without an up-front operator proposal by default; only when the merge overlay opts into a pre-mutation confirmation, present the changeset and intended lifecycle through the runtime's structured-question tool and obtain confirmation before the first mutating action — branch creation, commit, push, PR open, or merge — per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: GitHub-PR transport skills present `gh` payload input by supported harness environment, per `spx/15-agent-tools.pdr.md`, and present GitHub PR check waiting as exactly `gh pr checks <pr-number> --watch --fail-fast --interval 30` in one foreground command ([audit])
- ALWAYS: drive the lifecycle by invoking the governing skills — `/apply` or the language coding skills for implementation, `/commit-changes`, `/open-pr`, and `/manage-pr` — never reimplementing their protocols ([audit])
- NEVER: merge directly — the merge executes only through `/manage-pr`'s `MERGE_READINESS` authority, and any declared deploy or release action executes after merge through `DEPLOYMENT_READINESS` or `RELEASE_READINESS`, per `spx/15-merging.pdr.md` ([audit])

## Eval Coverage Model

When this node uses eval evidence, the eval suite covers these conversation cases:

- Argument instruction mode: a user asks `/manage-github-pr` to implement and ship work, and the response drives the default lifecycle autonomously — or presents a pre-mutation confirmation first when the merge overlay opts into it.
- Existing changeset mode: a dirty working tree or branch ahead of base is treated as the thing to ship, and intent is derived from the diff and commits.
- Empty mode: a clean base branch starts with `/interview`, not branch creation, committing, pushing, PR opening, or merging.
- Existing open PR mode: the branch already has a PR, or the user passes a PR number or URL, and `/manage-github-pr` invokes the management protocol instead of opening a duplicate PR.
