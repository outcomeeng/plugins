"""Test scaffolding for sanitizing-powerpoint: builds synthetic OPC PPTX archives and loads the marketplace scripts as importable modules."""

from __future__ import annotations

import importlib.util
import sys
import zipfile
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType

# parents[2] = repo root: outcomeeng_testing/harnesses/<file>
SCRIPTS_DIR: Path = (
    Path(__file__).resolve().parents[2]
    / "plugins"
    / "work"
    / "skills"
    / "sanitizing-powerpoint"
    / "scripts"
)
PPTX_AUDIT: Path = SCRIPTS_DIR / "pptx_audit.py"
PPTX_REPACK: Path = SCRIPTS_DIR / "pptx_repack.py"


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, (
        f"could not build module spec for {path}"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_audit() -> ModuleType:
    """Load ``pptx_audit.py`` as an importable module."""
    return _load_module("pptx_audit_under_test", PPTX_AUDIT)


def load_repack() -> ModuleType:
    """Load ``pptx_repack.py`` as an importable module."""
    return _load_module("pptx_repack_under_test", PPTX_REPACK)


def write_pptx(path: Path, parts: Mapping[str, str | bytes]) -> Path:
    """Pack ``parts`` into an OPC ZIP at ``path``.

    ``[Content_Types].xml`` is written first; remaining members follow in
    insertion order. Returns the written path for chaining.
    """
    content_types = "[Content_Types].xml"
    if content_types not in parts:
        raise ValueError(f"parts mapping must contain {content_types!r}")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        _write_member(zf, content_types, parts[content_types])
        for name, data in parts.items():
            if name == content_types:
                continue
            _write_member(zf, name, data)
    return path


def _write_member(zf: zipfile.ZipFile, name: str, data: str | bytes) -> None:
    payload = data.encode("utf-8") if isinstance(data, str) else data
    zf.writestr(name, payload)


def extract_pptx(zip_path: Path, dest: Path) -> Path:
    """Extract every member of ``zip_path`` into ``dest``. Returns ``dest``."""
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    return dest


def minimal_parts(*, orphan_layout: bool = False) -> dict[str, str]:
    """Return a minimal valid OPC presentation parts mapping.

    The mapping declares one slide master with one registered layout. With
    ``orphan_layout=True``, a second layout part is added with a matching
    content-type override but no master relationship — exercising the
    dimension-1 structure check in ``pptx_audit.py``.
    """
    parts: dict[str, str] = {
        "[Content_Types].xml": _content_types(orphan_layout=orphan_layout),
        "_rels/.rels": _ROOT_RELS,
        "ppt/presentation.xml": _PRESENTATION,
        "ppt/_rels/presentation.xml.rels": _PRES_RELS,
        "ppt/slideMasters/slideMaster1.xml": _SLIDE_MASTER,
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": _MASTER_RELS,
        "ppt/slideLayouts/slideLayout1.xml": _slide_layout(name="Blank"),
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": _LAYOUT_RELS,
        "ppt/theme/theme1.xml": _THEME,
    }
    if orphan_layout:
        parts["ppt/slideLayouts/slideLayout2.xml"] = _slide_layout(name="Orphan")
    return parts


def _content_types(*, orphan_layout: bool) -> str:
    extra = ""
    if orphan_layout:
        extra = (
            '  <Override PartName="/ppt/slideLayouts/slideLayout2.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument'
            ".presentationml.slideLayout+xml"
            '"/>\n'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension="rels"'
        ' ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '  <Default Extension="xml" ContentType="application/xml"/>\n'
        '  <Override PartName="/ppt/presentation.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.presentationml.presentation.main+xml"/>\n'
        '  <Override PartName="/ppt/slideMasters/slideMaster1.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.presentationml.slideMaster+xml"/>\n'
        '  <Override PartName="/ppt/slideLayouts/slideLayout1.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.presentationml.slideLayout+xml"/>\n'
        f"{extra}"
        '  <Override PartName="/ppt/theme/theme1.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>\n'
        "</Types>\n"
    )


_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org'
    '/package/2006/relationships">\n'
    '  <Relationship Id="rId1"'
    ' Type="http://schemas.openxmlformats.org/officeDocument'
    '/2006/relationships/officeDocument"'
    ' Target="ppt/presentation.xml"/>\n'
    "</Relationships>\n"
)


_PRESENTATION = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    "<p:presentation"
    ' xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument'
    '/2006/relationships">\n'
    "  <p:sldMasterIdLst>\n"
    '    <p:sldMasterId id="2147483648" r:id="rId1"/>\n'
    "  </p:sldMasterIdLst>\n"
    "</p:presentation>\n"
)


_PRES_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org'
    '/package/2006/relationships">\n'
    '  <Relationship Id="rId1"'
    ' Type="http://schemas.openxmlformats.org/officeDocument'
    '/2006/relationships/slideMaster"'
    ' Target="slideMasters/slideMaster1.xml"/>\n'
    "</Relationships>\n"
)


_SLIDE_MASTER = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    "<p:sldMaster"
    ' xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument'
    '/2006/relationships">\n'
    "  <p:sldLayoutIdLst>\n"
    '    <p:sldLayoutId id="2147483649" r:id="rId1"/>\n'
    "  </p:sldLayoutIdLst>\n"
    "</p:sldMaster>\n"
)


_MASTER_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org'
    '/package/2006/relationships">\n'
    '  <Relationship Id="rId1"'
    ' Type="http://schemas.openxmlformats.org/officeDocument'
    '/2006/relationships/slideLayout"'
    ' Target="../slideLayouts/slideLayout1.xml"/>\n'
    "</Relationships>\n"
)


_LAYOUT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org'
    '/package/2006/relationships">\n'
    '  <Relationship Id="rId1"'
    ' Type="http://schemas.openxmlformats.org/officeDocument'
    '/2006/relationships/slideMaster"'
    ' Target="../slideMasters/slideMaster1.xml"/>\n'
    "</Relationships>\n"
)


_THEME = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
    ' name="Office Theme">\n'
    "  <a:themeElements/>\n"
    "</a:theme>\n"
)


def _slide_layout(*, name: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        "<p:sldLayout"
        ' xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
        ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
        ' type="blank">\n'
        f'  <p:cSld name="{name}">\n'
        "    <p:spTree/>\n"
        "  </p:cSld>\n"
        "</p:sldLayout>\n"
    )
