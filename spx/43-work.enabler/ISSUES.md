# ISSUES — work enabler

Known unresolved gaps. `/contextualize` reads this file at context-load time; remove entries as they resolve.

## Audit dimensions 2–6 lack scenario assertions

`spx/43-work.enabler/work.md` declares one scenario for dimension 1 (orphan-layout detection) plus one conformance assertion for `pptx_repack.py`. The remaining five audit dimensions in `pptx_audit.py` — `layout_types()`, `fonts()`, `colors()`, `naming()`, `trim()` (~135 lines of audit logic in total) — are applied without a prior declare step.

**Resolution shape**: a follow-on PR that adds one scenario assertion per dimension to `work.md` with a matching pytest case under `spx/43-work.enabler/tests/`. The harness's `minimal_parts` builder already covers the structural shape; each new assertion needs a focused parts variation (a layout typed `cust` with empty `spTree` for dim 2; a non-theme `<a:latin typeface=...>` inside a slide for dim 3; a hardcoded `<a:srgbClr>` matching a theme slot for dim 4; a layout name without the master suffix for dim 5; an unused layout for dim 6).
