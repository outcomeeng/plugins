# ISSUES — agents conversion enabler

Coordination note; not spec truth.

## DEBT [consistency]: reassess `permissionMode` mapping for plugin-shipped agents

`changes-reviewer` run `2026-07-03_15-20-18-970-ba8ba57733e4` and CI review comment `2026-07-03T15:40:38Z` raised that Claude Code plugin-shipped agents do not support `permissionMode` frontmatter, while this node still specifies and tests `permissionMode` to Codex `sandbox_mode` mapping.

The question is open, not settled. `PERMISSION_MODE_MAPPINGS` in `outcomeeng/distribution/agents.py` has since widened rather than narrowed — it gained `default`, `auto`, `dontAsk`, and `bypassPermissions` entries and a `Mapping[str, str | None]` annotation, so more source values now resolve through the converter than when the question was first raised. The mapping assertion in `agents.md` is unchanged. No decision record keeps or removes the surface.

Revisit condition: when structural work on `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler` is scheduled, decide whether `permission_mode`, `PERMISSION_MODE_MAPPINGS`, and the associated mapping tests belong in the plugin-agent conversion path or should be removed in favor of tool-derived Codex policy config only.

Deferral reason: removing or re-scoping `permissionMode` changes the converter's declared frontmatter surface and belongs with the planned agent-conversion boundary split above, not with a changeset that withdraws an unrelated protocol.

## Claude plugin renders bundle the never-invoked placement script

Every Claude-target `<plugin>-plugin` skill ships `scripts/place_agents.py`
even though its own SKILL.md states the script serves only the Codex
rendering and is never invoked there. Omitting it requires a
target-conditional emission rule in the build's projection — new projection
semantics with their own evidence — which is a separate, larger concern than
any single changeset touching the lifecycle skill.

**Resolution shape**: teach the emission projection to omit a bundled file
per target when the source declares it target-scoped, then drop the script
from the Claude renders.

**Revisit condition**: with the next change to the build's emission
projection.

**Evidence**: raised by the skill-authoring audit of the canonical
agent-registry changeset as a size/hygiene warning, not a correctness
defect.

## Codex composition probe returns no usable implementation-audit verdict

The Change #76 probe on subject
`6c64464abf07a2e384dabea0d3d0bc19a1b12956` completed installation,
authenticated through the repository-installation harness, launched exactly
one generated `spec-tree_implementation-auditor`, and observed the child read
`spec-tree:audit-implementation` plus the installed Go and Python concern
skills without searching for a dedicated tool named `Skill`.

The child then recorded every one of the changeset's 319 paths as an optional,
skipped `coverage-gap` unit. That set includes changed Python implementation
and test files. SPX run `2026-09-17_15-12-34-814-1080e7adf6da` consequently
sealed `approved` with zero findings without any path receiving an audited
concern result. The child's final answer, relayed unchanged by the parent,
contained only the run token; the generated implementation-auditor contract
requires the token and rendered projection.

This leaves two Change #76 probe observations unsatisfied: the child did not
produce concern-audit coverage for changed implementation files, and it did not
return the implementation-audit terminal-result contract. Retrying the same
probe result is prohibited by the Change.

**Settlement condition**: a generated Codex implementation auditor produces a
concern-audit result for every changed implementation path in its scope and
returns the run token with its rendered projection; the defect belongs to
implementation-audit orchestration, not to skill composition.

**Evidence**: SPX run `2026-09-17_15-12-34-814-1080e7adf6da`, sealed
`approved` with zero findings over 319 `coverage-gap` units, observed on Change
#76 subject `6c64464abf07a2e384dabea0d3d0bc19a1b12956`.
