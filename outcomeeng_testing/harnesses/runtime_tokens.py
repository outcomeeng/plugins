"""Resource lifecycle and observations for runtime-token evidence."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.build import (
    SHARED_DIR_NAME,
    SHARED_FRAGMENT_FILENAME,
    TEMPLATES_DIR_NAME,
)
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
    empty_enforcement_registry,
    inverted_enforcement_registry_probe,
    lint_enforced_runtime_names,
    review_only_runtime_names,
    runtime_conditional_cases,
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
    """Exercise token and conditional expressions through the command boundary."""
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
    for conditional_case in runtime_conditional_cases():
        for source in conditional_case.matching_sources:
            if not _source_passes(source):
                return False
        for source in conditional_case.mismatching_sources:
            if _source_passes(source):
                return False
    return True


def ignored_file_matches_contract() -> bool:
    """Exercise every production ignore entry through scan and command layers."""
    for case in lint_enforced_runtime_names():
        for relative in RUNTIME_TOKEN_IGNORE:
            with TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory).resolve()
                path = root / relative
                path.parent.mkdir(parents=True)
                path.write_text(_raw_fixture(case)[0], encoding="utf-8")
                output = StringIO()
                with redirect_stdout(output):
                    exit_code = main([str(path)], repo_root=root)
                if not (
                    is_ignored(path, repo_root=root)
                    and scan_file(path, repo_root=root) == []
                    and scan_paths([path], repo_root=root) == []
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
    """Exercise controlled registry enforcement through every scanner layer."""
    probe = inverted_enforcement_registry_probe()
    empty_registry = empty_enforcement_registry()
    with TemporaryDirectory() as temporary_directory:
        path = Path(temporary_directory) / SKILL_FILENAME
        path.write_text(
            "\n".join((*probe.enforced_names, *probe.excluded_names)),
            encoding="utf-8",
        )
        violations = scan_file(path, registry=probe.registry)
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main([str(path)], registry=probe.registry)
        return (
            frozenset(forbidden_names(registry=probe.registry))
            == frozenset(probe.enforced_names)
            and {violation.token for violation in violations}
            == set(probe.enforced_names)
            and exit_code != 0
            and all(name in output.getvalue() for name in probe.enforced_names)
            and scan_file(path, registry=empty_registry) == []
            and main([str(path)], registry=empty_registry) == 0
        )


def review_only_names_are_excluded() -> bool:
    """Exercise every source-owned review-only name against the forbidden set."""
    forbidden = frozenset(forbidden_names())
    review_only = review_only_runtime_names()
    return bool(review_only) and all(case.name not in forbidden for case in review_only)


@dataclass(frozen=True)
class AuthoredTreeEnforcement:
    """The gate's selected files beside an independently derived inventory.

    Returns both sets and the per-file ignore observations rather than their
    agreement, so the linked test owns every comparison the assertion claims.
    """

    enforced_roots: tuple[Path, ...]
    expected_files: frozenset[Path]
    gate_files: frozenset[Path]
    raw_token_violations: tuple[str, ...]
    ignored_files: frozenset[Path]
    ignore_listed_files: frozenset[Path]


def authored_tree_enforcement() -> AuthoredTreeEnforcement:
    """Return the authored-tree enforcement observations, undecided."""
    repo_root = Path.cwd().resolve()
    source_root = repo_root / SOURCE_ROOT_NAME
    roots = (
        source_root / PLUGINS_DIR_NAME,
        source_root / SHARED_DIR_NAME,
        source_root / TEMPLATES_DIR_NAME,
    )
    expected_files = {
        path.resolve()
        for root in roots
        if root.is_dir()
        for path in root.rglob("*")
        if path.is_file() and path.suffix in TEXT_FILE_SUFFIXES
    }
    gate_files = {Path(raw_path).resolve() for raw_path in runtime_token_files()}
    return AuthoredTreeEnforcement(
        enforced_roots=roots,
        expected_files=frozenset(expected_files),
        gate_files=frozenset(gate_files),
        raw_token_violations=tuple(scan_paths(gate_files)),
        ignored_files=frozenset(path for path in gate_files if is_ignored(path)),
        ignore_listed_files=frozenset(
            path
            for path in gate_files
            if path.relative_to(repo_root).as_posix() in RUNTIME_TOKEN_IGNORE
        ),
    )


def _raw_fixture(case: RuntimeNameCase) -> tuple[str, int]:
    prefix_lines = (f"# {case.capability}", "")
    return "\n".join((*prefix_lines, case.name, "")), len(prefix_lines) + 1


def _source_passes(source: str) -> bool:
    with TemporaryDirectory() as temporary_directory:
        path = Path(temporary_directory) / SKILL_FILENAME
        path.write_text(source, encoding="utf-8")
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main([str(path)])
        return exit_code == 0 and output.getvalue() == "" and scan_file(path) == []
