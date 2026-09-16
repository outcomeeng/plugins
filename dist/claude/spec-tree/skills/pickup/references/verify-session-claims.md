<objective>

The executable contract for the read-only session-claim verifier used by the
pickup workflow.

</objective>

<inputs>

Invoke `python3 "${CLAUDE_SKILL_DIR}/scripts/verify_session_claims.py"
<claimed-session-id> --repo <repo-root>`. The session id addresses the published
`spx session show` contract. The optional repository root defaults to the current
working directory.

The verifier reads `git_ref`, `specs`, and `files` from `spx session show --json`.
It reads an optional `git_status` claim and pull-request references from the
plain session document. Paths must be non-empty, relative to the checkout, and
must not contain a parent-directory escape.

The repository root must exist, be an accessible directory, and contain its
`.git` repository metadata entry. An invalid root exits nonzero before any
observation and names the rejected path on standard error.

</inputs>

<output>

A successful reconciliation writes one JSON array to standard output. Every
element has four fields:

- `kind` — `session_metadata`, `git_ref`, `injected_path`, `node_status`,
  `uncommitted_state`, or `external_id`.
- `subject` — the session id, reference, path, node id, recorded tree state, or
  pull-request number being reconciled.
- `verdict` — `Confirmed`, `Discrepancy`, or `Unverifiable`.
- `evidence` — the observed state or the reason the observation could not run.

`Confirmed` means a comparable claim matches current state or an observation-only
claim surfaced its current value. `Discrepancy` means a comparable claim differs.
`Unverifiable` means the required observation could not be established. A
reconciliation containing `Unverifiable` verdicts still exits successfully so
the workflow can present every result and decide how to continue.

</output>

<tested_cases>

The claim-verification node's mapping and compliance evidence covers:

- branch and commit references that are reachable, absent, unavailable, or fail
  with a fatal Git status;
- injected spec and file paths that are present or absent;
- projected node records, absent nodes, and unavailable or malformed projections;
- matching and changed clean or dirty working-tree state;
- observed pull-request state and failed pull-request reads;
- unavailable `spx session show` calls and malformed JSON;
- empty, multiple, or non-object session records;
- absent required fields, an invalid `git_ref`, invalid path-list shapes, and
  absolute, empty, or parent-escaping paths;
- use of the injected command runner, stdlib-only imports, source-owned read-only
  commands, and unchanged repository status across verification.
- rejection of a missing repository root, a non-directory path, and a directory
  without repository metadata before any observation runs.

An unloadable session produces exactly one `session_metadata` verdict with
`Unverifiable`. An unavailable observation produces `Unverifiable` for that
claim. A missing path or unreachable valid reference produces `Discrepancy`.

</tested_cases>
