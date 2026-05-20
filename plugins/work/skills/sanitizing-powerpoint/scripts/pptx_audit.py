#!/usr/bin/env python3
"""Read-only six-dimension audit of a PowerPoint .pptx package.

Reports structural-integrity, layout-type, font, color, naming, and trim
findings. Never writes. Part of the work plugin's sanitizing-powerpoint skill.

Usage:
    python3 pptx_audit.py <deck.pptx> [--json]

Exit codes: 0 = audit ran (findings may exist), 2 = could not read the deck.

Tested with:
- Clean 6-slide / 5-master deck            -> only INFO findings (unused
                                              layouts, hardcoded brand colors)
- Same deck before sanitizing              -> layout-type, font, and naming
                                              findings reported
- Missing file / non-ZIP input             -> clear error, exit 2
"""

import json
import posixpath
import sys
import xml.etree.ElementTree as ET
import zipfile

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
RID = "{%s}id" % NS["r"]
CT_LAYOUT = (
    "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"
)
CT_MASTER = (
    "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"
)
CT_SLIDE = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"


def die(message, code=2):
    """Print an error to stderr and exit with the given code (default 2)."""
    print(message, file=sys.stderr)
    sys.exit(code)


def load(path):
    """Return {part-name: bytes} for every member of the .pptx ZIP."""
    try:
        with zipfile.ZipFile(path) as zf:
            return {n: zf.read(n) for n in zf.namelist() if not n.endswith("/")}
    except FileNotFoundError:
        die(f"error: file not found: {path}")
    except (zipfile.BadZipFile, IsADirectoryError) as exc:
        die(f"error: not a readable .pptx (ZIP): {path} ({exc})")


def rels_of(parts, part):
    """Return {Id: (relationship-type, resolved-target-part)} for a part."""
    folder, base = posixpath.split(part)
    rels_path = posixpath.join(folder, "_rels", base + ".rels")
    out = {}
    if rels_path not in parts:
        return out
    for rel in ET.fromstring(parts[rels_path]):
        target = rel.attrib["Target"]
        if target.startswith("/"):
            resolved = target.lstrip("/")
        else:
            resolved = posixpath.normpath(posixpath.join(folder, target))
        out[rel.attrib["Id"]] = (rel.attrib["Type"].rsplit("/", 1)[-1], resolved)
    return out


def names(prefix, parts):
    """Sorted part names directly under a folder prefix (no _rels)."""
    return sorted(
        n
        for n in parts
        if n.startswith(prefix) and "/_rels/" not in n and n.endswith(".xml")
    )


class Audit:
    def __init__(self, parts):
        self.parts = parts
        self.findings = []
        self.layouts = names("ppt/slideLayouts/slideLayout", parts)
        self.masters = names("ppt/slideMasters/slideMaster", parts)
        self.slides = names("ppt/slides/slide", parts)
        self.themes = names("ppt/theme/theme", parts)
        self.ct_overrides = self._content_types()
        self.master_of_layout = {}  # layout part -> master part
        self.theme_of_master = {}  # master part -> theme part
        self.theme_name = {}  # theme part -> display name
        self._map_relationships()

    def add(self, dim, severity, message):
        self.findings.append(
            {"dimension": dim, "severity": severity, "message": message}
        )

    def _content_types(self):
        root = ET.fromstring(self.parts["[Content_Types].xml"])
        out = {}
        for o in root:
            if o.tag.endswith("}Override"):
                out[o.attrib["PartName"].lstrip("/")] = o.attrib["ContentType"]
        return out

    def _map_relationships(self):
        for m in self.masters:
            for rtype, tgt in rels_of(self.parts, m).values():
                if rtype == "theme":
                    self.theme_of_master[m] = tgt
        for lay in self.layouts:
            for rtype, tgt in rels_of(self.parts, lay).values():
                if rtype == "slideMaster":
                    self.master_of_layout[lay] = tgt
        for t in self.themes:
            try:
                self.theme_name[t] = ET.fromstring(self.parts[t]).attrib.get("name", "")
            except ET.ParseError:
                self.theme_name[t] = ""

    def layout_name(self, layout):
        csld = ET.fromstring(self.parts[layout]).find("p:cSld", NS)
        return csld.attrib.get("name", "") if csld is not None else ""

    # -- dimension 1: structure ------------------------------------------
    def structure(self):
        pres = "ppt/presentation.xml"
        pres_rels = rels_of(self.parts, pres)
        root = ET.fromstring(self.parts[pres])
        registered_masters = set()
        mlist = root.find("p:sldMasterIdLst", NS)
        if mlist is not None:
            for mid in mlist.findall("p:sldMasterId", NS):
                rid = mid.attrib.get(RID)
                if rid not in pres_rels:
                    self.add(
                        1, "error", f"presentation.xml master r:id={rid} unresolved"
                    )
                else:
                    registered_masters.add(pres_rels[rid][1])
        for m in self.masters:
            if m not in registered_masters:
                self.add(1, "error", f"{m} is not registered in presentation.xml")

        referenced_layouts = {}
        for m in self.masters:
            mrels = rels_of(self.parts, m)
            id_list = ET.fromstring(self.parts[m]).find("p:sldLayoutIdLst", NS)
            seen = {}
            for e in (
                id_list.findall("p:sldLayoutId", NS) if id_list is not None else []
            ):
                rid = e.attrib.get(RID)
                if rid not in mrels:
                    self.add(1, "error", f"{m}: layout r:id={rid} unresolved")
                    continue
                tgt = mrels[rid][1]
                referenced_layouts.setdefault(tgt, []).append(m)
                if tgt in self.parts:
                    nm = self.layout_name(tgt)
                    if nm in seen:
                        self.add(1, "error", f'{m}: duplicate layout name "{nm}"')
                    seen[nm] = tgt
                else:
                    self.add(1, "error", f"{m}: layout part {tgt} is missing")
        for lay in self.layouts:
            owners = referenced_layouts.get(lay, [])
            if not owners:
                self.add(1, "error", f"{lay} is orphaned — no master lists it")
            elif len(owners) > 1:
                self.add(1, "error", f"{lay} is listed by {len(owners)} masters")

        for part, ct in (
            (p, c)
            for p, c in (
                [(x, CT_MASTER) for x in self.masters]
                + [(x, CT_LAYOUT) for x in self.layouts]
                + [(x, CT_SLIDE) for x in self.slides]
            )
        ):
            if self.ct_overrides.get(part) != ct:
                self.add(1, "error", f"{part} missing/wrong content-type override")

    # -- dimension 2: layout types ---------------------------------------
    def layout_types(self):
        for lay in self.layouts:
            root = ET.fromstring(self.parts[lay])
            ltype = root.attrib.get("type", "cust")
            tree = root.find("p:cSld/p:spTree", NS)
            shapes = (
                len(tree.findall("p:sp", NS)) + len(tree.findall("p:pic", NS))
                if tree is not None
                else 0
            )
            nm = self.layout_name(lay)
            if shapes == 0 and ltype != "blank":
                self.add(
                    2,
                    "warn",
                    f"{lay} \"{nm}\": empty layout typed '{ltype}', expected 'blank'",
                )
            if shapes > 0 and ltype == "blank":
                self.add(2, "warn", f"{lay} \"{nm}\": non-empty layout typed 'blank'")

    # -- dimension 3: fonts ----------------------------------------------
    def fonts(self):
        # Theme fonts = major/minor latin of the themes bound to slide masters.
        # The standard Office theme also carries ~40 script-fallback fonts in
        # <a:font script="…">; those are normal and are not scanned or flagged.
        theme_fonts = set()
        for t in set(self.theme_of_master.values()):
            if t not in self.parts:
                continue
            try:
                troot = ET.fromstring(self.parts[t])
            except ET.ParseError:
                continue
            for tag in ("a:majorFont", "a:minorFont"):
                latin = troot.find(f"a:themeElements/a:fontScheme/{tag}/a:latin", NS)
                if latin is not None and latin.attrib.get("typeface"):
                    theme_fonts.add(latin.attrib["typeface"])
        # Scan only the deck's own content — slides, layouts, masters — for
        # bullet fonts and hardcoded run/style fonts. Theme parts and the
        # notes/handout masters are out of scope.
        stray = {}  # typeface -> {role: count}
        for part, data in self.parts.items():
            if not (
                part.startswith("ppt/slides/")
                or part.startswith("ppt/slideLayouts/")
                or part.startswith("ppt/slideMasters/")
            ):
                continue
            try:
                root = ET.fromstring(data)
            except ET.ParseError:
                continue
            for el in root.iter():
                if el.tag == f"{{{NS['a']}}}buFont":
                    role = "buFont"
                elif el.tag == f"{{{NS['a']}}}latin":
                    role = "run/style font"
                else:
                    continue
                tf = el.attrib.get("typeface", "")
                if not tf or tf.startswith("+") or tf in theme_fonts:
                    continue
                stray.setdefault(tf, {}).setdefault(role, 0)
                stray[tf][role] += 1
        for tf, roles in sorted(stray.items()):
            detail = ", ".join(f"{n}x {role}" for role, n in sorted(roles.items()))
            self.add(3, "warn", f"non-theme font '{tf}' — {detail}")

    # -- dimension 4: colors ---------------------------------------------
    def colors(self):
        theme_hex = {}  # HEX -> scheme slot
        for t in self.themes:
            scheme = ET.fromstring(self.parts[t]).find(
                "a:themeElements/a:clrScheme", NS
            )
            if scheme is None:
                continue
            for slot in scheme:
                srgb = slot.find("a:srgbClr", NS)
                if srgb is not None:
                    theme_hex.setdefault(
                        srgb.attrib["val"].upper(), slot.tag.rsplit("}", 1)[-1]
                    )
        hardcoded = {}  # HEX -> count
        for part, data in self.parts.items():
            if not (
                part.startswith("ppt/slides/")
                or part.startswith("ppt/slideLayouts/")
                or part.startswith("ppt/slideMasters/")
            ):
                continue
            try:
                root = ET.fromstring(data)
            except ET.ParseError:
                continue
            for el in root.iter(f"{{{NS['a']}}}srgbClr"):
                hardcoded[el.attrib["val"].upper()] = (
                    hardcoded.get(el.attrib["val"].upper(), 0) + 1
                )
        for hex_val, count in sorted(hardcoded.items()):
            slot = theme_hex.get(hex_val)
            if slot:
                self.add(
                    4,
                    "info",
                    f"hardcoded color #{hex_val} ({count}x) "
                    f"equals theme '{slot}' — convertible to schemeClr",
                )
            else:
                self.add(
                    4,
                    "info",
                    f"hardcoded color #{hex_val} ({count}x) — no theme equivalent",
                )

    # -- dimension 5: naming ---------------------------------------------
    def naming(self):
        by_master = {}
        for lay in self.layouts:
            m = self.master_of_layout.get(lay)
            by_master.setdefault(m, []).append(lay)
        for m, lays in by_master.items():
            theme = self.theme_of_master.get(m)
            suffix = self.theme_name.get(theme, "") if theme else ""
            named = {lay: self.layout_name(lay) for lay in lays}
            for lay, nm in named.items():
                if nm.startswith(("1_", "2_", "3_")):
                    self.add(5, "info", f'{lay} "{nm}": PowerPoint dedup-prefix name')
            if not suffix:
                continue
            tail = f" | {suffix}"
            aligned = sum(1 for nm in named.values() if nm.endswith(tail))
            if aligned and aligned < len(named):
                for lay, nm in named.items():
                    if not nm.endswith(tail):
                        self.add(
                            5,
                            "info",
                            f'{lay} "{nm}": expected suffix '
                            f"'{tail}' (master convention)",
                        )

    # -- dimension 6: trim -----------------------------------------------
    def trim(self):
        used_layouts = set()
        for s in self.slides:
            for rtype, tgt in rels_of(self.parts, s).values():
                if rtype == "slideLayout":
                    used_layouts.add(tgt)
        used_masters = {self.master_of_layout.get(lay) for lay in used_layouts}
        for lay in self.layouts:
            if lay not in used_layouts:
                self.add(6, "info", f'{lay} "{self.layout_name(lay)}" used by no slide')
        for m in self.masters:
            if m not in used_masters:
                self.add(6, "info", f"{m} used by no slide")
        if "docMetadata/LabelInfo.xml" in self.parts:
            self.add(6, "info", "docMetadata/LabelInfo.xml — sensitivity label present")
        if any(p.startswith("ppt/webextensions/") for p in self.parts):
            self.add(6, "info", "ppt/webextensions/ — Office add-in task pane present")

    def run(self):
        self.structure()
        self.layout_types()
        self.fonts()
        self.colors()
        self.naming()
        self.trim()
        return self.findings


DIM_NAMES = {
    1: "Structure",
    2: "Layout types",
    3: "Fonts",
    4: "Colors",
    5: "Naming",
    6: "Trim",
}


def report(path, findings):
    print(f"pptx audit — {path}")
    print("=" * 64)
    if not findings:
        print("No findings. All six dimensions clean.")
        return
    for dim in range(1, 7):
        rows = [f for f in findings if f["dimension"] == dim]
        if not rows:
            continue
        print(f"\n[{dim}] {DIM_NAMES[dim]} — {len(rows)} finding(s)")
        for f in rows:
            print(f"  {f['severity'].upper():5s} {f['message']}")
    errors = sum(1 for f in findings if f["severity"] == "error")
    print("\n" + "=" * 64)
    print(f"{len(findings)} finding(s); {errors} integrity error(s).")


def main(argv):
    args = [a for a in argv[1:] if a != "--json"]
    as_json = "--json" in argv
    if len(args) != 1:
        die("usage: pptx_audit.py <deck.pptx> [--json]")
    parts = load(args[0])
    if "[Content_Types].xml" not in parts or "ppt/presentation.xml" not in parts:
        die(f"error: {args[0]} is not a PowerPoint presentation package")
    findings = Audit(parts).run()
    if as_json:
        print(json.dumps({"deck": args[0], "findings": findings}, indent=2))
    else:
        report(args[0], findings)


if __name__ == "__main__":
    main(sys.argv)
