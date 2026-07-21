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

- `work/sessions-test-evidence-ownership` carries the sessions evidence rewrite,
  the pickup claim-verifier fix, and the spec-tree plugin version bump the fix
  requires. No pull request or branch publication is assumed; re-derive branch,
  upstream, base, and PR state at pickup.
- The evidence contracts are re-established. Every linked assertion's case source
  is legitimate for its assertion type, every actual/expected pair draws its
  expectation from an owner outside the implementation path under test, and the
  three linked test files hold every predicate and assertion call.
- The oracle-coupling sweep is complete. The node-status expectation derives from
  the live `spx spec status --format json` projection rather than from any symbol
  the verifier also uses to produce its output; the refusal scenarios no longer
  read error-class names out of spec prose, which
  `spx/12-shipped-scripting.adr.md` routes to audit; and the git-ref cases arrange
  the conditions their assertions declare, including a branch literally named with
  40 hex characters and present on origin.
- Deterministic evidence passes on the current head: the node's three test files
  and the selected `just check` gate.

## Remaining work

### Deliver the slice

- Run `just check-full` once, after every applicable agentic gate converges on the
  same clean committed head. Any subsequent edit reopens the affected gates and
  invalidates that run.
- Invoke `/merge`; let the repository overlay select the GitHub pull-request
  transport.
- Open the sessions pull request only after `VERIFICATION_READINESS` holds, then
  manage current-head integration review and required checks through
  `MERGE_READINESS`.
- Merge with the repository-declared merge-commit command, complete the declared
  marketplace-source refresh, verify installed state, clean branch state, and close
  the session through `/handoff`.

Every test, build, or validation command first passes through `/wait-for-load`.

## First pickup action

Invoke `/understand`, then contextualize
`spx/21-spec-tree.enabler/76-sessions.enabler`, read this plan, and re-derive the
branch, base, and pull-request state before continuing delivery through `/merge`.
