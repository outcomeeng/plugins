# Issues — update-spx

Known follow-ups for the update-spx node. Coordination note; not spec truth.

## Eval coverage for the /understanding and /handoff orchestration (FOLLOW-UP)

The `/understanding` once-per-session staleness check and the `/handoff` staleness-marker proposal are LLM-driven skill orchestration, so the spec backs them with `[audit]` compliance assertions rather than `[test]` evidence — per `spx/15-spec-coverage.adr.md`, LLM-driven behavior takes `[eval]` where the producer emits a structured verdict and `[audit]` otherwise. The deterministic core (version compare, merge, scaffold) carries `[test]` evidence; the orchestration layer does not.

**Resolution shape**: add `[eval]` coverage for the two orchestration behaviors — `/understanding` emitting `<SPX_CLAUDE_STALE>` once per session against a drifted product, and `/handoff` carrying that marker into its persistence proposal — once an eval-harness path for skill-orchestration behavior is in place. Until then the `[audit]` lane stands. Surfaced by local review on `feat/update-spx`.

## Runtime-aware spx-level guide naming (FOLLOW-UP)

The spx-level guide is `spx/CLAUDE.md` under Claude and `spx/AGENTS.md` under Codex (where `spx/CLAUDE.md` is often a symlink to `spx/AGENTS.md`). `/update-spx` and `/understanding`'s drift check resolve the existing guide path, but `bootstrapping` step 3 hardcodes `--product spx/CLAUDE.md` when it scaffolds a new guide — so a Codex-only consumer with `spx/AGENTS.md` and no symlink would get a second `spx/CLAUDE.md` created instead of its `spx/AGENTS.md`.

**Resolution shape**: decide the runtime→guide-name mapping (Claude → `spx/CLAUDE.md`, Codex → `spx/AGENTS.md`) once and apply it across `bootstrapping`, `/update-spx`, and `/understanding` so scaffold and update target the same runtime-appropriate file. Until then, bootstrapping scaffolds `spx/CLAUDE.md`. Surfaced by local review on `feat/update-spx`.

## Codex SKILL.md omits allowed-tools (expected, no action)

The generated `dist/codex/spec-tree/skills/update-spx/SKILL.md` carries no `allowed-tools` frontmatter key while the Claude variant does. This is the build's intended Codex output — the Codex plugin format has no `allowed-tools` field. Recorded so a future reader does not mistake the asymmetry for drift; no action required unless Codex tooling begins to consume the field.
