# Reviewing Changes

PROVIDES a verification skill that reviews a working changeset through a single shipped runner, records the review as a sealed `spx journal --type review` run, and returns the raw run token
SO THAT local reviewers, wrapper agents, and future hosted integrations share one durable review record
CAN project the sealed journal into the surface they own without duplicating review rendering inside the skill

## Assertions

### Scenarios

- Given `SPX_VERIFY_BASE_REF` set in the environment, `review_run.py start` uses that scope, computes the review-input bundle, opens the review journal, appends the scope-entered event, and returns run state including `runToken`, `statePath`, `diffPath`, `manifestPath`, and `changedFiles` ([test](tests/test_skill_orchestration.scenario.l2.py))
- Given no `SPX_VERIFY_BASE_REF` AND `git symbolic-ref refs/remotes/origin/HEAD` resolves, `compute_diff.py` uses that symbolic ref reduced to its remote-tracking form `origin/<base>` as `base_ref`, so a stale local branch ref cannot widen the diff ([test](tests/test_skill_orchestration.scenario.l2.py))
- Given no `SPX_VERIFY_BASE_REF` AND no `refs/remotes/origin/HEAD` symbolic ref, `compute_diff.py` exits non-zero with a stderr message naming both sources so the operator can identify which to populate ([test](tests/test_skill_orchestration.scenario.l2.py))
- Given `SPX_VERIFY_HEAD_REF` set in the environment, `compute_diff.py` uses that value as `head_ref` instead of the default `HEAD` ([test](tests/test_skill_orchestration.scenario.l2.py))
- Given no `SPX_VERIFY_HEAD_REF`, `compute_diff.py` uses the literal `HEAD` as `head_ref` — `head_ref` has a default; `base_ref` does not ([test](tests/test_skill_orchestration.scenario.l2.py))
- Given committed feature changes, staged changes, unstaged changes, and untracked files in the working tree, `compute_diff.py` includes all four as labeled sections in the review input so local review sees every change the next push or commit can carry ([test](tests/test_skill_orchestration.scenario.l2.py))
- Given `compute_diff.py --bundle-dir <dir>`, the script writes a caller-owned scratch review-input bundle outside the git worktree containing `diff.md` and `manifest.json`, and stdout reports the two paths plus the diff byte count and section count so the reviewer can read the diff with random access while durable review state remains journal-only ([test](tests/test_skill_orchestration.scenario.l2.py))
- Given one raised finding, `review_run.py append-finding` appends one finding-reported event through the journal and `review_run.py finish` appends a terminal run-completed event carrying review status and finding counts, seals the run, removes runner-owned scratch state, and returns only `runToken` ([test](tests/test_skill_orchestration.scenario.l2.py))
- Given `review_run.py finish` is called before every changed file has a scope-advanced event, `finish` exits non-zero and names the unexamined files in stderr so an incomplete review cannot be sealed ([test](tests/test_skill_orchestration.scenario.l2.py))
- `review_result.parse_json` returns a `ReviewResult` dataclass on a conforming document and raises `ReviewResultValidationError` on every violation — a missing required key, an unknown `severity` or `concern` value, or a malformed citation — naming the offending value ([test](tests/test_review_result.scenario.l1.py))
- `review_result.to_json_dict` and `review_result.from_json_dict` round-trip a `ReviewResult` instance without loss ([test](tests/test_review_result.scenario.l1.py))

### Mappings

- `Severity` enum members map to the wire values `blocking`, `debt` ([test](tests/test_review_result.scenario.l1.py))
- `Concern` enum members map to exactly the five wire values `consistency`, `security`, `performance`, `evidence`, `architecture` ([test](tests/test_review_result.scenario.l1.py))
- Review severities map into the shared run-journal projection as `blocking` -> `reject` and `debt` -> `warning`; the projection then owns terminal status rollup from the sealed prefix ([test](tests/test_review_journal_emit.mapping.l1.py))
- `review_run.py finish` maps finding severities into terminal review counts on the run-completed event: rejecting findings increment `blocking`, warning findings increment `debt` ([test](tests/test_skill_orchestration.scenario.l2.py))
- `journal_emit.py render` remains a legacy helper projection over sealed journal events for compatibility tests, while the live skill path returns only the run token ([test](tests/test_review_journal_emit.mapping.l1.py))

### Properties

- For every `ReviewResult` instance, `from_json_dict(to_json_dict(r)) == r` — serialization is lossless ([test](tests/test_review_result.property.l1.py))

### Audit

- ALWAYS: the `review_result.py` policy module declares `SCHEMA_VERSION`, frozen `Finding` and `ReviewResult` dataclasses, and the `Severity` and `Concern` enums — the canonical legacy review-result schema lives in one Python module ([test](tests/test_review_result.scenario.l1.py))
- NEVER: the review-result schema carries a `summary`, acknowledgement, `decision`, or verdict field — a review produces findings only; each consumer applies its own policy by validity and phase per `spx/15-merging.pdr.md`, never by severity ([test](tests/test_review_result.scenario.l1.py))
- ALWAYS: the review prompt instructs the reviewer to review the whole diff and to treat any caller-supplied scope, severity pre-filter, or emphasis as non-authoritative ([audit])
- ALWAYS: the `review-changes` skill prose loads only the bundled prompt at `${CLAUDE_SKILL_DIR}/references/review-prompt.md`; repository-root `REVIEW.md`, `REVIEW.example.md`, and other review prompt files are not review context ([audit])
- ALWAYS: scripts under `plugins/spec-tree/skills/review-changes/scripts/` write no durable review state directly; `compute_diff.py` may write only the caller-owned scratch review-input bundle files, and `review_run.py` may write and remove runner-owned scratch state ([test](tests/test_reviewing_changes.audit.l1.py))
- ALWAYS: the swappable review prompt template lives at `plugins/spec-tree/skills/review-changes/references/review-prompt.md` and the skill prose loads it via `${CLAUDE_SKILL_DIR}/references/review-prompt.md` ([audit])
- ALWAYS: `Finding.rule` is a non-empty string whose form is a path-style citation into an existing rule in the spec-tree or skill ecosystem — `spx/<path>:<MUST\|NEVER\|ALWAYS\|SCENARIO\|MAPPING\|CONFORMANCE\|PROPERTY\|AUDIT>:<n>`, a path to a spec-tree ADR/PDR, `plugins/<plugin>/skills/<skill>/SKILL.md:<rule-slug>`, `AGENTS.md:<rule-slug>`, or `CLAUDE.md:<rule-slug>`. `rule` is never a free-form description, a required-action string, a repository-root review policy citation, or a tracking-location string ([test](tests/test_review_result.scenario.l1.py))
- ALWAYS: `Finding.rule` cites a rule that actually exists at the referenced location — the review prompt instructs the model to populate `rule` from rules declared in the loaded context, never to invent a citation ([eval](evals/judgment-grounding/eval.toml))
- ALWAYS: the wrapper agent invokes the `review-changes` skill and the skill uses only `review_run.py` as its command surface ([eval](evals/wrapper-protocol/eval.toml))
- ALWAYS: the verification skill emits a `blocking` finding asserting absence of a file or fact only when the diff itself contains the deletion or omission — the verification skill does not hallucinate missing artifacts it cannot observe ([eval](evals/judgment-grounding/eval.toml))
- ALWAYS: finding `severity` matches the rubric in `plugins/spec-tree/skills/review-changes/references/review-prompt.md` — `blocking` for merge-safety defects, `debt` for real defects that do not jeopardize merge safety ([eval](evals/severity-classification/eval.toml))
- ALWAYS: each pass against a given changeset surfaces every finding the changeset exhibits in that single pass — there is no cross-pass continuity, and a finding missed on this pass has no second chance unless the diff itself changes ([audit])
- NEVER: any script under `plugins/spec-tree/skills/review-changes/scripts/` imports a third-party package, depends on `uv` at runtime, or imports any `outcomeeng_*` module — stdlib only per the Plugin Portability Constraints in `AGENTS.md` ([test](tests/test_reviewing_changes.audit.l1.py))
- NEVER: the wrapper agent writes review artifacts outside `spx journal`; durable review state is the sealed review journal prefix ([eval](evals/wrapper-protocol/eval.toml))
- NEVER: the review prompt is embedded inside `SKILL.md` or any script — the prompt is one standalone markdown file at the declared reference path so swapping the prompt does not require touching code ([audit])
- NEVER: repository-root `REVIEW.md` or `REVIEW.example.md` exists in this product checkout — local and CI review use the hidden prompt shipped by the `review-changes` skill ([audit])
- NEVER: the live `review-changes` skill path renders, summarizes, counts, or restates findings for the caller; caller-facing output is the raw run token ([test](tests/test_skill_orchestration.scenario.l2.py))
