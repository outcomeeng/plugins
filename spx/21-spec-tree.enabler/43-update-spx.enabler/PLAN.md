# PLAN — two-file deterministic guide generation

Coordination note; not spec truth. Reconcile before use.

## Objective

The product's spx-level agent guide must exist as **two checked-in files** in the
product's own `spx/` directory, because one repository is worked by multiple agents
concurrently and each reads its own filename:

- `spx/CLAUDE.md` — read by Claude Code
- `spx/AGENTS.md` — read by Codex

`spx/` is a fixed on-disk directory, not a per-runtime plugin render: both agents see the
same directory, so both files must be present, each carrying runtime-appropriate content.
Today the renderer emits only `CLAUDE.md`; this repo symlinks `CLAUDE.md` → `AGENTS.md`, so
Codex gets the Claude-shaped guide and never its own — notably the mandatory auditor-subagent
rules Codex needs because it tends to keep working in the main context instead of spawning the
auditor agent.

## Design (confirmed)

1. **Single source, two outputs.** Render the one canonical template once per runtime:
   `target=claude` → `spx/CLAUDE.md`, `target=codex` → `spx/AGENTS.md`. Runtime-divergent
   content lives in the single source as conditional/token spans: the Codex auditor-subagent
   mandate, the runtime tool names (`AskUserQuestion` ↔ `request_user_input`), and the
   self-referential guide filename (`CLAUDE.md` ↔ `AGENTS.md`).
2. **Fully deterministic — no LLM.** Verified: the render is pure string transformation;
   staleness is dotted-version + language-set compare (`--check` already); language detection
   reads the distinct test-file extensions under `spx/**/tests/` (the in-use ground truth —
   `.py` here, matching the recorded `languages: [python]`). Nothing needs agent judgment.
3. **Gate, not skill.** A `just`/lefthook regenerate-and-diff step keeps both files current,
   the same contract as `dist-diff`. Retire the `/update-spx` skill, the `/understand`
   once-per-session staleness marker, and the `/handoff` marker plumbing.
4. **Generator stays a shipped stdlib-only skill script** (`update_spx.py`), evolved in
   place — no `spx`-CLI dependency, ships immediately.

## Spec changes (truth-first, same change)

- Amend `21-render-model.adr.md`: the guide is two files per product (one per agent runtime)
  from a single source rendered per-runtime; runtime is a variation axis alongside language;
  generation is deterministic (no agent judgment); language detection is read from
  `spx/**/tests/` extensions.
- Align `update-spx.md` assertions: render emits both `CLAUDE.md` and `AGENTS.md`; per-runtime
  divergence; deterministic language detection; gate integration; drop the `[audit]`
  LLM-orchestration assertions for `/understand` and `/handoff` staleness (the orchestration is
  retired).

## Implementation steps

1. `update_spx.py`: render both files from one template with a `target` parameter; auto-detect
   languages from `spx/**/tests/` extensions; staleness over both output files.
2. Template `understand/templates/spx-claude.md`: author the runtime-divergent spans (Codex
   auditor-subagent section, filename and tool self-references). Consider a runtime-neutral
   template filename.
3. Gate: `just` recipe + lefthook step regenerate both files and fail on drift.
4. Retire the `/update-spx` SKILL, the `/understand` staleness workflow step + success
   criteria, and the `/handoff` marker handling.
5. Tests: two-output render, per-runtime divergence, language detection from extensions, gate
   drift behavior.

## Gates

`adr-auditor` (ADR), `spec-auditor` (`update-spx.md`), `test-evidence-auditor` (tests),
`develop:skill-auditor` (edited SKILLs), `just check`, then `/merge`.
