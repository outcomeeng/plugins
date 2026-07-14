"""Resource lifecycle and observations for runtime-token evidence."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.build import SHARED_DIR_NAME, SHARED_FRAGMENT_FILENAME
from outcomeeng.distribution.contracts import (
    PLUGINS_DIR_NAME,
    SKILL_FILENAME,
    SOURCE_ROOT_NAME,
    TEXT_FILE_SUFFIXES,
    format_runtime_token,
)
from outcomeeng.validation._steps import runtime_token_files
from outcomeeng.validation.runtime_tokens import (
    RUNTIME_TOKEN_IGNORE,
    forbidden_names,
    is_ignored,
    main,
    scan_file,
    scan_paths,
)
from outcomeeng_testing.generators.runtime_tokens import (
    RuntimeNameCase,
    lint_enforced_runtime_names,
    review_only_runtime_names,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder


def raw_token_report_matches_contract() -> bool:
    """Exercise file, line, token, output, and failing exit status together."""
    for case in lint_enforced_runtime_names():
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / SKILL_FILENAME
            content, expected_line = _raw_fixture(case)
            path.write_text(content, encoding="utf-8")
            violations = scan_file(path)
            output = StringIO()
            with redirect_stdout(output):
                exit_code = main([str(path)])
            report = output.getvalue()
            if not (
                len(violations) == 1
                and violations[0].line == expected_line
                and violations[0].token == case.name
                and exit_code != 0
                and str(path) in report
                and f":{expected_line}:" in report
                and case.name in report
            ):
                return False
    return True


def token_expression_matches_contract() -> bool:
    """Exercise a source-owned runtime token through the command boundary."""
    for case in lint_enforced_runtime_names():
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / SKILL_FILENAME
            path.write_text(
                format_runtime_token(case.kind, case.capability),
                encoding="utf-8",
            )
            output = StringIO()
            with redirect_stdout(output):
                exit_code = main([str(path)])
            if exit_code != 0 or output.getvalue() != "" or scan_file(path) != []:
                return False
    return True


def ignored_file_matches_contract() -> bool:
    """Exercise one controlled ignore entry through scan and command layers."""
    for case in lint_enforced_runtime_names():
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            path = (
                root
                / SOURCE_ROOT_NAME
                / PLUGINS_DIR_NAME
                / case.capability
                / SKILL_FILENAME
            )
            path.parent.mkdir(parents=True)
            path.write_text(_raw_fixture(case)[0], encoding="utf-8")
            relative = path.relative_to(root).as_posix()
            ignore = frozenset({relative})
            output = StringIO()
            with redirect_stdout(output):
                exit_code = main([str(path)], ignore=ignore, repo_root=root)
            if not (
                is_ignored(path, ignore=ignore, repo_root=root)
                and scan_file(path, ignore=ignore, repo_root=root) == []
                and scan_paths([path], ignore=ignore, repo_root=root) == []
                and exit_code == 0
                and output.getvalue() == ""
                and bool(scan_file(path, ignore=frozenset(), repo_root=root))
            ):
                return False
    return True


def shared_fragment_raw_token_is_reported() -> bool:
    """Exercise default enforcement over a generated shared fragment."""
    for case in lint_enforced_runtime_names():
        with TemporaryDirectory() as temporary_directory:
            builder = SrcTreeBuilder(Path(temporary_directory))
            topic = case.capability.replace("_", "-")
            builder.add_shared_topic(
                case.kind,
                topic,
                fragment_body=_raw_fixture(case)[0],
            )
            fragment = (
                builder.shared_root / case.kind / topic / SHARED_FRAGMENT_FILENAME
            )
            if [violation.token for violation in scan_file(fragment)] != [case.name]:
                return False
    return True


def every_enforced_registry_name_is_rejected() -> bool:
    """Exercise every source-owned guard-enforced registry name."""
    with TemporaryDirectory() as temporary_directory:
        path = Path(temporary_directory) / SKILL_FILENAME
        for case in lint_enforced_runtime_names():
            path.write_text(_raw_fixture(case)[0], encoding="utf-8")
            if [violation.token for violation in scan_file(path)] != [case.name]:
                return False
        return True


def forbidden_names_derive_from_enforced_registry_kinds() -> bool:
    """Compare the derived names with the registry's independently flattened set."""
    expected = frozenset(case.name for case in lint_enforced_runtime_names())
    return frozenset(forbidden_names()) == expected


def review_only_names_are_excluded() -> bool:
    """Exercise every source-owned review-only name against the forbidden set."""
    forbidden = frozenset(forbidden_names())
    review_only = review_only_runtime_names()
    return bool(review_only) and all(case.name not in forbidden for case in review_only)


def authored_tree_default_enforcement_matches_contract() -> bool:
    """Compare the gate selector with an independent authored-tree inventory."""
    source_root = Path.cwd().resolve() / SOURCE_ROOT_NAME
    roots = (
        source_root / PLUGINS_DIR_NAME,
        source_root / SHARED_DIR_NAME,
    )
    expected_files = {
        path.resolve()
        for root in roots
        if root.is_dir()
        for path in root.rglob("*")
        if path.is_file() and path.suffix in TEXT_FILE_SUFFIXES
    }
    gate_files = {Path(raw_path).resolve() for raw_path in runtime_token_files()}
    if not gate_files or gate_files != expected_files or scan_paths(gate_files):
        return False
    return all(
        is_ignored(Path(raw_path))
        == (
            Path(raw_path).resolve().relative_to(Path.cwd().resolve()).as_posix()
            in RUNTIME_TOKEN_IGNORE
        )
        for raw_path in gate_files
    )


def _raw_fixture(case: RuntimeNameCase) -> tuple[str, int]:
    prefix_lines = (f"# {case.capability}", "")
    return "\n".join((*prefix_lines, case.name, "")), len(prefix_lines) + 1
