# ISSUES — Authoring

Known issues for the `/authoring` skill node. Coordination note: verify each entry against the current
skill, decisions, tests, and intent before acting.

## `/authoring` (and other delegating skills) may lack `Skill` in allowed-tools

`src/plugins/spec-tree/skills/authoring/SKILL.md` declares `allowed-tools: Read, Glob, Grep, Write,
Edit` — no `Skill` — yet `/authoring` chains into `/contextualizing` (and the methodology has it hand
off to `/decomposing`). PR #113 fixed the identical gap in `/bootstrapping`, where a Codex CI review
flagged it `BLOCKING`: without `Skill` in `allowed-tools`, the mandated skill delegation cannot fire.
Any skill that invokes another skill in its body while restricting `allowed-tools` without listing
`Skill` carries the same latent defect.

**Verify first:** confirm whether `allowed-tools` actually blocks the `Skill` tool at runtime. The
pre-change `/bootstrapping` used `AskUserQuestion` without listing it and appeared to work, which
suggests some tools may be available regardless — establish the enforcement model before a broad sweep.

**Resolution shape:** sweep `src/plugins/spec-tree/skills/*/SKILL.md` (and the language plugins) for
skills that invoke `Skill(...)` or instruct invoking another skill while their `allowed-tools` omits
`Skill`; add `Skill` to each. Consider encoding the rule in `develop:standardizing-skills`: a skill
that delegates to another skill MUST list `Skill` in `allowed-tools`.

Surfaced during PR #113 (archetype library) closing reflection, 2026-06-04.
