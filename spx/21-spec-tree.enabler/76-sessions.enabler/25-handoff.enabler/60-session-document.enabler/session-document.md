# Session Document

PROVIDES the content contract of a session document — the frontmatter that surfaces in the queue, the repository pointers the next agent re-derives from, and the external state it cannot re-derive
SO THAT an agent claiming the document
CAN initialize from durable truth rather than from a narrative of what the previous session did

## Assertions

### Compliance

- ALWAYS: the `/handoff` skill presents `spx session handoff` payload input by supported harness environment — quoted heredoc for interactive Claude Code and Codex sessions, and one physical `printf '%s\n' ... | spx session handoff` line for programmatic runners that require single-line commands — per `spx/15-agent-tools.pdr.md` ([audit])
- ALWAYS: a `/handoff` session document's `goal` frontmatter names the session's deliverable or target end-state in output-shaped wording, while `next_step` names the imperative first action for pickup, so `spx session list` and `spx session todo` surface what the continuation produces rather than a generic activity verb ([audit])
- ALWAYS: a `/handoff` session document initializes the next agent through repository-derived pointers — the anchored node paths and the first action — so the next agent re-derives detail and skill choices from the spec tree rather than from the session file ([audit])
- ALWAYS: when external infrastructure holds state the next agent cannot re-derive from the spec tree, PLAN.md/ISSUES.md, or git history — live PR, run, image, or job identifiers and their status, deployed inventories, in-flight workflows — the `/handoff` session document records that observable state and guides the next pickup from it in prose ([audit])
- NEVER: structure a `/handoff` session document as a retrospective, changelog, activity log, or duplicate of PLAN.md/ISSUES.md, or encode the next pickup's decision as fixed if-then branches — the document points at durable truth and records only the external state the next agent cannot re-derive ([audit])
