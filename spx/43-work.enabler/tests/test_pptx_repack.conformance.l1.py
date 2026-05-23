"""Level-1 conformance evidence: ``pptx_repack.py`` preserves OPC member ordering.

Covers the conformance assertion in ``spx/43-work.enabler/work.md``:

- The deck rebuilt by ``pptx_repack.py`` keeps ``[Content_Types].xml`` as
  the first ZIP member, per the OPC packaging convention.

The OPC packaging convention (ECMA-376 part 2, section 10.1.2.4) requires
``[Content_Types].xml`` as the first physical member of an OPC package;
some readers depend on this ordering for content-type discovery.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from outcomeeng_testing.harnesses.sanitizing_powerpoint import (
    extract_pptx,
    load_repack,
    minimal_parts,
    write_pptx,
)

OPC_FIRST_MEMBER = "[Content_Types].xml"


def test_repack_preserves_content_types_as_first_zip_member(tmp_path: Path) -> None:
    original = write_pptx(tmp_path / "in.pptx", minimal_parts())
    workdir = extract_pptx(original, tmp_path / "work")
    out_path = tmp_path / "out.pptx"

    repack = load_repack()
    repack.main(["pptx_repack.py", str(original), str(workdir), str(out_path)])

    with zipfile.ZipFile(out_path) as zf:
        members = [name for name in zf.namelist() if not name.endswith("/")]

    assert members[0] == OPC_FIRST_MEMBER
