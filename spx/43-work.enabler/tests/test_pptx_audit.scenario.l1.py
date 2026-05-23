"""Level-1 scenario evidence for ``pptx_audit.py`` dimension-1 orphan detection.

Covers the scenario assertion in ``spx/43-work.enabler/work.md``:

- Given a synthetic ``.pptx`` containing an orphaned slide layout, when
  ``pptx_audit.py`` runs against it, then the audit reports the orphan
  under the structure dimension.

The audit is exercised through its ``Audit`` class on a parts mapping built
by the harness; the orphan is a layout part with a content-type override
but no relationship from any slide master, matching the dimension-1
``orphaned — no master lists it`` check in the script.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.sanitizing_powerpoint import (
    load_audit,
    minimal_parts,
    write_pptx,
)


def test_audit_reports_orphan_layout_under_structure_dimension(
    tmp_path: Path,
) -> None:
    deck_path = write_pptx(tmp_path / "orphan.pptx", minimal_parts(orphan_layout=True))

    audit = load_audit()
    parts = audit.load(str(deck_path))
    findings = audit.Audit(parts).run()

    structure_orphans = [
        f for f in findings if f["dimension"] == 1 and "orphaned" in f["message"]
    ]

    assert len(structure_orphans) == 1
    assert "slideLayout2" in structure_orphans[0]["message"]
