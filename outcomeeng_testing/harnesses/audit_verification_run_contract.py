"""Repository-owned audit contract checks."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from itertools import pairwise
from pathlib import Path
from shutil import rmtree
from tempfile import TemporaryDirectory
from typing import Final, cast

from outcomeeng.validation.audit_artifacts import (
    AGENTS_DIR_NAME,
    IMPLEMENTATION_AUDITOR_FILENAME,
    LANGUAGE_AUDIT_CONCERNS,
    LANGUAGE_AUDIT_SKILL_TEMPLATE,
    LANGUAGE_CODE_SKILL_TEMPLATE,
    PLUGIN_SURFACE_PATHS,
    RETIRED_AUDIT_RUNTIME_FILENAMES,
    RETIRED_IMPLEMENTATION_AUDITOR_FILENAMES,
    RETIRED_LANGUAGE_AUDIT_SKILL_TEMPLATE,
    SKILL_FILENAME,
    SKILLS_DIR_NAME,
    SPEC_TREE_PLUGIN_NAME,
    check_audit_artifact_contract,
    check_audit_runtime_surface,
    check_language_concern_surface,
    check_runtime_surface,
    check_wrapper_surface,
    implementation_audit_runtime_directory,
    implementation_languages,
    language_specific_auditor_filenames,
)
from outcomeeng.validation.implementation_audit_contract import (
    RUN_FINDING_COUNT_FIELD,
    RUN_SEALED_FIELD,
    RUN_SEQUENCE_FIELD,
    RUN_TERMINAL_STATUS_FIELD,
    RUN_TOKEN_FIELD,
    AuditTerminalStatus,
    ImplementationAuditConcern,
    expected_verification_projection,
    implementation_audit_finding_key,
    implementation_audit_finding_payload,
    implementation_audit_input_payload,
    implementation_audit_provenance,
    implementation_audit_scope_payload,
)
from outcomeeng.validation.spx_version import (
    BUNX_COMMAND_PREFIX,
    BUNX_EXECUTABLE,
    NPX_COMMAND_PREFIX,
    NPX_EXECUTABLE,
    PNPM_COMMAND_PREFIX,
    PNPM_EXECUTABLE,
    REQUIRED_SPX_VERSION,
    SPX_PACKAGE_NAME,
    VERIFICATION_RUN_MINIMUM_SPX_VERSION,
    VERIFICATION_RUN_REQUIRED_COMMANDS,
    WORKFLOW_PATH,
    is_satisfied,
    minimum_release_package_command,
    parse_version,
    read_pinned_version,
    verification_run_floor_is_satisfied,
)
from outcomeeng_testing.generators.audit_verification_run_contract import (
    implementation_audit_verification_probes,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
SPX_RELEASE_FIXTURE: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "spx_verification_run_release.json"
)
SPX_VERIFICATION_RUN_HELP_FIXTURE: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "spx_verification_run_help.txt"
)


def spx_floor_provides_verification_run_lifecycle() -> bool:
    """Return whether the repository floor includes verification runs."""
    release = _verification_run_release()
    published_version = _required_string(release, "version")
    integrity = _required_string(release, "dist.integrity")
    tarball = _required_string(release, "dist.tarball")
    help_text = SPX_VERIFICATION_RUN_HELP_FIXTURE.read_text(encoding="utf-8")
    pinned_version = read_pinned_version(WORKFLOW_PATH.read_text(encoding="utf-8"))
    return (
        pinned_version is not None
        and published_version == VERIFICATION_RUN_MINIMUM_SPX_VERSION
        and integrity.startswith("sha512-")
        and tarball.endswith(f"spx-{published_version}.tgz")
        and is_satisfied(REQUIRED_SPX_VERSION, published_version)
        and verification_run_floor_is_satisfied(REQUIRED_SPX_VERSION)
        and verification_run_floor_is_satisfied(pinned_version)
        and is_satisfied(pinned_version, REQUIRED_SPX_VERSION)
        and all(
            f"  {command}" in help_text
            for command in VERIFICATION_RUN_REQUIRED_COMMANDS
        )
    )


def audit_contract_rejects_below_verification_run_floor() -> bool:
    """Return whether validation rejects the version before the published floor."""
    minimum = parse_version(VERIFICATION_RUN_MINIMUM_SPX_VERSION)
    below_floor = ".".join(str(part) for part in (*minimum[:-1], minimum[-1] - 1))
    return not verification_run_floor_is_satisfied(below_floor)


def implementation_auditor_is_the_only_implementation_wrapper() -> bool:
    """Return whether every live surface satisfies wrapper identity rules."""
    return _all_live_surfaces_pass(check_wrapper_surface)


def language_concern_skill_trios_exist() -> bool:
    """Return whether the live repository satisfies cross-surface audit rules."""
    return not check_audit_artifact_contract(REPO_ROOT)


def implementation_audit_runtime_contains_only_skill() -> bool:
    """Return whether every live audit runtime satisfies artifact rules."""
    return _all_live_surfaces_pass(check_audit_runtime_surface)


def audit_runtime_trees_exclude_retired_artifacts() -> bool:
    """Return whether every live audit runtime satisfies artifact rules."""
    return _all_live_surfaces_pass(check_audit_runtime_surface)


def spx_verification_run_accepts_implementation_audit_payloads() -> bool:
    """Exercise the SPX lifecycle used by implementation-audit orchestration."""
    spx_command = _minimum_release_spx_command()
    rule = spx_verification_run_accepts_implementation_audit_payloads.__name__
    terminal_status = AuditTerminalStatus.REJECTED

    with TemporaryDirectory() as temporary_directory:
        repository = Path(temporary_directory)
        scope, run_token, scope_reports, finding_report = (
            _record_implementation_audit_finding(
                repository,
                rule,
                spx_verification_run_accepts_implementation_audit_payloads.__doc__
                or rule,
                spx_command,
            )
        )
        finish_report = _run_spx(
            repository,
            spx_command,
            ("finish",),
            scope,
            run_token=run_token,
            terminal_status=terminal_status.value,
        )
        render_report = _run_spx(
            repository,
            spx_command,
            ("render",),
            scope,
            run_token=run_token,
        )

    scope_sequences = tuple(
        scope_report.get(RUN_SEQUENCE_FIELD) for scope_report in scope_reports
    )
    scope_sequence_numbers = tuple(
        sequence for sequence in scope_sequences if isinstance(sequence, int)
    )
    actual_projection = (
        bool(scope_sequence_numbers)
        and len(scope_sequence_numbers) == len(scope_sequences)
        and all(
            current == previous + 1
            for previous, current in pairwise(scope_sequence_numbers)
        )
        and finding_report.get(RUN_SEQUENCE_FIELD) == scope_sequence_numbers[-1] + 1,
        finish_report.get(RUN_TERMINAL_STATUS_FIELD),
        finish_report.get(RUN_SEALED_FIELD),
        render_report.get(RUN_TOKEN_FIELD),
        render_report.get(RUN_FINDING_COUNT_FIELD),
        render_report.get(RUN_SEALED_FIELD),
        render_report.get(RUN_TERMINAL_STATUS_FIELD),
    )
    return actual_projection == expected_verification_projection(
        run_token,
        finding_count=1,
        terminal_status=terminal_status,
    )


def spx_verification_run_rejects_mismatched_terminal_status() -> bool:
    """Return whether SPX rejects approval after a blocking finding."""
    spx_command = _minimum_release_spx_command()
    rule = spx_verification_run_rejects_mismatched_terminal_status.__name__

    with TemporaryDirectory() as temporary_directory:
        repository = Path(temporary_directory)
        scope, run_token, _, _ = _record_implementation_audit_finding(
            repository,
            rule,
            spx_verification_run_rejects_mismatched_terminal_status.__doc__ or rule,
            spx_command,
        )
        try:
            _run_spx(
                repository,
                spx_command,
                ("finish",),
                scope,
                run_token=run_token,
                terminal_status=AuditTerminalStatus.APPROVED.value,
            )
        except subprocess.CalledProcessError:
            return True

    return False


def audit_contract_rejects_language_specific_wrapper() -> bool:
    """Return whether validation rejects every language wrapper filename."""
    language = _source_language()
    return all(
        _language_wrapper_filename_is_rejected(language, filename)
        for filename in language_specific_auditor_filenames(language)
    )


def audit_contract_rejects_language_wrapper_under_spec_tree() -> bool:
    """Reject every language wrapper filename under the generic host."""
    language = _source_language()
    return all(
        _language_wrapper_filename_is_rejected(
            SPEC_TREE_PLUGIN_NAME,
            filename,
        )
        for filename in language_specific_auditor_filenames(language)
    )


def audit_contract_rejects_unrecognized_language_specific_wrapper() -> bool:
    """Reject a language-specific wrapper without a matching code skill."""
    with _valid_surface() as surface:
        filename = f"java-{ImplementationAuditConcern.CODE.value}-auditor.md"
        _touch(surface / SPEC_TREE_PLUGIN_NAME / AGENTS_DIR_NAME / filename)
        return bool(check_wrapper_surface(surface))


def minimum_release_runner_supports_npx_fallback() -> bool:
    """Return whether exact-release selection falls back to standard npm tooling."""
    minimum_version = _required_string(_verification_run_release(), "version")
    package_spec = f"{SPX_PACKAGE_NAME}@{minimum_version}"
    return minimum_release_package_command(
        package_spec,
        executable_finder=_find_npx_only,
    ) == (*NPX_COMMAND_PREFIX, package_spec)


def minimum_release_runner_preserves_precedence() -> bool:
    """Prove each source-owned exact-release package-runner precedence branch."""
    minimum_version = _required_string(_verification_run_release(), "version")
    package_spec = f"{SPX_PACKAGE_NAME}@{minimum_version}"
    cases = (
        (
            frozenset((PNPM_EXECUTABLE, BUNX_EXECUTABLE, NPX_EXECUTABLE)),
            PNPM_COMMAND_PREFIX,
        ),
        (
            frozenset((BUNX_EXECUTABLE, NPX_EXECUTABLE)),
            BUNX_COMMAND_PREFIX,
        ),
        (frozenset((NPX_EXECUTABLE,)), NPX_COMMAND_PREFIX),
    )
    return all(
        minimum_release_package_command(
            package_spec,
            executable_finder=_available_executable_finder(available),
        )
        == (*expected_prefix, package_spec)
        for available, expected_prefix in cases
    )


def implementation_audit_unit_ids_are_subject_specific() -> bool:
    """Keep coverage and finding identity distinct for each subject path."""
    language = _source_language()
    provenance = implementation_audit_provenance(
        agent_plugin_version=_plugin_version(SPEC_TREE_PLUGIN_NAME),
        language_plugin_version=_plugin_version(language),
        tool_version=REQUIRED_SPX_VERSION,
    )
    probes = implementation_audit_verification_probes(language)
    scope_payloads = tuple(
        implementation_audit_scope_payload(
            probe.language,
            probe.concern,
            subject_path=probe.subject_path,
            producer_provenance=provenance,
        )
        for probe in probes
    )
    finding_payloads = tuple(
        implementation_audit_finding_payload(
            probe.language,
            probe.concern,
            rule=implementation_audit_unit_ids_are_subject_specific.__name__,
            subject_path=probe.subject_path,
            message=implementation_audit_unit_ids_are_subject_specific.__doc__
            or probe.unit_id,
            observed=probe.subject_path,
            expected=probe.unit_id,
            producer_provenance=provenance,
        )
        for probe in probes
    )
    return len({probe.unit_id for probe in probes}) == len(probes) and all(
        scope_payload["unitId"] == probe.unit_id
        and finding_payload["unitId"] == probe.unit_id
        for probe, scope_payload, finding_payload in zip(
            probes,
            scope_payloads,
            finding_payloads,
            strict=True,
        )
    )


def implementation_audit_payloads_reject_empty_subject() -> bool:
    """Reject scope and finding payloads without a concrete subject."""
    language = _source_language()
    concern = ImplementationAuditConcern.CODE
    provenance = implementation_audit_provenance(
        agent_plugin_version=_plugin_version(SPEC_TREE_PLUGIN_NAME),
        language_plugin_version=_plugin_version(language),
        tool_version=REQUIRED_SPX_VERSION,
    )
    try:
        implementation_audit_scope_payload(
            language,
            concern,
            subject_path="",
            producer_provenance=provenance,
        )
    except ValueError:
        pass
    else:
        return False

    try:
        implementation_audit_finding_payload(
            language,
            concern,
            rule=implementation_audit_payloads_reject_empty_subject.__name__,
            subject_path="",
            message=implementation_audit_payloads_reject_empty_subject.__doc__ or "",
            observed="",
            expected=implementation_audit_payloads_reject_empty_subject.__name__,
            producer_provenance=provenance,
        )
    except ValueError:
        return True
    return False


def audit_contract_rejects_retired_implementation_wrappers() -> bool:
    """Return whether validation rejects every retired wrapper name."""
    return all(
        _retired_implementation_wrapper_is_rejected(filename)
        for filename in RETIRED_IMPLEMENTATION_AUDITOR_FILENAMES
    )


def audit_contract_rejects_retired_wrappers_in_every_plugin() -> bool:
    """Return whether every retired wrapper is rejected in every source plugin."""
    return all(
        _language_wrapper_filename_is_rejected(plugin_name, filename)
        for plugin_name in _source_plugin_names()
        for filename in RETIRED_IMPLEMENTATION_AUDITOR_FILENAMES
    )


def audit_contract_rejects_incomplete_language_trio() -> bool:
    """Return whether validation rejects a missing language concern skill."""
    with _valid_surface() as surface:
        language = _source_language()
        concern = LANGUAGE_AUDIT_CONCERNS[-1]
        _language_concern_path(surface, language, concern).unlink()
        return bool(check_language_concern_surface(surface))


def audit_contract_rejects_retired_language_audit_skill() -> bool:
    """Return whether validation rejects a retired aggregate language audit skill."""
    with _valid_surface() as surface:
        language = _source_language()
        retired_skill = (
            surface
            / language
            / SKILLS_DIR_NAME
            / RETIRED_LANGUAGE_AUDIT_SKILL_TEMPLATE.format(language=language)
        )
        _touch(retired_skill / SKILL_FILENAME)
        return bool(check_language_concern_surface(surface))


def audit_contract_rejects_missing_generated_surface() -> bool:
    """Reject a repository missing one declared generated plugin surface."""
    with _valid_repository_surfaces() as root:
        rmtree(root / PLUGIN_SURFACE_PATHS[-1])
        return bool(check_audit_artifact_contract(root))


def audit_contract_rejects_missing_generated_audit_host() -> bool:
    """Reject a generated surface missing the audit-owning plugin."""
    with _valid_repository_surfaces() as root:
        rmtree(root / PLUGIN_SURFACE_PATHS[-1] / SPEC_TREE_PLUGIN_NAME)
        return bool(check_audit_artifact_contract(root))


def audit_contract_rejects_missing_single_surface_audit_host() -> bool:
    """Reject a lone source surface missing the audit-owning plugin."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        surface = root / PLUGIN_SURFACE_PATHS[0]
        _populate_valid_surface(surface, _source_language())
        rmtree(surface / SPEC_TREE_PLUGIN_NAME)
        return bool(check_audit_artifact_contract(root))


def audit_contract_rejects_missing_generated_language() -> bool:
    """Reject a generated surface missing an expected language plugin."""
    with _valid_repository_surfaces() as root:
        rmtree(root / PLUGIN_SURFACE_PATHS[-1] / _source_language())
        return bool(check_audit_artifact_contract(root))


def audit_contract_rejects_missing_single_surface_language() -> bool:
    """Reject a lone source surface missing one language concern skill."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        surface = root / PLUGIN_SURFACE_PATHS[0]
        language = _source_language()
        _populate_valid_surface(surface, language)
        _language_concern_path(
            surface,
            language,
            LANGUAGE_AUDIT_CONCERNS[-1],
        ).unlink()
        return bool(check_audit_artifact_contract(root))


def audit_contract_rejects_extra_runtime_artifact() -> bool:
    """Return whether validation rejects an extra runtime artifact."""
    with _valid_surface() as surface:
        runtime_dir = implementation_audit_runtime_directory(surface)
        _touch(runtime_dir / f"{SKILL_FILENAME}.extra")
        return bool(check_runtime_surface(surface))


def audit_contract_rejects_missing_runtime_skill() -> bool:
    """Return whether validation rejects a missing runtime skill."""
    with _valid_surface() as surface:
        runtime_dir = implementation_audit_runtime_directory(surface)
        (runtime_dir / SKILL_FILENAME).unlink()
        return bool(check_runtime_surface(surface))


def audit_contract_rejects_retired_artifact_in_other_runtime() -> bool:
    """Return whether validation rejects retired files in another audit skill."""
    with _valid_surface() as surface:
        runtime_dir = surface / SPEC_TREE_PLUGIN_NAME / SKILLS_DIR_NAME / "audit-tests"
        _touch(runtime_dir / SKILL_FILENAME)
        _touch(runtime_dir / "scripts" / RETIRED_AUDIT_RUNTIME_FILENAMES[0])
        return bool(check_audit_runtime_surface(surface))


def audit_contract_rejects_retired_artifact_in_language_runtime() -> bool:
    """Reject a retired runtime file in a language concern skill."""
    with _valid_surface() as surface:
        language = _source_language()
        runtime_dir = _language_concern_path(
            surface,
            language,
            LANGUAGE_AUDIT_CONCERNS[0],
        ).parent
        _touch(runtime_dir / "scripts" / RETIRED_AUDIT_RUNTIME_FILENAMES[0])
        return bool(check_audit_runtime_surface(surface))


def _all_live_surfaces_pass(check: Callable[[Path], list[str]]) -> bool:
    return all(not check(REPO_ROOT / relative) for relative in PLUGIN_SURFACE_PATHS)


@contextmanager
def _valid_surface() -> Iterator[Path]:
    with TemporaryDirectory() as temporary_directory:
        surface = Path(temporary_directory)
        _populate_valid_surface(surface, _source_language())
        yield surface


@contextmanager
def _valid_repository_surfaces() -> Iterator[Path]:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        language = _source_language()
        for relative_surface in PLUGIN_SURFACE_PATHS:
            _populate_valid_surface(root / relative_surface, language)
        yield root


def _populate_valid_surface(surface: Path, language: str) -> None:
    _touch(
        surface
        / language
        / SKILLS_DIR_NAME
        / LANGUAGE_CODE_SKILL_TEMPLATE.format(language=language)
        / SKILL_FILENAME
    )
    for concern in LANGUAGE_AUDIT_CONCERNS:
        _touch(_language_concern_path(surface, language, concern))
    _touch(
        surface
        / SPEC_TREE_PLUGIN_NAME
        / AGENTS_DIR_NAME
        / IMPLEMENTATION_AUDITOR_FILENAME
    )
    _touch(implementation_audit_runtime_directory(surface) / SKILL_FILENAME)


def _language_concern_path(surface: Path, language: str, concern: str) -> Path:
    return (
        surface
        / language
        / SKILLS_DIR_NAME
        / LANGUAGE_AUDIT_SKILL_TEMPLATE.format(language=language, concern=concern)
        / SKILL_FILENAME
    )


def _retired_implementation_wrapper_is_rejected(filename: str) -> bool:
    with _valid_surface() as surface:
        _touch(surface / SPEC_TREE_PLUGIN_NAME / AGENTS_DIR_NAME / filename)
        return bool(check_wrapper_surface(surface))


def _language_wrapper_filename_is_rejected(
    plugin_name: str,
    filename: str,
) -> bool:
    with _valid_surface() as surface:
        _touch(surface / plugin_name / AGENTS_DIR_NAME / filename)
        return bool(check_wrapper_surface(surface))


def _source_language() -> str:
    return implementation_languages(REPO_ROOT / PLUGIN_SURFACE_PATHS[0])[0]


def _source_plugin_names() -> tuple[str, ...]:
    source_surface = REPO_ROOT / PLUGIN_SURFACE_PATHS[0]
    return tuple(
        sorted(path.name for path in source_surface.iterdir() if path.is_dir())
    )


def _record_implementation_audit_finding(
    repository: Path,
    rule: str,
    message: str,
    spx_command: tuple[str, ...],
) -> tuple[str, str, tuple[dict[str, object], ...], dict[str, object]]:
    language = _source_language()
    probes = implementation_audit_verification_probes(language)
    provenance = implementation_audit_provenance(
        agent_plugin_version=_plugin_version(SPEC_TREE_PLUGIN_NAME),
        language_plugin_version=_plugin_version(language),
        tool_version=_spx_version(spx_command),
    )
    _initialize_changeset_repository(
        repository,
        tuple(probe.subject_path for probe in probes),
    )
    scope = _changeset_scope(repository)
    start_report = _run_spx(
        repository,
        spx_command,
        ("start",),
        scope,
        payload=implementation_audit_input_payload(rule),
    )
    run_token = _required_string(start_report, RUN_TOKEN_FIELD)
    scope_reports = tuple(
        _run_spx(
            repository,
            spx_command,
            ("scope", "add"),
            scope,
            run_token=run_token,
            payload=implementation_audit_scope_payload(
                probe.language,
                probe.concern,
                subject_path=probe.subject_path,
                producer_provenance=provenance,
            ),
            idempotency_key=probe.unit_id,
        )
        for probe in probes
    )
    finding_probe = probes[-1]
    finding_report = _run_spx(
        repository,
        spx_command,
        ("finding", "add"),
        scope,
        run_token=run_token,
        payload=implementation_audit_finding_payload(
            finding_probe.language,
            finding_probe.concern,
            rule=rule,
            subject_path=finding_probe.subject_path,
            message=message,
            observed=finding_probe.subject_path,
            expected=finding_probe.subject_path,
            producer_provenance=provenance,
        ),
        idempotency_key=implementation_audit_finding_key(
            finding_probe.language,
            finding_probe.concern,
            subject_path=finding_probe.subject_path,
            rule=rule,
        ),
    )
    return scope, run_token, scope_reports, finding_report


def _initialize_changeset_repository(
    repository: Path,
    subject_paths: tuple[str, ...],
) -> None:
    _run(repository, ("git", "init", "-q"))
    _run(repository, ("git", "config", "user.email", "audit@example.com"))
    _run(repository, ("git", "config", "user.name", "Audit Contract"))
    for subject in subject_paths:
        subject_path = repository / subject
        subject_path.parent.mkdir(parents=True, exist_ok=True)
        subject_path.write_text("", encoding="utf-8")
    _run(repository, ("git", "add", *subject_paths))
    _run(repository, ("git", "commit", "-q", "-m", "initial"))
    for subject in subject_paths:
        (repository / subject).write_text(__doc__ or subject, encoding="utf-8")
    _run(repository, ("git", "add", *subject_paths))
    _run(repository, ("git", "commit", "-q", "-m", "change"))


def _changeset_scope(repository: Path) -> str:
    base = _run(repository, ("git", "rev-parse", "HEAD~1")).stdout.strip()
    head = _run(repository, ("git", "rev-parse", "HEAD")).stdout.strip()
    return f"{base}..{head}"


def _run_spx(
    repository: Path,
    spx_command: tuple[str, ...],
    action: tuple[str, ...],
    scope: str,
    *,
    run_token: str | None = None,
    payload: Mapping[str, object] | None = None,
    idempotency_key: str | None = None,
    terminal_status: str | None = None,
) -> dict[str, object]:
    command = (
        *spx_command,
        "verification",
        "run",
        *action,
        "--verification-type",
        "audit",
        "--scope-type",
        "changeset",
        "--scope",
        scope,
    )
    if action == ("start",):
        command += ("--input", "stdin")
    if run_token is not None:
        command += ("--run", run_token)
    if idempotency_key is not None:
        command += ("--payload", "stdin", "--idempotency-key", idempotency_key)
    if terminal_status is not None:
        command += ("--terminal-status", terminal_status)
    input_text = None if payload is None else f"{json.dumps(payload)}\n"
    parsed = cast(
        object,
        json.loads(_run(repository, command, input_text).stdout),
    )
    if not isinstance(parsed, dict):
        raise TypeError("spx command did not return a JSON object")
    return cast(dict[str, object], parsed)


def _plugin_version(plugin_name: str) -> str:
    manifest_path = (
        REPO_ROOT
        / PLUGIN_SURFACE_PATHS[0]
        / plugin_name
        / ".claude-plugin"
        / "plugin.json"
    )
    manifest = cast(object, json.loads(manifest_path.read_text(encoding="utf-8")))
    if not isinstance(manifest, dict):
        raise TypeError(f"plugin manifest is not a JSON object: {manifest_path}")
    return _required_string(manifest, "version")


def _minimum_release_spx_command() -> tuple[str, ...]:
    minimum_version = _required_string(_verification_run_release(), "version")
    package_spec = f"{SPX_PACKAGE_NAME}@{minimum_version}"
    minimum_command = minimum_release_package_command(package_spec)

    actual_version = _spx_version(minimum_command)
    if actual_version != minimum_version:
        raise RuntimeError(
            "minimum-release SPX command returned "
            f"{actual_version}, expected {minimum_version}"
        )
    return minimum_command


def _find_npx_only(executable: str) -> str | None:
    return executable if executable == NPX_EXECUTABLE else None


def _available_executable_finder(
    available: frozenset[str],
) -> Callable[[str], str | None]:
    def find(executable: str) -> str | None:
        return executable if executable in available else None

    return find


def _verification_run_release() -> Mapping[str, object]:
    release = cast(
        object,
        json.loads(SPX_RELEASE_FIXTURE.read_text(encoding="utf-8")),
    )
    if not isinstance(release, dict):
        raise TypeError("SPX release fixture is not a JSON object")
    return cast(dict[str, object], release)


def _spx_version(spx_command: tuple[str, ...]) -> str:
    return _run(REPO_ROOT, (*spx_command, "--version")).stdout.strip()


def _run(
    repository: Path,
    arguments: tuple[str, ...],
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=repository,
        input=input_text,
        text=True,
        check=True,
        capture_output=True,
    )


def _required_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise TypeError(f"missing string field: {key}")
    return value


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
