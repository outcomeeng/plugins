# Plan: Hook Safety Validator

Created by `spx/15-hook-safety.pdr.md` (Hook Safety Contract). That PDR declares `[compliance]` testing rules over every plugin's hook configuration; this enabler is their implementation home, alongside the existing plugin-manifest, skill-frontmatter, and reference-portability validators.

## Next implementation step

Add a hook-safety validation check (a `32-*.enabler` child here) that scans every plugin's hook config across `dist/claude` and `dist/codex` and fails on:

- a hook registered on any blocking-capable event (PreToolUse, UserPromptSubmit, UserPromptExpansion, PermissionRequest, PostToolBatch, Stop, SubagentStop, PreCompact, or any other event where exit 2 / a deny-or-block decision / a timeout denies the agent's action);
- a hook entry with no explicit `timeout`;
- a hook command that is a bare script-file invocation at a substituted path with no inline fallback to a successful empty result;
- a hook command naming a version-pinned plugin cache path.

Tests are `[compliance]` evidence exercised against violating hook-config fixtures, per `spx/15-test-language.adr.md`. The check joins the `spx/15-validation.enabler/65-gate.enabler` pipeline.

## Scope: deterministic validator vs audit

This validator enforces the PDR's `### Testing` (`[compliance]`) rules only — the crisply falsifiable hook-config properties listed above. The PDR's `### Audit` rules are semantic command-shape and process properties that no reliable scan falsifies as declared, so they are verified by the PDR/hook audit, not this validator: inline-floor reachability across every branch, optional-dependency probing, kill-switch presence, last-resort justification, and distribution-version collapse. A hook can therefore pass this validator and still owe the audited properties — that split is intentional, not a gap. Strengthening any audited rule to `[compliance]` requires the contract to first mandate a scannable convention (for example a named kill-switch env var the validator can match); absent that, deterministic detection would mis-fire.

## Governing decision

`spx/15-hook-safety.pdr.md` — Testing assertions.
