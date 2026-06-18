# Plan: Hook Safety Validator

Created by `spx/15-hook-safety.pdr.md` (Hook Safety Contract). That PDR declares `[compliance]` testing rules over every plugin's hook configuration; this enabler is their implementation home, alongside the existing plugin-manifest, skill-frontmatter, and reference-portability validators.

## Status

The validator node `spx/15-validation.enabler/32-hook-safety.enabler` is built: `outcomeeng/validation/hook_safety.py` (an allowlist of non-blocking events plus checks for an explicit `timeout`, a guarded command shape, and version-pinned cache paths) with `[compliance]` and `scenario` evidence under the node's `tests/`. The pytest gate enforces it.

## Remaining step

Wire the validator CLI (`python3 -m outcomeeng.validation.hook_safety`) into the `spx/15-validation.enabler/65-gate.enabler` `STEPS` pipeline so the gate scans the live `dist/claude` and `dist/codex` trees on every run. This step is deferred to the change that rewrites the spec-tree `SessionStart` hook to the inline-guard form (see `spx/21-spec-tree.enabler/PLAN.md`): the validator already flags the current hook (no explicit `timeout`, bare substituted-path invocation), so adding the gate step before the hook conforms would fail `just check`. Wire the step and the hook fix together.

## Scope: deterministic validator vs audit

This validator enforces the PDR's `### Testing` (`[compliance]`) rules only — the crisply falsifiable hook-config properties listed above. The PDR's `### Audit` rules are semantic command-shape and process properties that no reliable scan falsifies as declared, so they are verified by the PDR/hook audit, not this validator: inline-floor reachability across every branch, optional-dependency probing, kill-switch presence, last-resort justification, and distribution-version collapse. A hook can therefore pass this validator and still owe the audited properties — that split is intentional, not a gap. Strengthening any audited rule to `[compliance]` requires the contract to first mandate a scannable convention (for example a named kill-switch env var the validator can match); absent that, deterministic detection would mis-fire.

## Governing decision

`spx/15-hook-safety.pdr.md` — Testing assertions.
