---
name: sanitize-powerpoint
description: >-
  ALWAYS invoke this skill when sanitizing, cleaning up, auditing, or aligning a PowerPoint (.pptx) deck — slide-master and layout structure, layout type attributes, stray fonts, non-theme colors, or layout naming. NEVER hand-edit pptx XML without this skill.
argument-hint: "[path/to/deck.pptx]"
allowed-tools: Read, Write, Edit, Bash(ls:*), Bash(mktemp -d:*), Bash(unzip:*), Bash(python3 "${SKILL_DIR}/scripts/pptx_audit.py":*), Bash(python3 "${SKILL_DIR}/scripts/pptx_repack.py":*), request_user_input
---

<objective>
A repaired `.pptx` whose every untouched part is byte-identical to the original — only the parts that resolved an approved finding differ.
</objective>

<core_rules>
Five rules govern every run. Violating any of them corrupts a deck or silently discards the work.

- **NEVER modify a deck PowerPoint has open.** A sibling `~$<name>.pptx` lock file means PowerPoint holds the deck. It regenerates the file from memory on its next save and discards any external edit. Stop and ask the user to close PowerPoint.
- **ALWAYS audit → present → approve → fix → verify.** Never auto-fix. Some findings are mechanical; some need a human decision (which theme color a hardcoded color maps to, which layout names to rename). Present findings and get scope approval first.
- **ALWAYS back up the original** before swapping the repaired file in. PowerPoint cannot undo an external overwrite.
- **Fix content parts, not `app.xml`.** PowerPoint regenerates `docProps/app.xml` (the "Fonts Used" / titles manifest) from deck content on every save. Editing only `app.xml` is undone on the next save. Fix the parts that hold the real data; `app.xml` then stays correct on its own.
- **Change as few parts as possible.** Repackage surgically (see `<repackaging>`). A deck reviewer sees a minimal diff, not a wholesale re-save.

</core_rules>

<workflow>
Run these steps in order. Steps 2 and 6 use the bundled scripts in `<scripts>`.

1. **Locate and guard.** Resolve the `.pptx` path from `$ARGUMENTS`; when it is empty, resolve the path the user named in conversation. Check for a sibling `~$<name>.pptx` lock file (`ls` the directory). If present, STOP — PowerPoint has the deck open; ask the user to close it before continuing.

2. **Audit.** Run `pptx_audit.py` on the deck. It reads the package read-only and reports findings across the six dimensions in `<audit_dimensions>`. Read the full report.

3. **Present and scope.** Show the user the findings grouped by dimension. Mechanical fixes (layout `type`, font redirect) and judgment fixes (color mapping, layout renames) are different — surface the judgment ones explicitly. Use `request_user_input` to get per-dimension or per-finding approval. Fix only what the user approves.

4. **Extract.** Create the working directory with `mktemp -d` so it is unique per invocation and lands in the session's temporary directory, **outside any git repository**. Never extract into the deck's own folder, and never name a fixed temporary path — concurrent runs collide on one. Remove the directory on every exit path, including failure.

5. **Apply approved fixes.** Edit the extracted XML part by part, following `${SKILL_DIR}/references/audit-and-fix.md`. Handle one dimension at a time, and track every changed part.

6. **Repackage and verify.** Run `pptx_repack.py` with the original deck, the working directory, and an output path. It rebuilds the package preserving every untouched part's content and the original member order, then verifies (see `<repackaging>`). Do not hand-roll the repackage.

7. **Back up and swap.** Re-check the lock file (step 1) — if PowerPoint reopened the deck, stop. Copy the original to a timestamped backup (an `_archive/` sibling, or `<name>_pre-sanitize-<date>.pptx`). Copy the repaired file over the original.

8. **Confirm.** Run `pptx_audit.py` on the now-live file. Confirm the approved findings are resolved and no new finding appeared.

</workflow>

<audit_dimensions>
The audit covers six dimensions. `references/audit-and-fix.md` gives the detection method and the exact XML transformation for each.

| # | Dimension        | What it catches                                                                                                                                                                 |
| - | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | **Structure**    | Orphaned layout parts, broken `r:id` references, missing content-type overrides, layouts duplicated within a master, unregistered masters                                       |
| 2 | **Layout types** | A layout's `type` attribute (`blank`, `secHead`, `title`, `titleOnly`, `obj`, `cust`, …) not matching its actual content — e.g. an empty layout typed `cust` instead of `blank` |
| 3 | **Fonts**        | Typefaces that are not the theme's major/minor font — stray `buFont` bullet fonts, theme script-fallbacks, hardcoded run fonts                                                  |
| 4 | **Colors**       | Hardcoded `<a:srgbClr>` values where a theme `<a:schemeClr>` exists for the same color                                                                                          |
| 5 | **Naming**       | Layout names that deviate from the deck's own dominant naming pattern; PowerPoint dedup artifacts (`1_`-prefixed names)                                                         |
| 6 | **Trim**         | Masters and layouts used by zero slides, unused themes, sensitivity labels (`docMetadata/LabelInfo.xml`), Office add-ins (`ppt/webextensions/`)                                 |

Dimension 5 is **inferred, never imposed**: the audit detects the pattern the deck already uses most (commonly `<Type> | <MasterName>`) and flags only the outliers. It never invents a convention.
</audit_dimensions>

<repackaging>
A `.pptx` is an OPC ZIP. Two repackaging properties matter, and `pptx_repack.py` enforces both:

- **Content-surgical.** Every part the fix did not touch is written back with identical content. Only changed parts differ.
- **Order-preserving.** `[Content_Types].xml` stays the first member; all other members keep their original order. Some readers depend on this.

`pptx_repack.py` rebuilds the archive from the original, substituting only the parts that changed in the working directory, then verifies — and exits non-zero on failure:

- ZIP integrity (`unzip -t` equivalent).
- XML well-formedness of every `.xml` and `.rels` part in the output archive.

It also reports the member-count delta against the original. This is informational, not enforced: dimension 6 (trim) deliberately removes parts, and the script has no way to distinguish an approved trim from an accidental drop, so a changed count is printed as a note rather than gated by exit code. Compare it against the trim findings the user approved in step 3.

NEVER repackage by extracting everything and re-zipping with default tooling — that reorders members and can recompress parts in ways some readers reject. Always use `pptx_repack.py`.
</repackaging>

<scripts>
Both scripts are standard-library Python 3.13+ — no third-party dependencies, no install step.

| Script                   | Purpose                                                                                        | Usage                                                                                |
| ------------------------ | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `scripts/pptx_audit.py`  | Read-only six-dimension audit; prints a findings report. `--json` for machine-readable output. | `python3 "${SKILL_DIR}/scripts/pptx_audit.py" <deck.pptx>`                           |
| `scripts/pptx_repack.py` | Content-surgical repackage of a working directory back into a `.pptx`, with verification.      | `python3 "${SKILL_DIR}/scripts/pptx_repack.py" <original.pptx> <workdir> <out.pptx>` |

The audit script never writes. The repack script writes only its named output file.
</scripts>

<failure_modes>
Failures from real usage. Each one cost a wrong diagnosis or a lost edit.

**Mistaking multi-master UX for corruption**

- What happened: Claude saw a layout missing from PowerPoint's Layout gallery and assumed it was corrupt. It was structurally perfect.
- Why it failed: A deck can carry several slide masters. PowerPoint's `Home → Layout` gallery shows only the layouts of the *current slide's* master. A layout on a different master is simply not shown there.
- How to avoid: Before "fixing" a missing layout, check which master owns it and which master the slide uses. Run the structure audit; trust it over the UI.

**Overwriting a deck PowerPoint has open**

- What happened: Claude copied the repaired file over the original while PowerPoint still held the deck. PowerPoint saved from memory minutes later and the repair vanished.
- Why it failed: PowerPoint keeps the deck in memory and owns the file until closed; the `~$<name>.pptx` lock file signals this.
- How to avoid: Check the lock file before extracting and again before swapping. Never swap while it exists.

**Fixing `app.xml` and nothing else**

- What happened: Claude removed a font from `docProps/app.xml`'s "Fonts Used" list and changed nothing else; it reappeared on the next save.
- Why it failed: PowerPoint regenerates `app.xml` from deck content on every save. `app.xml` is a derived manifest, not a source of truth.
- How to avoid: Fix the content parts (`buFont`, theme fonts). `app.xml` corrects itself on the next save.

**Redirecting a bullet font to a font without the glyph**

- What happened: Claude redirected `buFont` from Arial to a theme font that lacked U+2022; bullets rendered as blank or tofu.
- Why it failed: The bullet character must exist in the bullet font.
- How to avoid: Before redirecting `buFont`, confirm the target font covers every `buChar` codepoint the deck uses (U+2022 is the common one).

**Assuming a layout rename needs slide relinking**

- What happened: Claude treated renaming a layout as risky, expecting every slide on it to need an update.
- Why it failed: Slides reference layouts — and layouts reference masters — by relationship ID and part path, never by display name. `<p:cSld name="…">` is display-only.
- How to avoid: Rename `<p:cSld name>` freely. No relinking is needed; the rename cannot break a reference.

</failure_modes>

<success_criteria>
A sanitizing run is complete when:

- [ ] The audit ran and its findings were presented to the user.
- [ ] Only user-approved fixes were applied.
- [ ] The repaired deck passes `pptx_repack.py` verification (ZIP integrity, XML well-formedness); any member-count change matches the trim scope approved in step 3.
- [ ] The original deck was backed up before the swap.
- [ ] A re-run of `pptx_audit.py` on the live file confirms the approved findings are resolved and no new finding appeared.
- [ ] The working directory came from `mktemp -d`, was removed on exit, and was the only scratch artifact; the deck's folder holds only the deck and its backup.

</success_criteria>

<reference_guides>

| File                          | When to read                                                                                                     |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `references/opc-structure.md` | Before the first audit — the package anatomy, the master→layout→slide relationship chain, the layout `type` enum |
| `references/audit-and-fix.md` | During steps 3 and 5 — the detection method and exact XML transformation for each of the six dimensions          |

</reference_guides>
