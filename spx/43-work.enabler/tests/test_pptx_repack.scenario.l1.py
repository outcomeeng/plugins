"""Level-1 scenario evidence for ``pptx_repack.py`` round-trip and integrity exit.

Covers two scenario assertions in ``spx/43-work.enabler/work.md``:

- Given a workdir that is a verbatim extraction of the original deck,
  when ``pptx_repack.py`` rebuilds the archive, then the rebuilt deck
  reports zero changed parts.
- Given a workdir whose changed part contains malformed XML, when
  ``pptx_repack.py`` runs verification, then the script exits with code 3.

Exercised through the script's ``main(argv)`` entry point; the script's
``die`` helper raises ``SystemExit`` with the documented integrity code.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.sanitizing_powerpoint import (
    extract_pptx,
    load_repack,
    minimal_parts,
    write_pptx,
)

INTEGRITY_EXIT_CODE = 3


def test_verbatim_workdir_round_trips_with_zero_changed_parts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    original = write_pptx(tmp_path / "in.pptx", minimal_parts())
    workdir = extract_pptx(original, tmp_path / "work")
    out_path = tmp_path / "out.pptx"

    repack = load_repack()
    repack.main(["pptx_repack.py", str(original), str(workdir), str(out_path)])

    captured = capsys.readouterr()
    assert "changed:   0" in captured.out


def test_malformed_workdir_xml_exits_with_integrity_code(tmp_path: Path) -> None:
    original = write_pptx(tmp_path / "in.pptx", minimal_parts())
    workdir = extract_pptx(original, tmp_path / "work")
    # pptx_repack.verify() iterates every output member and validates each
    # `.xml` / `.rels` part; corruption of any XML part triggers exit 3.
    corrupted = workdir / "ppt" / "presentation.xml"
    corrupted.write_text("<presentation not closed")
    out_path = tmp_path / "out.pptx"

    repack = load_repack()

    with pytest.raises(SystemExit) as exc_info:
        repack.main(["pptx_repack.py", str(original), str(workdir), str(out_path)])

    assert exc_info.value.code == INTEGRITY_EXIT_CODE
