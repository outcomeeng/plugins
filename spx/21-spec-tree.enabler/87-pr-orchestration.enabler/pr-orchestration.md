# PR Orchestration

PROVIDES a single user-facing entry point, the `/pr` skill, that drives a changeset from intent to merged through the governed lifecycle skills
SO THAT a developer on either runtime
CAN ship a change end to end — proposing, committing, opening, and merging — without invoking each lifecycle skill by hand

## Assertions

### Scenarios

- Given `/pr` invoked with arguments, when it runs, then it interprets the arguments as instructions, presents a proposal through the runtime's structured-question tool, and on confirmation drives the lifecycle by invoking `/committing-changes`, `/opening-pr`, and `/managing-pr` ([review])
- Given `/pr` invoked with no arguments and an existing changeset — uncommitted working-tree changes, or a branch ahead of its base — when it runs, then it derives the proposal from that changeset and, on confirmation, drives the same lifecycle ([review])
- Given `/pr` invoked with no arguments and a clean working tree on the base branch, when it runs, then it interviews the user through `/interviewing` to establish the change before any mutation ([review])

### Conformance

- The `/pr` skill conforms to portable-skill packaging — a `SKILL.md` under `plugins/spec-tree/skills/pr/` that is user-invocable and reads free-form input through `$ARGUMENTS`, so it activates on both runtimes, per `spx/13-plugin-and-runtime-conventions.adr.md` ([test](tests/test_pr_orchestration.conformance.l1.py))

### Compliance

- ALWAYS: present a proposal through the runtime's structured-question tool and obtain confirmation before any mutating action — branch creation, commit, push, PR open, or merge ([review])
- ALWAYS: drive the lifecycle by invoking the governing skills — `/applying` or the language coding skills for implementation, `/committing-changes`, `/opening-pr`, and `/managing-pr` — never reimplementing their protocols ([review])
- NEVER: merge directly — the merge executes only through `/managing-pr`'s `MERGE_READINESS` ∧ `PRODUCTION_READINESS` authority, per `spx/15-agent-pr-authority.pdr.md` ([review])
