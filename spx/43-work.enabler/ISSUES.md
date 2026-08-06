# ISSUES — work enabler

Known unresolved gaps. `/contextualize` reads this file at context-load time; remove entries as they resolve.

## Audit dimensions 2–6 lack scenario assertions

`spx/43-work.enabler/work.md` declares one scenario for dimension 1 (orphan-layout detection) plus one conformance assertion for `pptx_repack.py`. The remaining five audit dimensions in `pptx_audit.py` — `layout_types()`, `fonts()`, `colors()`, `naming()`, `trim()` (~135 lines of audit logic in total) — are applied without a prior declare step.

**Resolution shape**: a follow-on PR that adds one scenario assertion per dimension to `work.md` with a matching pytest case under `spx/43-work.enabler/tests/`. The harness's `minimal_parts` builder already covers the structural shape; each new assertion needs a focused parts variation (a layout typed `cust` with empty `spTree` for dim 2; a non-theme `<a:latin typeface=...>` inside a slide for dim 3; a hardcoded `<a:srgbClr>` matching a theme slot for dim 4; a layout name without the master suffix for dim 5; an unused layout for dim 6).

## Two shipped PowerPoint scripts await extraction into the SPX CLI

The `sanitize-powerpoint` skill ships two scripts past the fifty-line threshold:

- `src/plugins/work/skills/sanitize-powerpoint/scripts/pptx_audit.py` (407 lines) — the read-only six-dimension deck audit reporting structural-integrity, layout-type, font, color, naming, and trim findings.
- `src/plugins/work/skills/sanitize-powerpoint/scripts/pptx_repack.py` (134 lines) — the content-surgical repackage that rebuilds a `.pptx` from an extracted working directory in the original member order and verifies the result.

Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; both have proven their value in use, so extraction is what they owe.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product, and the plugins product may depend on the resulting capability only once it is published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts the fix outside any changeset confined to this repository. This pair also raises a scope question the other extractions do not: deck sanitation is document craft rather than spec-tree machinery, so whether the SPX CLI is the right home is itself undecided — the alternative the ADR names is removal, if the capability proves unwanted.

**Resolution shape**: decide first whether deck sanitation belongs in the SPX CLI at all or is retired instead. If it is kept, port the audit dimensions and the repackager, publish, advance the floor, and reduce the shipped skill to its instruction with no scripts; declare the five undeclared audit dimensions above before the port so the extraction carries a specified contract rather than undeclared behavior. Revisit when that decision is taken.

## A narrow tool grant cannot express the scratch-directory removal the skill mandates

`sanitize-powerpoint` creates its working directory with `mktemp -d` and requires removal on every exit path, including failure, with a success-criteria item that proves it. Declaring a narrow `allowed-tools` contract for the skill founders on that requirement: the directory's path is chosen at run time, and no Bash grant pattern binds to it. The grants that would work — `Bash(rm -rf:*)` or a `${TMPDIR}` wildcard — authorize approval-free removal of paths the run never created, which is the overbroad-grant defect the skill auditor rejects elsewhere. Naming every other command while omitting the removal states a contract the body's own mandate breaks.

The skill therefore declares no `allowed-tools` and every command reaches per-call approval, which is correct but leaves the tool contract undocumented for its reader.

**Resolution shape**: pick one of three. Give `mktemp -d` an explicit template under a fixed prefix so a grant can match the prefix, once the prefix form is confirmed portable across the BSD and GNU `mktemp` a consumer may have. Or move the working directory's lifetime into `pptx_repack.py`, so a Python context manager owns creation and removal and no shell removal exists to grant. Or add a `<shell_scope>` section stating that the removal is deliberately approval-gated, matching the doctrine `/open-pr` already carries, and declare the remaining commands.

**Evidence**: raised as a `reject consistency` finding by the changeset reviewer against the path-boundary changeset, which had added an `allowed-tools` list omitting any removal capability. The list was withdrawn rather than completed with an overbroad grant.
