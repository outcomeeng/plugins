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

from outcomeeng.distribution.build import (
    RUNTIME_TOKEN_REGISTRY,
    SHARED_FRAGMENT_FILENAME,
)
from outcomeeng.validation.runtime_tokens import (
    main,
    scan_file,
    scan_paths,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

_RAW_NAME = RUNTIME_TOKEN_REGISTRY["ask_user"]["claude"]
_CAPABILITY = "ask_user"


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


def test_raw_token_in_a_shared_fragment_is_reported(tmp_path: Path) -> None:
    # A shared fragment the build inlines into plugin output is enforced too — a
    # raw token there leaks into every target that includes it. The step
    # enumerates src/_shared/ alongside src/plugins/.
    builder = SrcTreeBuilder(tmp_path)
    builder.add_shared_topic(
        "shared-scope", "shared-topic", fragment_body=f"Ask via {_RAW_NAME}.\n"
    )
    fragment = (
        builder.shared_root / "shared-scope" / "shared-topic" / SHARED_FRAGMENT_FILENAME
    )

    violations = scan_file(fragment)
    assert [v.token for v in violations] == [_RAW_NAME]


def test_ignored_file_with_raw_token_is_exempt(tmp_path: Path) -> None:
    # An entry on the ignore-list is the explicit, tracked exemption: a file
    # carrying a raw token is not reported when its repo-relative path is on the
    # ignore-list, and is reported when it is not. The live exemption set is empty
    # (full enforcement), so a controlled ignore-list and root inject the exemption
    # the scenario exercises.
    skill = tmp_path / "plugins" / "wip" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(f"# Heading\n\nUse {_RAW_NAME} to ask.\n", encoding="utf-8")
    relative = "plugins/wip/SKILL.md"

    assert scan_file(skill, ignore=frozenset({relative}), repo_root=tmp_path) == []

    reported = scan_file(skill, ignore=frozenset(), repo_root=tmp_path)
    assert [v.token for v in reported] == [_RAW_NAME]

    # The same exemption applies through scan_paths, the delegation layer the CLI
    # entry point (main) drives: an ignore-listed file is exempt, an un-ignored one
    # is reported.
    assert scan_paths([skill], ignore=frozenset({relative}), repo_root=tmp_path) == []
    via_paths = scan_paths([skill], ignore=frozenset(), repo_root=tmp_path)
    assert [v.token for v in via_paths] == [_RAW_NAME]

    # ...and through main, the CLI entry point: an ignore-listed file exits 0, an
    # un-ignored one carrying a raw token exits non-zero. This covers the full
    # main -> scan_paths -> scan_file exemption path the gate step runs.
    assert main([str(skill)], ignore=frozenset({relative}), repo_root=tmp_path) == 0
    assert main([str(skill)], ignore=frozenset(), repo_root=tmp_path) == 1
