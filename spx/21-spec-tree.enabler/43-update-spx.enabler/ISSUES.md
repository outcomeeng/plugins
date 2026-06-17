# Issues — update-spx

Known follow-ups for the update-spx node. Coordination note; not spec truth.

## Eval coverage for the /understand and /handoff orchestration (FOLLOW-UP)

The `/understand` once-per-session staleness check (version drift and language drift, including detecting the project's enabled languages) and the `/handoff` staleness-marker proposal are LLM-driven skill orchestration, so the spec backs them with `[audit]` compliance assertions rather than `[test]` evidence — per `spx/15-spec-coverage.adr.md`, LLM-driven behavior takes `[eval]` where the producer emits a structured verdict and `[audit]` otherwise. The deterministic core (version compare, language filter, render) carries `[test]` evidence; the orchestration layer does not.

**Resolution shape**: add `[eval]` coverage for the orchestration behaviors — `/understand` detecting the project's languages and emitting `<SPX_CLAUDE_STALE>` once per session against a version-drifted or language-drifted product, and `/handoff` carrying that marker into its persistence proposal — once an eval-harness path for skill-orchestration behavior is in place. Until then the `[audit]` lane stands. Surfaced by local review on `feat/update-spx` and `fix/spx-claude-template-render`.

## Structure-diagram product line shows an illustration token (FOLLOW-UP)

The rendered guide's Structure Overview shows `{product-slug}.product.md` as an illustration token rather than the product's actual root spec filename (for example `outcomeeng.product.md`). The Guide Render Model ADR accepts this: the render substitutes no per-product string, so the structure diagram teaches the pattern with placeholders (`{slug}`, `{product-slug}`) instead of concrete paths. A reader navigating to find the product spec root sees the pattern, not the path — a readability trade-off of the no-substitution model, recorded for a future reader; no action unless the diagram's pedagogy proves confusing in practice. Surfaced by local review on `fix/spx-claude-template-render`.

## Codex SKILL.md omits allowed-tools (expected, no action)

The generated `dist/codex/spec-tree/skills/update-spx/SKILL.md` carries no `allowed-tools` frontmatter key while the Claude variant does. This is the build's intended Codex output — the Codex plugin format has no `allowed-tools` field. Recorded so a future reader does not mistake the asymmetry for drift; no action required unless Codex tooling begins to consume the field.
