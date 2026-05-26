# OPC structure of a `.pptx`

Anatomy of a PowerPoint package — read this before the first audit.

Contents:

- Package basics
- Part tree
- The relationship model
- The master → layout → slide cascade
- Content types
- The layout `type` attribute
- How parts are named
- Themes, fonts, and colors
- `app.xml` is derived

## Package basics

A `.pptx` is a ZIP archive following the Open Packaging Conventions (OPC). Each entry is a *part* — almost always an XML document. Unzipping the archive and editing the XML is a fully supported way to change a deck; PowerPoint re-reads whatever the parts say.

Two structural rules hold across the package:

- `[Content_Types].xml` MUST be present and SHOULD be the first member of the archive.
- Every part's relationships live in a sibling `_rels/` folder.

## Part tree

```
[Content_Types].xml              ← content type of every part
_rels/.rels                      ← package-level relationships
docProps/
  app.xml                        ← derived manifest (fonts used, slide titles)
  core.xml, custom.xml           ← document properties
docMetadata/
  LabelInfo.xml                  ← sensitivity label (optional)
ppt/
  presentation.xml               ← the deck root: master list, slide list, slide size
  _rels/presentation.xml.rels
  presProps.xml, viewProps.xml, tableStyles.xml
  slideMasters/slideMasterN.xml  + _rels/
  slideLayouts/slideLayoutN.xml  + _rels/
  slides/slideN.xml              + _rels/
  notesMasters/, handoutMasters/
  theme/themeN.xml
  media/imageN.png
  webextensions/                 ← Office add-in task panes (optional)
```

The part *numbers* (`slideLayout6.xml`) are arbitrary identifiers, not an order. Order comes from the `*IdLst` elements and relationships described below.

## The relationship model

Nothing in OPC references another part by filename. References go through relationships.

A part `X.xml` has its relationships in `_rels/X.xml.rels`:

```xml
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster2.xml" />
```

Inside the XML, an element points at a relationship by its `Id`, usually via the `r:id` attribute:

```xml
<p:sldLayoutId id="2147483739" r:id="rId1" />
```

To resolve any reference: read the element's `r:id`, look that `Id` up in the part's `.rels`, follow `Target`. A reference is **broken** when the `r:id` has no matching `Relationship`, or the `Target` part does not exist.

## The master → layout → slide cascade

```
presentation.xml
  <p:sldMasterIdLst> → <p:sldMasterId r:id=…>   → slideMasterN.xml
  <p:sldIdLst>       → <p:sldId r:id=…>         → slideN.xml

slideMasterN.xml
  <p:sldLayoutIdLst> → <p:sldLayoutId r:id=…>   → slideLayoutN.xml

slideN.xml.rels        → relationship type "slideLayout"  → the layout it uses
slideLayoutN.xml.rels  → relationship type "slideMaster"  → its owning master
slideMasterN.xml.rels  → relationship type "theme"        → its theme
```

Consequences worth knowing:

- A layout belongs to **exactly one** master — the one whose `<p:sldLayoutIdLst>` lists it. A layout part that no master lists is **orphaned**.
- A master must appear in `presentation.xml`'s `<p:sldMasterIdLst>` to be active.
- PowerPoint's `Home → Layout` gallery shows only the layouts of the **current slide's master**. A layout absent from the gallery is usually on a different master, not broken.

## Content types

`[Content_Types].xml` declares a content type for every part, by extension default or by explicit override:

```xml
<Default Extension="xml" ContentType="application/xml" />
<Override PartName="/ppt/slideLayouts/slideLayout6.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml" />
```

Masters, layouts, slides, themes, and `presentation.xml` each need an `Override` — their content type is not the `xml` default. A part with no declared content type can be silently dropped by PowerPoint.

## The layout `type` attribute

`<p:sldLayout>` carries a `type` attribute (`ST_SlideLayoutType`). It declares the layout's *kind* so PowerPoint can match layouts when pasting slides. The value should match the layout's actual content. Common values:

| `type`      | Layout kind                                |
| ----------- | ------------------------------------------ |
| `title`     | Title slide (centered title + subtitle)    |
| `secHead`   | Section header / divider                   |
| `titleOnly` | Title, no body                             |
| `obj`       | Title + one content placeholder            |
| `twoObj`    | Title + two content placeholders           |
| `blank`     | No placeholders at all                     |
| `cust`      | Custom — PowerPoint will not auto-match it |

**The attribute is optional; when absent it defaults to `cust`.** An empty layout left as `cust` instead of `blank`, or a section divider left as `cust` instead of `secHead`, is a type mismatch — valid XML, but wrong metadata.

## How parts are named

- **Layouts** carry a display name in `<p:cSld name="…">`. PowerPoint shows it in the layout gallery and Slide Master view. It is display-only — no relationship uses it.
- **Masters** usually have an *empty* `<p:cSld>` name. PowerPoint displays a master using its bound **theme's** name (`<a:theme name="…">` in the theme part). To "name" a master, name its theme.
- PowerPoint appends a `1_`, `2_`, … prefix when importing a layout whose name collides with an existing one. A `1_`-prefixed name is a dedup artifact, not an intentional name.

## Themes, fonts, and colors

Each master binds one theme. The theme defines a font scheme and a color scheme:

- `<a:fontScheme>` → `<a:majorFont>` (headings) and `<a:minorFont>` (body), each with `<a:latin typeface="…">` plus optional `<a:font script="…" typeface="…"/>` script fallbacks. Parts reference theme fonts as `+mj-lt` (major latin) and `+mn-lt` (minor latin).
- `<a:clrScheme>` → `dk1 lt1 dk2 lt2 accent1…accent6 hlink folHlink`. Parts reference theme colors as `<a:schemeClr val="accent1"/>`; the master's `<p:clrMap>` maps the `bg1/tx1/…` names onto the scheme slots.

A **hardcoded** color is `<a:srgbClr val="RRGGBB"/>`. A **hardcoded** font is a literal `typeface="Some Font"` that is neither a theme reference nor the theme's own family. Bullets carry their own font in `<a:buFont typeface="…"/>` — PowerPoint's default there is `Arial`, which is benign but appears in the font manifest.

## `app.xml` is derived

`docProps/app.xml` holds a `<TitlesOfParts>` vector (slide titles, theme names, fonts used) and `<HeadingPairs>` counts. PowerPoint **regenerates it from deck content on every save**. It is a derived manifest, never a source of truth — fix the content parts and `app.xml` follows.
