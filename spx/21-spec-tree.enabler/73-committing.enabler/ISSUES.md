# Issues: Committing

Coordination note; not spec truth.

## Two scenarios carry interim `[audit]` tags in place of their declared evidence lanes

The `### Scenarios` assertions on splitting a multi-plugin staging set and on Conventional Commits conformance linked a test file that was never written. Both now carry `[audit]` as an explicit interim so no evidence link dangles, which departs from the lanes `spx/15-spec-coverage.adr.md` assigns: the split recommendation is LLM-driven skill behavior and belongs on `[eval]`; the message-format check is a deterministic function of a string and belongs on `[test]`. The interim tag was an operator decision (2026-09-07) that chose recording the gaps over building evidence in the changeset that retired `spx/EXCLUDE`.

**Resolution shape.** For the split recommendation, author an eval suite under `evals/` with `/commit-changes` (`src/plugins/spec-tree/skills/commit-changes/SKILL.md`) as the producer and cases for single-plugin and multi-plugin staging sets, then restore the `[eval](evals/…/eval.toml)` tag. For the format check, the skill ships no validator: either add a stdlib Conventional Commits validator the skill invokes and link a `[test]` under `tests/`, or, if no validator is wanted, reword the assertion as the skill's instruction and keep `[audit]`. Route each through `/verify`.

**Evidence.** Surfaced by the CI changeset review on PR #562 (head `812ed0ea12dc481f6abd54d4d7d21f20873068a9`), which found this node alone among the retagged nodes without a recorded rationale.
