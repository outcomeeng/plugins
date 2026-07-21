# Plan: trustworthy sessions test evidence

## Selected slice

The executable slice contains one existing node:

- `spx/21-spec-tree.enabler/76-sessions.enabler`

The slice delivers sessions evidence whose linked assertion files own every
predicate while harnesses expose observations and generators supply legitimate
variable domains. A change that breaks handoff and pickup behavior, claim-to-verdict
mapping, or node-status projection must fail the linked test without a matching
harness change and without an expected result derived from the implementation path
that produced the actual result.

The observable path is:

1. A maintainer runs the sessions node's deterministic evidence against generated
   session payloads, temporary git repositories, the real `spx session` CLI, and
   the shipped pickup claim verifier.
2. Harnesses arrange resources and return raw command, filesystem, git, runner,
   and verifier observations.
3. The linked test files apply the predicates declared by
   `spx/21-spec-tree.enabler/76-sessions.enabler/sessions.md`.
4. A broken session transition, ref-reachability result, claim relation, or
   node-status projection produces a focused assertion failure.
5. The committed changeset is inspected through the test-evidence audit,
   implementation audit, changeset review, deterministic gate, and pull request.

## Current state

- `work/sessions-test-evidence-ownership` contains the sessions evidence rewrite and
  is rebased on the current `origin/main`.
- The branch patch is unchanged by the latest base synchronization and has no path
  overlap with the base delta.
- The merged testing standards invalidate the branch's earlier audits, review, and
  readiness evidence. All current-head gates must run again.
- The former `ISSUES.md` item describing the initial infrastructure extraction is
  resolved by the committed generator and harness split; the issue file remains
  removed.
- No pull request or branch publication is assumed. Re-derive branch, upstream,
  base, and PR state at pickup.

## Remaining work

### 1. Re-establish the evidence contracts

- Invoke `/apply` for the selected single-node slice and load `/test`,
  `/test-python`, `/code-python`, and their shared standards before edits.
- For every linked assertion, answer the production-behavior, proof, and failure
  questions from `/test` and record the assertion type's legitimate case source.
- Apply the inversion check to every imported infrastructure seam: reversing a
  linked assertion must not require or induce a harness or generator change.
- Apply the oracle-independence check to every actual/expected pair: mutating the
  implementation path that produces the actual value must not mutate the expected
  value through shared logic or metadata.
- Apply the case-provenance check to every input and expected output: scenario cases
  come from the spec assertion, mapping cases from complete source-owned finite
  domains, compliance cases from the governing rule, and variable domains from
  meaningful generators.

### 2. Remove coupled oracles and hidden predicates

- Replace the node-status scalar-field expectation that currently derives both the
  arranged payload and expected projection from `NODE_STATUS_SCALAR_FIELDS` with an
  independent contract derived from the governing assertion or another owner that
  does not drive verifier output.
- Sweep claim-relation mapping, origin-branch reachability, session transition,
  error-name, command-prefix, metadata-loading, and read-only checks for the same
  actual/expected coupling class.
- Keep behavioral predicates and assertion APIs in the three linked test files.
  Harnesses may validate their own observation contracts but must not return a
  pass/fail verdict for a sessions assertion.
- Keep production vocabulary and finite domains in production source, resource and
  command execution in harnesses, meaningful variable domains in generators, and
  inert whole-payload data in fixture files only when a real payload is the case.
- Improve the pickup verifier's production contract before changing a test when an
  independent oracle requires a missing enum, schema, registry, constructor,
  protocol, or typed observation boundary.

### 3. Regenerate and establish deterministic evidence

- Run `just clean` before verification.
- Format every changed Python or Markdown file with the repository recipes selected
  by `AGENTS.md`.
- Regenerate `dist/claude/` and `dist/codex/` with `just build-skills` after any
  authored pickup-skill source change.
- Recalculate the required plugin version bump against the current base with
  `just bump-dry origin/main`, apply the required bump, and regenerate.
- Run the three linked sessions test files through `just test`.
- Run `just check` against the resulting changed-path selection.
- Commit a clean deterministic-passing checkpoint through `/commit-changes`.

Every test, build, or validation command first passes through `/wait-for-load`.

### 4. Converge isolated verification

- Dispatch `test-evidence-auditor` for the three sessions assertion files and their
  complete imported generator and harness chain.
- Dispatch `implementation-auditor` for the committed changeset after deterministic
  verification passes.
- Dispatch `changes-reviewer` with raw scope `HEAD`, render its sealed review journal
  through `/project-run-journal`, and resolve every valid bounded finding as a
  defect class across the touched node.
- After each repair, rerun affected deterministic evidence, create a new checkpoint
  commit, and repeat every invalidated agentic gate against the new head.
- Run `just check-full` once, after all applicable agentic gates converge on the same
  clean committed head. Any subsequent edit reopens the affected gates.

### 5. Deliver the slice

- Invoke `/merge`; let the repository overlay select the GitHub pull-request
  transport.
- Open the sessions pull request only after `VERIFICATION_READINESS` holds, then
  manage current-head integration review and required checks through
  `MERGE_READINESS`.
- Merge with the repository-declared merge-commit command, complete the declared
  marketplace-source refresh, verify installed state, clean branch state, and close
  the session through `/handoff`.

## First pickup action

Invoke `/understand`, then contextualize
`spx/21-spec-tree.enabler/76-sessions.enabler`, read this plan, and resume `/apply`
with the oracle-independence sweep beginning at the node-status scalar-field
evidence.
