"""Harnesses for audit-tests evidence."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast


class Declaration(Protocol):
    name: str
    kind: str


class DeclarationScanner(Protocol):
    def scan_text(self, source: str, path: Path) -> list[Declaration]: ...


@dataclass(frozen=True)
class AuditVerdict:
    status: str
    finding_category: str


def audit_verdict_for_test_owned_declaration() -> AuditVerdict:
    declarations = _scanner().scan_text(
        _fixture("test_owned_declaration.py").read_text(encoding="utf-8"),
        _fixture("test_owned_declaration.py"),
    )
    if any(
        declaration.name == "mapping_runs" and declaration.kind == "variable"
        for declaration in declarations
    ):
        return AuditVerdict(status="REJECT", finding_category="test-owned declaration")
    return AuditVerdict(status="APPROVED", finding_category="")


def _scanner() -> DeclarationScanner:
    module_path = Path(
        "src/plugins/spec-tree/skills/audit-tests/scripts/declaration_scan.py"
    )
    spec = importlib.util.spec_from_file_location(
        "audit_tests_declaration_scan", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load declaration scanner from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(DeclarationScanner, module)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "audit_tests" / name
