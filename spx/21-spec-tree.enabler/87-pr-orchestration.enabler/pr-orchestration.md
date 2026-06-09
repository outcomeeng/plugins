# PR Orchestration

PROVIDES the `/pr` lifecycle router for changes that are ready to ship
SO THAT a developer on either runtime
CAN take a change from intent to merge through the governed commit, PR, review, merge, and handoff protocols without choosing each internal protocol by hand

## Assertions

### Scenarios

- Given `/pr` invoked with arguments, when it runs, then it interprets the arguments as instructions, presents a proposal through the runtime's structured-question tool, and on confirmation drives the lifecycle by invoking `/committing-changes`, `/opening-pr`, and `/managing-pr` ([review])
- Given `/pr` invoked with no arguments and an existing changeset — uncommitted working-tree changes, or a branch ahead of its base — when it runs, then it derives the proposal from that changeset and, on confirmation, drives the same lifecycle ([review])
- Given `/pr` invoked with no arguments and a clean working tree on the base branch, when it runs, then it interviews the user through `/interviewing` to establish the change before any mutation ([review])
- Given spec-tree work is destined for the default branch and no local lifecycle overlay changes the route, when `/pr` receives confirmation, then it runs the default lifecycle through `/committing-changes`, `/opening-pr`, `/managing-pr`, and post-merge closure through `/handoff --no-session` ([review])
- Given `spx/local/merging.md` exists and declares a no-PR route or a different PR lifecycle, when `/understanding` loads the foundation and `/pr` prepares its proposal, then that local overlay governs the lifecycle route instead of the default PR route ([test](tests/test_pr_orchestration.conformance.l1.py))
- Given `/pr` is invoked with an existing PR number, PR URL, or branch that already has an open PR, when it runs, then it delegates PR-state work to `/managing-pr` instead of opening another PR ([test](tests/test_pr_orchestration.conformance.l1.py))

### Conformance

- The `/pr` skill conforms to portable-skill packaging — a `SKILL.md` under `plugins/spec-tree/skills/pr/` that is user-invocable and reads free-form input through `$ARGUMENTS`, so it activates on both runtimes, per `spx/13-plugin-and-runtime-conventions.adr.md` ([test](tests/test_pr_orchestration.conformance.l1.py))
- The PR lifecycle protocol skills conform to internal-protocol packaging — `/opening-pr` and `/managing-pr` remain loadable by `/pr` while hidden from direct user invocation, and the direct `/open-pr` command wrapper is absent ([test](tests/test_pr_orchestration.conformance.l1.py))

### Compliance

- ALWAYS: present a proposal through the runtime's structured-question tool and obtain confirmation before any mutating action — branch creation, commit, push, PR open, or merge ([review])
- ALWAYS: drive the lifecycle by invoking the governing skills — `/applying` or the language coding skills for implementation, `/committing-changes`, `/opening-pr`, and `/managing-pr` — never reimplementing their protocols ([review])
- NEVER: merge directly — the merge executes only through `/managing-pr`'s `MERGE_READINESS` ∧ `PRODUCTION_READINESS` authority, per `spx/15-agent-pr-authority.pdr.md` ([review])

## Eval Coverage Model

When this node uses eval evidence, the eval suite covers these conversation cases:

- Argument instruction mode: a user asks `/pr` to implement and ship work, and the response proposes the default lifecycle before mutation.
- Existing changeset mode: a dirty working tree or branch ahead of base is treated as the thing to ship, and the proposal derives intent from the diff and commits.
- Empty mode: a clean base branch starts with `/interviewing`, not branch creation, committing, pushing, PR opening, or merging.
- Local lifecycle overlay mode: `spx/local/merging.md` changes the route, and `/pr` follows the overlay in its proposal and execution plan.
- Existing open PR mode: the branch already has a PR, or the user passes a PR number or URL, and `/pr` invokes the management protocol instead of opening a duplicate PR.
