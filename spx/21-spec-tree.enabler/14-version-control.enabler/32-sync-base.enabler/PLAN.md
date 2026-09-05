# Checkpoint recovery alignment

Governing decision: `spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`.

The declaration separates the synchronization primitive from the skill that owns checkpoint recovery. Complete the following implementation work before release:

1. Align `src/plugins/spec-tree/skills/sync-base/SKILL.md`: distinguish primitive outcomes from workflow completion, apply existing path-scoped authority, require successful `/commit-changes` completion before retry, and retain distinct authority, checkpoint, Git, and conflict failures. Replace blanket claims that every stop must be a conflict with the explicit authority and failure boundaries.
2. Check the checkpoint contract in `src/plugins/spec-tree/skills/commit-changes/SKILL.md` under `spx/21-spec-tree.enabler/73-committing.enabler`. Keep preservation commits available with `passing`, `failing`, or `not-run` verification; require passing evidence only for the later verification gate.
3. Align the context-loading consumer through `spx/21-spec-tree.enabler/18-context-loading.enabler/PLAN.md`, then inspect interview prerequisite handling under `spx/21-spec-tree.enabler/54-interview.enabler` without introducing caller-specific behavior into reusable skills.
4. Establish evidence through `/verify`: retain the real-Git primitive tests, audit the recovery contract, and route any structured behavioral regression through the producer's eval capability. Cover authorized dirty work with failing or absent verification, operator-owned work with and without authority, failed commits, and a current checkout with pending edits. A Markdown wording test does not prove recovery behavior.
5. Bump the plugin through `just bump`, regenerate both agent surfaces with `just build-skills`, run the skill/document checks, and complete the independent decision, spec, skill, and changeset gates before `/merge`.

The required pre-improvement `instructions_skill-auditor` dispatch returned HTTP 400: `The 'gpt-5.4' model is not supported when using Codex with a ChatGPT account.` The role produced no verdict. Resolve that dispatch capability or obtain an explicit process exception before treating the skill audit as satisfied; deterministic validation supplies no replacement verdict.
