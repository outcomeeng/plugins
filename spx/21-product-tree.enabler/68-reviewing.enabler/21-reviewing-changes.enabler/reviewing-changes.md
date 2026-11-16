---
id: 01a0ebd7-2062-7753-af29-fcc5f9112e6a
tier: prototype
malleability: spec
---

# Reviewing Changes

PROVIDES a verification skill that reviews a working changeset through a single shipped runner, records the review as a sealed `spx journal --type review` run, and returns the raw run token
SO THAT local reviewers, wrapper agents, and hosted integrations share one durable review record
CAN project the sealed journal into the surface they own without duplicating review rendering inside the skill

## Assertions

### Test.Scenario: runner start

- [start-run-state](tests/test_skill_orchestration.scenario.l2.py):
  - Given `SPX_VERIFY_BASE_REF` set in the environment
  - When `review_run.py start` runs
  - Then it uses that scope, computes the review-input bundle, opens the review journal, appends the scope-entered event, and returns run state including `runToken`, `statePath`, `diffPath`, `manifestPath`, and `changedFiles`
- [base-from-origin-head](tests/test_skill_orchestration.scenario.l2.py):
  - Given no `SPX_VERIFY_BASE_REF`, and `git symbolic-ref refs/remotes/origin/HEAD` resolves
  - When `compute_diff.py` resolves its base
  - Then `base_ref` is that symbolic ref reduced to its remote-tracking form `origin/<base>`, so a stale local branch ref cannot widen the diff
- [no-base-source](tests/test_skill_orchestration.scenario.l2.py):
  - Given no `SPX_VERIFY_BASE_REF` and no `refs/remotes/origin/HEAD` symbolic ref
  - When `compute_diff.py` runs
  - Then it exits non-zero with a stderr message naming both sources, so the operator can identify which to populate
- [head-from-env](tests/test_skill_orchestration.scenario.l2.py):
  - Given `SPX_VERIFY_HEAD_REF` set in the environment
  - When `compute_diff.py` resolves its head
  - Then `head_ref` is that value instead of the default `HEAD`
- [head-default](tests/test_skill_orchestration.scenario.l2.py):
  - Given no `SPX_VERIFY_HEAD_REF`
  - When `compute_diff.py` resolves its head
  - Then `head_ref` is the literal `HEAD`, because `head_ref` has a default and `base_ref` does not
- [four-sections](tests/test_skill_orchestration.scenario.l2.py):
  - Given committed feature changes, staged changes, unstaged changes, and untracked files in the working tree
  - When `compute_diff.py` builds the review input
  - Then it includes all four as labeled sections, so local review sees every change the next push or commit can carry
- [bundle-dir](tests/test_skill_orchestration.scenario.l2.py):
  - Given `compute_diff.py --bundle-dir <dir>`
  - When it runs
  - Then it writes a caller-owned scratch review-input bundle outside the git worktree containing `diff.md` and `manifest.json`, and stdout reports the two paths plus the diff byte count and section count, so the reviewer can read the diff with random access while durable review state remains journal-only
- [start-pins-head](tests/test_review_run_pinned_head.scenario.l1.py):
  - Given `SPX_VERIFY_HEAD_REF=FETCH_HEAD`, where `FETCH_HEAD` names a pull-request head one commit past `origin/<base>`, and a base fetch that rewrites `FETCH_HEAD` to the base tip
  - When `review_run.py start` runs
  - Then the run state's head identity is the pull-request head commit, and `changedFiles` lists exactly the paths that commit changes

### Test.Scenario: runner finish

- [finding-sealed](tests/test_skill_orchestration.scenario.l2.py):
  - Given one raised finding
  - When `review_run.py append-finding` and then `review_run.py finish` run
  - Then `append-finding` appends one finding-reported event through the journal, and `finish` appends a terminal run-completed event carrying review status and finding counts, seals the run, removes runner-owned scratch state, and returns only `runToken`
- [unexamined-refused](tests/test_skill_orchestration.scenario.l2.py):
  - Given a changed file that is neither a declared generated extent nor a pure rename and has no scope-advanced event and no unread mark
  - When `review_run.py finish` runs
  - Then it exits non-zero and names the unexamined files in stderr, so an incomplete review cannot be sealed
- [unread-file](tests/test_review_run_unread_file.scenario.l2.py):
  - Given `review_run.py finish --unread-file <path>` naming a file that lists one changed path per line
  - When `finish` runs
  - Then it marks each listed path as unread exactly as one `--unread` argument per path does, so an unread set of any size reaches the runner through one argument

### Test.Scenario: generated extents

- [no-declaration](tests/test_review_run_generated_extents.scenario.l2.py):
  - Given no `spx/local/generated-sources.toml` committed at the scope's base ref
  - When `review_run.py start` runs
  - Then it lists no declared generated extent and treats every changed file as an ordinary changed file
- [whole-file-extent](tests/test_review_run_generated_extents.scenario.l2.py):
  - Given a changeset whose changed files include a file that a relation's whole-file output pattern matches
  - When `review_run.py finish` runs
  - Then it records the file on the run-completed event as skipped by declaration together with its relation's regenerate command, appends no scope-advanced event and no unread mark for it, and seals a run whose only unexamined files are declared generated extents by its findings rather than as `failed`
- [generator-changed](tests/test_review_run_generated_extents.scenario.l2.py):
  - Given a changeset that changes a relation's declared source or generator together with a file that relation's whole-file output pattern matches
  - When `review_run.py start` and then `review_run.py finish` run
  - Then `start` flags that relation in the returned run state, so the reviewer judges the generator change with the extents as evidence it may read, and `finish` still requires neither a scope-advanced event nor an unread mark for the extent
- [declaration-at-base](tests/test_review_run_declaration_base.scenario.l2.py):
  - Given a repository whose `spx/local/generated-sources.toml` differs between the scope's base commit and the head or the working tree
  - When `review_run.py start` runs
  - Then the run state lists the relations and extents of the declaration as committed at the scope's base ref, so an edit at the head or in the working tree changes neither, and when the declaration is itself a changed path, `declaration-changed` governs exemption
- [declaration-changed](tests/test_review_run_declaration_changed.scenario.l2.py):
  - Given a changeset whose changed paths include `spx/local/generated-sources.toml`
  - When `review_run.py start` and then `review_run.py finish` run
  - Then `start` exempts no changed file from coverage by declaration and flags every relation in the returned run state with the changed declaration as the reason, and `finish` names the changed declaration on the run-completed event

### Test.Scenario: renames

- [pure-rename](tests/test_review_run_renames.scenario.l2.py):
  - Given a changeset that renames a file with git rename detection
  - When `review_run.py start` and then `review_run.py finish` run
  - Then the changed-file set lists the file once under its new path with its former path recorded, and `finish` records a rename with unchanged content on the run-completed event as renamed without content change, with no scope-advanced event and no unread mark for it
- [rename-with-content](tests/test_review_run_renames.scenario.l2.py):
  - Given a changeset that renames a file and changes its content
  - When `review_run.py finish` runs
  - Then it requires a scope-advanced event or an unread mark for the file under its new path, exactly as for any other changed file

### Test.Scenario: review result

- [parse-conforming](tests/test_review_result.scenario.l1.py):
  - Given a conforming review-result document
  - When `review_result.parse_json` reads it
  - Then it returns a `ReviewResult` dataclass
- [missing-key](tests/test_review_result.scenario.l1.py):
  - Given a document that omits a required key
  - When `review_result.parse_json` reads it
  - Then it raises `ReviewResultValidationError` naming the missing key
- [out-of-enum](tests/test_review_result.scenario.l1.py):
  - Given a finding whose `severity` or `concern` is outside its enum
  - When `review_result.parse_json` reads it
  - Then it raises `ReviewResultValidationError` naming the offending value and the allowed set
- [round-trip](tests/test_review_result.scenario.l1.py):
  - Given a `ReviewResult` instance
  - When `review_result.to_json_dict` writes it and `review_result.from_json_dict` reads the result back
  - Then the instance read back equals the instance written, with no loss

### Test.Mapping: [severity-wire](tests/test_review_result.mapping.l1.py)

Each `Severity` enum member maps to one wire value, and the enum holds no other member.

| Case     | Member     | Wire value |
| -------- | ---------- | ---------- |
| blocking | `BLOCKING` | `blocking` |
| debt     | `DEBT`     | `debt`     |

### Test.Mapping: [concern-wire](tests/test_review_result.mapping.l1.py)

The `Concern` enum members map to exactly five wire values.

| Case         | Wire value     |
| ------------ | -------------- |
| consistency  | `consistency`  |
| security     | `security`     |
| performance  | `performance`  |
| evidence     | `evidence`     |
| architecture | `architecture` |

### Test.Mapping: [projection-severity](tests/test_review_journal_emit.mapping.l1.py)

Each review severity maps to one severity of the shared run-journal projection, and the projection then owns terminal status rollup from the sealed prefix.

| Case     | Review severity | Projection severity |
| -------- | --------------- | ------------------- |
| blocking | `blocking`      | `reject`            |
| debt     | `debt`          | `warning`           |

### Test.Mapping: [finish-counts](tests/test_skill_orchestration.mapping.l2.py)

`review_run.py finish` maps each finding's severity to the terminal review count on the run-completed event that the finding increments.

| Case     | Finding                        | Count incremented |
| -------- | ------------------------------ | ----------------- |
| blocking | a rejecting `blocking` finding | `blocking`        |
| debt     | a warning `debt` finding       | `debt`            |

### Test.Mapping: [unit-and-tracked](tests/test_skill_orchestration.mapping.l2.py)

`review_run.py append-finding` maps a finding payload's optional `unit` and `tracked` fields onto the finding-reported event, carrying each field the payload holds and omitting each field it lacks, and `review_run.py finish` counts a `tracked` `debt` finding toward `debt` as it counts an untracked one.

| Case        | Payload fields       | Event data                     |
| ----------- | -------------------- | ------------------------------ |
| both-set    | `unit` and `tracked` | `unit` and `tracked`, verbatim |
| unit-only   | `unit`               | `unit`, verbatim               |
| both-absent | neither              | neither                        |

### Test.Mapping: [declared-extents](tests/test_review_run_generated_extents.mapping.l2.py)

`review_run.py start` reads the declaration `spx/local/generated-sources.toml` as committed at the scope's base ref (`git show <base>:spx/local/generated-sources.toml`), and maps each changed file to its listing in the manifest and the returned run state.

| Case               | Changed file                                           | Listing                                                                                                         |
| ------------------ | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| whole-file-match   | a file a relation's whole-file output pattern matches  | a declared generated extent under that relation, with the relation's sources, generator, and regenerate command |
| no-match           | a file no relation's whole-file output pattern matches | an ordinary changed file                                                                                        |
| declaration-absent | any file, with no declaration at the base              | an ordinary changed file, with no extent                                                                        |

### Test.Mapping: [render-count](tests/test_review_journal_emit.mapping.l1.py)

`journal_emit.py render` is a helper projection over sealed journal events for compatibility tests, while the live skill path returns only the run token; it maps each finding severity in the sealed prefix to the class its count line counts, such as `BLOCKING: 1, DEBT: 1` for one finding of each.

| Case     | Finding severity | Count-line class |
| -------- | ---------------- | ---------------- |
| blocking | `blocking`       | `BLOCKING`       |
| debt     | `debt`           | `DEBT`           |

### Test.Mapping: [rule-citation](tests/test_review_result.mapping.l1.py)

`Finding.rule` is a non-empty string whose form is a path-style citation into an existing rule in the product-tree or skill ecosystem, and each declared citation family maps to the parse the parser gives it.

| Case           | Citation form                                                                           | Parse    |
| -------------- | --------------------------------------------------------------------------------------- | -------- |
| spec-assertion | `spx/<path>:<MUST\|NEVER\|ALWAYS\|SCENARIO\|MAPPING\|CONFORMANCE\|PROPERTY\|AUDIT>:<n>` | accepted |
| decision       | a path to a product-tree ADR or PDR                                                     | accepted |
| plugin-skill   | `plugins/<plugin>/skills/<skill>/SKILL.md:<rule-slug>`                                  | accepted |
| agents-rule    | `AGENTS.md:<rule-slug>`                                                                 | accepted |
| claude-rule    | `CLAUDE.md:<rule-slug>`                                                                 | accepted |

### Test.Property: review result

- [lossless-serialization](tests/test_review_result.property.l1.py): For every valid `ReviewResult` instance, over an unbounded space of findings, `from_json_dict(to_json_dict(r)) == r`, so serialization is lossless

### Test.Compliance: runner boundaries

- [stale-base-relayed](tests/test_stale_base_relay.compliance.l1.py): ALWAYS: `review_run.py start` relays the shared resolver's stale-base refusal for a head behind the fetched `origin/<base>` tip — the dedicated exit code and the diagnostic, with no run state — before it opens a journal, so no review run records a tree that cannot merge
- [unfetchable-base](tests/test_stale_base_relay.compliance.l1.py): ALWAYS: `review_run.py start` reports a base it cannot fetch or resolve as one stderr diagnostic line carrying git's own message and a nonzero exit, with no run state and no traceback
- [empty-scope-stops](tests/test_review_run_empty_scope.compliance.l1.py): NEVER: `review_run.py start` opens a review journal for a scope whose committed, staged, unstaged and untracked sections hold no changed path; it exits nonzero with one stderr diagnostic naming the base and head commit ids and returns no run state, so no review seals a verdict over an empty diff
- [region-output-ordinary](tests/test_review_run_generated_extents.compliance.l2.py): NEVER: `review_run.py start` treats a region-bounded output of a relation — a `file` with `begin` and `end` markers — as a declared generated extent; the file stays an ordinary changed file that requires a scope-advanced event or an unread mark
- [scratch-only-writes](tests/test_reviewing_changes.compliance.l1.py): ALWAYS: scripts under `plugins/product-tree/skills/review-changes/scripts/` write no durable review state directly; `compute_diff.py` writes only the caller-owned scratch review-input bundle files, and `review_run.py` writes and removes only runner-owned scratch state
- [stdlib-only](tests/test_reviewing_changes.compliance.l1.py): NEVER: any script under `plugins/product-tree/skills/review-changes/scripts/` imports a third-party package, depends on `uv` at runtime, or imports any `outcomeeng_*` module — stdlib only per the Plugin Portability Constraints in `AGENTS.md`
- token-only-output: NEVER: the live `review-changes` skill path renders, summarizes, counts, or restates findings for the caller; caller-facing output is the raw run token

### Test.Compliance: identity and citations

- [commit-branch-identity](tests/test_review_branch_identity.compliance.l2.py): ALWAYS: a review whose branch value names a commit rather than a branch records the checked-out branch as its branch identity and slug, per [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md)
- [rule-citation-rejected](tests/test_review_result.compliance.l1.py): NEVER: `Finding.rule` is a free-form description, a required-action string, a repository-root review policy citation, a tracking-location string, a relative `SKILL.md:<rule-slug>` citation, or a citation whose file, assertion, or rule slug does not exist; the parser rejects each and names the offending value
- rendered-agent-tokens: ALWAYS: `review_result.py` takes the agent tokens of its generated-tree citation candidates from the data file the build renders beside it, and declares no agent token of its own

### Audit: scope and coverage

- read-before-advance: The review skill advances a changed file's scope only after reading the file, and marks every changed file it does not read as unread before it finishes, except a declared generated extent and a pure rename, which the runner accounts for without a scope-advanced event or an unread mark, per [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md).
- no-commit-branch-export: The reviewer agent never exports a commit as the branch identity for a commit-range input, per [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md).
- pr-head-pinned: For a pull-request reference, the wrapper agent resolves `FETCH_HEAD` to its full commit id with `git rev-parse` right after `git fetch origin pull/<n>/head`, and states that id as `SPX_VERIFY_HEAD_REF`; a pull-request review whose head assignment names `FETCH_HEAD` or another ref a later fetch can move fails the audit.
- consumer-scope: The review scope extends from changed files to every unchanged consumer of a changed governing declaration — a full-path citation of the changed decision or spec, a rendering or generated output the repository's declared generated-source relations derive from it, a consumer or specialization the loaded governance names, or a sibling specialization under a changed superset rule — discovered through read-only search bounded to those declared relationships and never through an unbounded repository-wide semantic search, with a contradiction reported as a `consistency` finding at the consumer's location.
- consumer-not-scope: Consumer discovery leaves the journal's scope coverage on the changed-file set; an inspected unchanged consumer is a finding site, never an `append-scope` unit, so a probe or consumer inspection that finds no defect appends no event and the finding-only journal contract holds.
- single-pass: Each pass against a given changeset surfaces every finding the changeset exhibits in that single pass; no pass carries continuity to another, and a finding missed on this pass has no second chance unless the diff itself changes.

### Audit: review prompt

- whole-diff: The review prompt instructs the reviewer to review the whole diff and to treat any caller-supplied scope, severity pre-filter, or emphasis as non-authoritative.
- adversarial-probes: The review prompt carries one domain-neutral `<adversarial_probes>` section the reviewer applies before treating a reviewed unit as clean — a counterexample probe that classifies constructed domain members through a universal, totality, or partition claim exactly as written; a conjunct-completeness probe that aligns derived, restated, or rendered text condition by condition with its cited source; a definite-description probe that resolves every newly introduced description or category name to its declaring owner in the loaded truth chain; and a blast-radius probe that follows a changed governing declaration into its consumers, checks the changed files themselves for retired terminology, and verifies closure claims against the resulting files — each observation attempted against its strongest plausible refutation before it becomes a finding, and each probe encoding no execution level, runner name, or node vocabulary.
- bundled-prompt-only: The `review-changes` skill prose loads only the bundled prompt at `${CLAUDE_SKILL_DIR}/references/review-prompt.md`; repository-root `REVIEW.md`, `REVIEW.example.md`, and other review prompt files are not review context.
- prompt-location: The swappable review prompt template lives at `plugins/product-tree/skills/review-changes/references/review-prompt.md`, and the skill prose loads it via `${CLAUDE_SKILL_DIR}/references/review-prompt.md`.
- existing-rule-cited: `Finding.rule` cites a rule that exists at the referenced location; the review prompt instructs the model to populate `rule` from rules declared in the loaded context and never to invent a citation.
- severity-rubric: Finding `severity` matches the rubric in `plugins/product-tree/skills/review-changes/references/review-prompt.md`: `blocking` for merge-safety defects, `debt` for real defects that do not jeopardize merge safety.
- issues-entry-keys: The review prompt instructs the Reviewer to read the `ISSUES.md` of each governing node of the changed files, to record with each finding its entry key — the path of the file it names, the label of the unit that encloses it, and its rule citation — and to label `TRACKED` each `debt` finding whose entry key an entry heading in that `ISSUES.md` carries.
- same-evidence-verdict: The review prompt fixes the criteria of the `evidence` concern, so two passes over an unchanged subject — the same unit text under the same governing context, at any head — raise the same `evidence` finding or none, and no pass reads another pass's verdict to reach its own.
- prompt-standalone: The review prompt is embedded in neither `SKILL.md` nor any script; it is one standalone markdown file at the declared reference path, so swapping the prompt touches no code.
- no-root-review-file: No repository-root `REVIEW.md` or `REVIEW.example.md` exists in this product checkout; local and CI review use the hidden prompt shipped by the `review-changes` skill.

### Audit: findings and surfaces

- finding-file-path: The `review-changes` skill writes each finding payload with the file-write tool to a file in the scratch directory the harness names for the session, copying that directory into the finding path character for character; when the file-write result reports a path the scratch directory does not contain by whole path components, it stops before `append-finding`, naming the reported path; it passes `append-finding` the path exactly as the file-write result reports it, written out literally; and when `append-finding` exits nonzero with a diagnostic that names the finding file absent, it runs `append-finding` once more with the path copied from the file-write result and, on a second failure, stops and reports the exit, the stderr and the run token; no finding path is retyped from memory.
- schema-module: The `review_result.py` policy module declares `SCHEMA_VERSION`, frozen `Finding` and `ReviewResult` dataclasses, and the `Severity` and `Concern` enums, so the canonical review-result schema lives in one Python module.
- findings-only-schema: The review-result schema carries no `summary`, acknowledgement, `decision`, or verdict field; a review produces findings only, and each consumer acts on a `blocking` finding by validity and phase and on a `debt` finding by its ruling, per [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md).
- runner-only-surface: The wrapper agent invokes the `review-changes` skill, and the skill uses only `review_run.py` as its command surface.
- observed-absence: The verification skill emits a `blocking` finding asserting absence of a file or fact only when the diff itself contains the deletion or omission, and asserts no missing artifact it cannot observe.
- stale-eval-history: No review raises a finding on the sole ground that an eval's `history.jsonl` records a run on an earlier commit than the head, because evaluate runs in CI only on an operator's dispatch, so the history file is a trend record and never a result the changeset owes, per `scope-by-type` in [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md).
- known-diffs: Known-clean diffs yield zero `blocking` findings, and known-broken diffs yield at least one `blocking` finding.
- journal-only-state: The wrapper agent writes no review artifact outside `spx journal`; durable review state is the sealed review journal prefix.
