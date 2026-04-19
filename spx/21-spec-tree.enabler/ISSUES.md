# Issues: Spec Tree Enabler

Issues discovered during contradiction analysis of `spx/EXCLUDE`, sync-exclude, and the quality gate mechanism. Source: `methodology/skills/skill-structure.md` stale content + cross-file contradiction audit.

## ~~1. State terminology disagrees across three layers~~ (FIXED)

Fixed: `methodology/skills/skill-structure.md` now uses "Declared / Specified / Failing / Passing" matching `durable-map.md`. Also replaced "three phases: spec-tree maintenance, implementation, commit" with "three steps: declare, spec, apply" across all docs and skills. Upstream `outcomeeng/methodology` repo still needs updating.

## ~~2. spx CLI must own all quality gate concerns~~ (FIXED)

Fixed: `excluded-nodes.md` and `sync-exclude.md` rewritten to describe `spx` CLI as quality gate owner. Skills updated. Commit `30cb7b7`.

## ~~3. Spec-tree must never write project config files~~ (FIXED)

Fixed: `excluded-nodes.md` states "No config manipulation" and `sync-exclude.md` has NEVER compliance assertion. Commit `30cb7b7`.

## ~~4. `excluded-nodes.md` falsely claims language plugins own sync implementation~~ (FIXED)

Fixed: `excluded-nodes.md` rewritten — no language plugin references remain. Commit `30cb7b7`.

## ~~5. `sync-exclude.md` spec overpromises reusability~~ (FIXED)

Fixed: spec rewritten — now says "SO THAT spec-tree projects in any language CAN..." and describes `spx` CLI invocation logic. Commit `30cb7b7`.

## ~~6. TypeScript plugin has zero EXCLUDE support~~ (FIXED)

Fixed: `spx` CLI owns quality gate and is language-agnostic — `spx test passing` works for any language. Commit `30cb7b7`.

## ~~7. Conflicting sync commands across Python skills~~ (FIXED)

Fixed: all `sync-exclude` references removed from plugins. Zero matches remain. Commit `30cb7b7`.

## 8. Multi-language test discovery missing from methodology (PARTIAL)

Multi-language discovery is documented in `excluded-nodes.md` and `sync-exclude.md` spec (mapping assertions for pytest/vitest). The `status.yaml` reference in `testing-foundation.md` was removed in commit `391e9e5`.

**Remaining:** upstream `outcomeeng/methodology` repo still needs the multi-language principle added to `spec-tree-reference.md`.

## 9. `committing-changes` references `just check`

`skill-structure.md` line 457: "Run project validation (e.g., `just check`)." Should reference `spx` validation as the spec-tree quality gate. `just check` is the project's own concern, separate from spec-tree.

## 10. Spec headers diverged from upstream methodology

Plugin uses `PROVIDES ... SO THAT ... CAN ...` and `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`. Upstream `outcomeeng/methodology/reference/spec-tree-reference.md` uses `## Enables...` and `## We believe that...`. Plugin leads; upstream needs to catch up.

## 11. Upstream methodology still references `spx-lock.yaml`

`outcomeeng/methodology/reference/spec-tree-reference.md` lines 86-108 describe a lock-file model (`spx-lock.yaml`, blob hashes, "Needs work / Stale / Valid" states) that the plugin replaced with the EXCLUDE + derived-state model. The upstream needs to be rewritten to match.
