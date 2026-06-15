"""Scenario evidence: the runtime-token validator's report and exit behavior.

Spec: spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md

The validator reads a file from disk and, on a raw runtime token, reports the file,
line, and token and exits non-zero; on token-only content it reports nothing and exits
zero; a file on the ignore-list is exempt. The discriminating token name comes from the
source-owned registry the detector derives from.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.build import RUNTIME_TOKEN_REGISTRY
from outcomeeng.validation.runtime_tokens import (
    RUNTIME_TOKEN_IGNORE,
    main,
    scan_file,
)

_RAW_NAME = RUNTIME_TOKEN_REGISTRY["ask_user"]["claude"]
_CAPABILITY = "ask_user"
_REPO_ROOT = Path(__file__).resolve().parents[4]


def test_raw_token_is_reported_with_file_line_and_token_and_exits_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text(f"# Heading\n\nUse {_RAW_NAME} to ask.\n", encoding="utf-8")

    violations = scan_file(skill)
    assert len(violations) == 1
    assert violations[0].line == 3
    assert violations[0].token == _RAW_NAME

    exit_code = main([str(skill)])
    assert exit_code != 0
    out = capsys.readouterr().out
    assert str(skill) in out
    assert ":3" in out


def test_token_expressed_content_reports_nothing_and_exits_zero(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        f"# Heading\n\nAsk via {{{{! tool('{_CAPABILITY}') !}}}} now.\n",
        encoding="utf-8",
    )
    assert scan_file(skill) == []
    assert main([str(skill)]) == 0


def test_ignored_file_with_raw_token_is_not_reported() -> None:
    # An entry on the ignore-list is the explicit, tracked exception for a
    # not-yet-converted file; its real content carries raw tokens today.
    ignored_relative = next(iter(RUNTIME_TOKEN_IGNORE))
    ignored_path = _REPO_ROOT / ignored_relative
    assert ignored_path.is_file()

    assert scan_file(ignored_path) == []
    assert main([str(ignored_path)]) == 0
