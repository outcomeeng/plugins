# Audit and fix catalog

Detection method and exact XML transformation for each of the six audit dimensions. Read `opc-structure.md` first.

Contents:

- Editing discipline
- Removing a part — the five-place checklist
- Dimension 1 — Structure and integrity
- Dimension 2 — Layout type attributes
- Dimension 3 — Font hygiene
- Dimension 4 — Color hygiene
- Dimension 5 — Layout naming
- Dimension 6 — Trim

## Editing discipline

Every fix edits an extracted XML part. Hold to three rules:

- Edit the **smallest** element that resolves the finding. Do not reformat the part.
- After editing a part, it MUST stay well-formed XML. `pptx_repack.py` verifies this; a malformed part fails the run.
- A fix that adds or removes a *part* (dimension 6) MUST update every place that references it — see the checklist below.

## Removing a part — the five-place checklist

A slide layout (or master, or any referenced part) is wired into the package in up to five places. Removing the `.xml` file alone leaves a broken package. Remove **all** of:

1. The part file itself — `ppt/slideLayouts/slideLayoutN.xml`.
2. Its relationships file — `ppt/slideLayouts/_rels/slideLayoutN.xml.rels`.
3. The `<Override>` for it in `[Content_Types].xml`.
4. The `*Id` entry in its parent's `*IdLst` — e.g. `<p:sldLayoutId>` in the owning master.
5. The `<Relationship>` in the parent's `.rels` that the `*Id` resolved through.

A master also has a `<p:sldMasterId>` in `presentation.xml` and a relationship in `presentation.xml.rels`.

## Dimension 1 — Structure and integrity

| Finding               | Detection                                                                      | Fix                                                                                                                         |
| --------------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| Orphaned layout       | A `slideLayoutN.xml` part that no master's `<p:sldLayoutIdLst>` lists          | Either re-list it under the correct master (add `<p:sldLayoutId>` + relationship) or remove it via the five-place checklist |
| Broken `r:id`         | An `r:id` whose `Id` is absent from the part's `.rels`                         | Add the missing `<Relationship>`, or delete the dangling reference element                                                  |
| Missing content type  | A master/layout/slide/theme part with no `<Override>` in `[Content_Types].xml` | Add the `<Override>` with the correct content type                                                                          |
| Duplicate layout name | Two layouts under one master sharing a `<p:cSld name>`                         | Rename one (dimension 5)                                                                                                    |
| Unregistered master   | A `slideMasterN.xml` not in `presentation.xml`'s `<p:sldMasterIdLst>`          | Register it (add `<p:sldMasterId>` + relationship) or remove it                                                             |

Structure findings are integrity defects — a deck can fail to open or lose content. Fix all of them. They are mechanical, but re-listing vs. removing an orphan is a judgment call: re-list if a slide needs it, remove if it is dead.

## Dimension 2 — Layout type attributes

Detection: for each `slideLayoutN.xml`, count placeholder shapes (`<p:sp>` under `<p:spTree>`) and read the `type` attribute on `<p:sldLayout>`. Mismatches:

- Zero shapes, `type` is `cust` or absent → should be `blank`.
- A centered title + subtitle, `type` is `cust` → should be `secHead` (section divider) or `title` (title slide).
- A title-only layout typed `cust` → should be `titleOnly`.

Fix — add or correct the attribute on the root element:

```xml
<!-- before: empty layout, type defaults to cust -->
<p:sldLayout xmlns:a="…" xmlns:r="…" xmlns:p="…" preserve="1">

<!-- after -->
<p:sldLayout xmlns:a="…" xmlns:r="…" xmlns:p="…" type="blank" preserve="1">
```

Place `type` before `preserve`, matching how PowerPoint writes it. `type="blank"` for an empty layout is mechanical. Other kinds (`secHead`, `titleOnly`, `obj`) are heuristic — confirm with the user.

## Dimension 3 — Font hygiene

Detection: collect every `typeface="…"` in slides, layouts, and masters. The expected fonts are the theme's `<a:majorFont>` / `<a:minorFont>` latin families. Theme parts and the notes/handout masters are out of scope — their `<a:font script="…">` script fallbacks are standard Office content and stay untouched. Flag the rest:

- `<a:buFont typeface="Arial" …/>` — bullet-glyph font. PowerPoint's default; benign but lists `Arial` in the font manifest.
- `<a:latin typeface="SomeFont"/>` inside a run or list style — a hardcoded run font.

Fix — redirect a bullet font to the theme body font:

```xml
<!-- before -->
<a:buFont typeface="Arial" panose="020B0604020202020204" pitchFamily="34" charset="0" />
<!-- after -->
<a:buFont typeface="Commissioner" />
```

**Before redirecting `buFont`, confirm the target font covers every `buChar` codepoint used** (collect `<a:buChar char="…"/>` values; U+2022 `•` is the usual one). A bullet font missing the glyph renders blank.

After the content parts are clean, `docProps/app.xml` regenerates clean on the next PowerPoint save. To ship a clean file immediately, also remove the font's `<vt:lpstr>` entry from `app.xml`'s `<TitlesOfParts>` and decrement the "Fonts Used" count in `<HeadingPairs>` and the vector `size`.

Redirecting `buFont` is mechanical once glyph coverage is confirmed. Changing a hardcoded run font alters appearance — get approval.

## Dimension 4 — Color hygiene

Detection: collect every `<a:srgbClr val="RRGGBB"/>`. Read the theme `<a:clrScheme>` (`dk1 lt1 dk2 lt2 accent1…accent6 hlink folHlink`). For each hardcoded color, check whether its value equals a theme color.

Fix — convert a hardcoded color that duplicates a theme color:

```xml
<!-- before: literal value equal to the theme's accent1 -->
<a:srgbClr val="4472C4" />
<!-- after -->
<a:schemeClr val="accent1" />
```

This dimension is **report-first, always**. A hardcoded color is not automatically wrong:

- A value with no theme equivalent cannot be converted — report it, do not touch it.
- A value equal to a theme color may still be deliberate (a color frozen against future theme edits).

Present every color finding and convert only on explicit, per-color approval.

## Dimension 5 — Layout naming

Detection: collect every layout `<p:cSld name>`. Infer the deck's dominant pattern — most often `<Type> | <MasterName>`, where `<MasterName>` is the owning master's theme name. Flag layouts that deviate, and any `1_`-prefixed dedup artifact.

Fix — rewrite the display name:

```xml
<!-- before -->
<p:cSld name="1_Title Slide">
<!-- after -->
<p:cSld name="Pitch statement | Cover">
```

The name is display-only — no slide or master references it, so a rename cannot break anything. But the *target* name is a human decision: the audit proposes names that fit the inferred pattern; the user confirms each. Never rename to a value already used by another layout in the same master (dimension 1 duplicate).

## Dimension 6 — Trim

Detection:

- Masters / layouts used by zero slides — walk the cascade, mark every layout a slide reaches and every master those layouts belong to; the unmarked remainder is unused.
- Themes referenced by no master, notes master, or handout master.
- `docMetadata/LabelInfo.xml` — a sensitivity label.
- `ppt/webextensions/` — Office add-in task panes.

Fix — remove via the five-place checklist. Removing a master also clears its `<p:sldMasterId>` in `presentation.xml` and the relationship in `presentation.xml.rels`; removing webextensions or the label part also clears any relationship that points at them.

Trim is **report-first**. Unused is not unwanted — a deck template ships unused layouts on purpose. Remove only on explicit approval. This is the one dimension that changes the package's member count; `pptx_repack.py` verification accounts for deliberately added or removed parts.
