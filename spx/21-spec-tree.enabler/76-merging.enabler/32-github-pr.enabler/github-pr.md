# GitHub PR Transport

PROVIDES the GitHub-PR merge transport — the `/github-pr` lifecycle orchestration that takes a ready changeset from intent to a merged pull request, invoked by `/merge` when it selects this transport
SO THAT a developer on either runtime
CAN take a change from intent to merge through the governed commit, PR, review, merge, and handoff protocols without choosing each internal protocol by hand, per `spx/15-merging.pdr.md`

## Assertions

### Scenarios

- Given `/github-pr` invoked with arguments, when it runs, then it interprets the arguments as instructions and drives the lifecycle by invoking `/committing-changes`, `/opening-pr`, and `/managing-pr` — autonomously by default, or presenting a pre-mutation confirmation through the runtime's structured-question tool and waiting first when the merge overlay opts into it ([review])
- Given `/github-pr` invoked with no arguments and an existing changeset — uncommitted working-tree changes, or a branch ahead of its base — when it runs, then it derives intent from that changeset and drives the same lifecycle, presenting a pre-mutation confirmation first only when the merge overlay opts into it ([review])
- Given `/github-pr` invoked with no arguments and a clean working tree on the base branch, when it runs, then it interviews the user through `/interviewing` to establish the change before any mutation ([review])
- Given a confirmed GitHub-PR changeset, when `/github-pr` drives the lifecycle, then it runs `/committing-changes`, `/opening-pr`, `/managing-pr`, and post-merge closure through `/handoff --no-session` ([review])
- Given `/github-pr` is invoked with an existing PR number, PR URL, or branch that already has an open PR, when it runs, then it delegates PR-state work to `/managing-pr` instead of opening another PR ([review])

### Conformance

- The `/github-pr` skill conforms to portable-skill packaging — a `SKILL.md` under `plugins/spec-tree/skills/github-pr/`, user-invocable, shipped as a skill rather than a command, so it activates on both runtimes, per `spx/13-plugin-and-runtime-conventions.adr.md` ([test](tests/test_github_pr.conformance.l1.py))
- The PR lifecycle protocol skills conform to internal-protocol packaging — `/opening-pr` and `/managing-pr` are `user-invocable: false` (hidden from direct user invocation, loaded by `/github-pr`), and the direct `/open-pr` command wrapper is absent ([test](tests/test_github_pr.conformance.l1.py))

### Compliance

- ALWAYS: the GitHub-PR transport's `/github-pr` orchestration is selected by `/merge`, not by itself — `/github-pr` assumes this transport and reads `spx/local/merging.md` only for the transport's configuration, never to decide whether a PR is the transport ([audit])
- ALWAYS: drive the lifecycle from a determined changeset without an up-front operator proposal by default; only when the merge overlay opts into a pre-mutation confirmation, present the changeset and intended lifecycle through the runtime's structured-question tool and obtain confirmation before the first mutating action — branch creation, commit, push, PR open, or merge — per `spx/15-merging.pdr.md` ([review])
- ALWAYS: drive the lifecycle by invoking the governing skills — `/applying` or the language coding skills for implementation, `/committing-changes`, `/opening-pr`, and `/managing-pr` — never reimplementing their protocols ([review])
- NEVER: merge directly — the merge executes only through `/managing-pr`'s `MERGE_READINESS` ∧ `PRODUCTION_READINESS` authority, per `spx/15-merging.pdr.md` ([review])

## Eval Coverage Model

When this node uses eval evidence, the eval suite covers these conversation cases:

- Argument instruction mode: a user asks `/github-pr` to implement and ship work, and the response drives the default lifecycle autonomously — or presents a pre-mutation confirmation first when the merge overlay opts into it.
- Existing changeset mode: a dirty working tree or branch ahead of base is treated as the thing to ship, and intent is derived from the diff and commits.
- Empty mode: a clean base branch starts with `/interviewing`, not branch creation, committing, pushing, PR opening, or merging.
- Existing open PR mode: the branch already has a PR, or the user passes a PR number or URL, and `/github-pr` invokes the management protocol instead of opening a duplicate PR.
