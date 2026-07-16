"""Harness for review-changes scenario, property, and compliance tests.

Provides the shared scaffolding consumed by every test file under
``spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/tests/``:

- ``SCRIPTS_DIR`` and the per-script paths derived from it. A single source
  keeps every test file from walking ``__file__.parents[...]`` to find
  ``src/plugins/spec-tree/skills/review-changes/scripts``.
- ``REFERENCES_DIR`` and ``REVIEW_PROMPT_PATH``. Tests that assert the
  swappable prompt is a standalone reference file consume the path from
  one source.
- ``SKILL_DIR`` and ``SKILL_FILE``. The compliance tests inspect skill
  prose for the absence of an embedded prompt and presence of a
  ``${CLAUDE_SKILL_DIR}/references/review-prompt.md`` load expression.
- ``REVIEW_RUN_SCRIPT``. Tests assert the skill's public command surface is
  the single runner.
- ``JOURNAL_EMIT_SCRIPT`` and ``load_journal_emit_module``. Legacy tests assert
  the review-result-to-journal adapter consumes the shared projection.
- ``WRAPPER_AGENT_PATH``. Compliance tests check the wrapper agent's
  frontmatter shape when the agent file exists; missing files are
  tolerated (the agent is authored in a separate step).
- ``load_review_result_module``. An importlib loader for the
  ``review_result`` policy module.
- ``run_script``. A thin ``subprocess.run`` wrapper for CLI invocations.
- ``make_review_result_dict``. Factory that constructs review documents from
  the production schema module and source-derived finding values.

The harness lives in ``outcomeeng_testing/harnesses/`` because shared test
scaffolding is production code with its home outside ``tests/`` and
outside ``spx/``.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib.util
import io
import json
import os
import pathlib
import re
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field, replace
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any, Callable, cast

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.reviewing_changes import (
    REVIEW_RESULT_MODULE_PATH,
    load_review_result_module,
    make_finding_dict,
    make_review_result_dict,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

# Two ``parents`` hops land at the repository root: this file lives at
# ``outcomeeng_testing/harnesses/reviewing_changes.py``.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

SKILL_DIR = REPO_ROOT / "src" / "plugins" / "spec-tree" / "skills" / "review-changes"
SKILL_FILE = SKILL_DIR / "SKILL.md"
SCRIPTS_DIR = SKILL_DIR / "scripts"
REFERENCES_DIR = SKILL_DIR / "references"
REVIEW_PROMPT_PATH = REFERENCES_DIR / "review-prompt.md"

COMPUTE_DIFF_SCRIPT = SCRIPTS_DIR / "compute_diff.py"
JOURNAL_EMIT_SCRIPT = SCRIPTS_DIR / "journal_emit.py"
REVIEW_RUN_SCRIPT = SCRIPTS_DIR / "review_run.py"

WRAPPER_AGENT_PATH = (
    REPO_ROOT / "src" / "plugins" / "spec-tree" / "agents" / "changes-reviewer.md"
)
REVIEW_NODE_DIR = (
    REPO_ROOT
    / "spx"
    / "21-spec-tree.enabler"
    / "68-reviewing.enabler"
    / "21-reviewing-changes.enabler"
)
REVIEW_SPEC_PATH = REVIEW_NODE_DIR / "reviewing-changes.md"
REVIEW_FIXTURES_DIR = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "reviewing_changes"
)
RULE_SLUG_DOCUMENT_FIXTURE = REVIEW_FIXTURES_DIR / "rule_slug_document.md"
REVIEW_RUN_METADATA_BRANCH_FIXTURE = (
    REVIEW_FIXTURES_DIR / "review_run_metadata_branch.json"
)
REVIEW_RUN_METADATA_PULL_REQUEST_FIXTURE = (
    REVIEW_FIXTURES_DIR / "review_run_metadata_pull_request.json"
)
CONTAMINATING_JOURNAL_ENV_VALUE = "contaminating-later-env"


@contextmanager
def configured_environment(
    values: dict[str, str],
    *,
    clear: bool,
) -> Iterator[None]:
    """Apply process environment values and restore the original mapping."""

    original = os.environ.copy()
    try:
        if clear:
            os.environ.clear()
        os.environ.update(values)
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)


@contextmanager
def configured_stdin(stream: io.StringIO) -> Iterator[None]:
    """Install one in-memory stdin stream and restore the original stream."""

    original = sys.stdin
    try:
        sys.stdin = stream
        yield
    finally:
        sys.stdin = original


def review_rule_citations() -> tuple[str, ...]:
    """Return the independent citation corpus owned by the test generator."""

    from outcomeeng_testing.generators.reviewing_changes import valid_rule_citations

    return valid_rule_citations()


def malformed_rule_citation() -> str:
    """Derive a malformed citation from a valid source-owned citation."""

    return f"{review_rule_citations()[0]}:invalid"


@dataclass(frozen=True)
class RuleCitationObservation:
    """Accepted and rejected rule-citation parser observations."""

    accepted_rules: tuple[str, ...]
    expected_rules: tuple[str, ...]
    malformed_rule: str
    malformed_error: str


def rule_citation_observation() -> RuleCitationObservation:
    """Exercise every declared citation family and one derived malformed rule."""

    review_result = load_review_result_module()
    expected_rules = review_rule_citations()
    accepted_rules = tuple(
        review_result.parse_json(
            json.dumps(make_review_result_dict(findings=[make_finding_dict(rule=rule)]))
        )
        .findings[0]
        .rule
        for rule in expected_rules
    )
    malformed = malformed_rule_citation()
    try:
        review_result.parse_json(
            json.dumps(
                make_review_result_dict(findings=[make_finding_dict(rule=malformed)])
            )
        )
    except review_result.ReviewResultValidationError as exc:
        malformed_error = str(exc)
    else:
        malformed_error = ""
    return RuleCitationObservation(
        accepted_rules=accepted_rules,
        expected_rules=expected_rules,
        malformed_rule=malformed,
        malformed_error=malformed_error,
    )


def runtime_review_skill_path() -> pathlib.Path:
    """Return the generated runtime skill path used by citation validation."""

    return (
        REPO_ROOT
        / "dist"
        / "claude"
        / "spec-tree"
        / "skills"
        / "review-changes"
        / "SKILL.md"
    ).resolve(strict=True)


def rule_slug_document() -> str:
    """Return the inert markdown corpus for rule-slug discovery."""

    return RULE_SLUG_DOCUMENT_FIXTURE.read_text(encoding="utf-8")


def review_result_round_trip_holds() -> bool:
    """Run the configured ReviewResult serialization property."""

    from outcomeeng_testing.generators.reviewing_changes import review_results

    review_result = load_review_result_module()
    seed_value = review_result.SCHEMA_VERSION

    @seed(seed_value)
    @settings(max_examples=100, deadline=None)
    @given(result=review_results())
    def round_trip(result: Any) -> None:
        encoded = review_result.to_json_dict(result)
        assert review_result.from_json_dict(encoded) == result

    run_replayable_property(
        round_trip,
        seed_value=seed_value,
        replay_path=str(REVIEW_RESULT_MODULE_PATH),
    )
    return True


def malformed_finding_ids_are_rejected() -> bool:
    """Run the configured open-domain finding-identifier property."""
    from outcomeeng_testing.generators.reviewing_changes import malformed_finding_ids

    review_result = load_review_result_module()
    seed_value = review_result.SCHEMA_VERSION

    @seed(seed_value)
    @settings(max_examples=100, deadline=None)
    @given(finding_id=malformed_finding_ids())
    def rejects_invalid_identifier(finding_id: str) -> None:
        payload = json.dumps(
            make_review_result_dict(findings=[make_finding_dict(finding_id=finding_id)])
        )
        try:
            review_result.parse_json(payload)
        except review_result.ReviewResultValidationError as exc:
            assert repr(finding_id) in str(exc)
            return
        raise AssertionError(f"accepted malformed finding id {finding_id!r}")

    run_replayable_property(
        rejects_invalid_identifier,
        seed_value=seed_value,
        replay_path=str(REVIEW_RESULT_MODULE_PATH),
    )
    return True


def malformed_rule_citations_are_rejected() -> bool:
    """Run the configured open-domain rule-citation property."""
    from outcomeeng_testing.generators.reviewing_changes import (
        malformed_rule_citations,
    )

    review_result = load_review_result_module()
    seed_value = review_result.SCHEMA_VERSION

    @seed(seed_value)
    @settings(max_examples=100, deadline=None)
    @given(rule=malformed_rule_citations())
    def rejects_invalid_citation(rule: str) -> None:
        payload = json.dumps(
            make_review_result_dict(findings=[make_finding_dict(rule=rule)])
        )
        try:
            review_result.parse_json(payload)
        except review_result.ReviewResultValidationError as exc:
            assert repr(rule) in str(exc)
            return
        raise AssertionError(f"accepted malformed rule citation {rule!r}")

    run_replayable_property(
        rejects_invalid_citation,
        seed_value=seed_value,
        replay_path=str(REVIEW_RESULT_MODULE_PATH),
    )
    return True


def versioned_sibling_plugin_resolution_holds() -> bool:
    """Exercise citation resolution across versioned sibling plugin roots."""
    review_result = load_review_result_module()
    with TemporaryDirectory() as temporary_directory:
        marketplace_root = pathlib.Path(temporary_directory) / "outcomeeng"
        script_path = (
            marketplace_root
            / "spec-tree"
            / "0.77.2"
            / "skills"
            / "review-changes"
            / "scripts"
            / "review_result.py"
        )
        sibling_skill = (
            marketplace_root
            / "typescript"
            / "0.22.0"
            / "skills"
            / "code-typescript"
            / "SKILL.md"
        )
        sibling_skill.parent.mkdir(parents=True)
        sibling_skill.write_text(
            "<principles>\nALWAYS: typed\n</principles>\n", encoding="utf-8"
        )

        candidates = review_result._runtime_plugin_skill_candidates_from(
            script_path,
            "typescript",
            "code-typescript",
        )

        return sibling_skill in candidates


@dataclass(frozen=True)
class ReviewModuleSurfaceObservation:
    """Structural observations for the canonical review-result module."""

    schema_version_is_positive: bool
    severity_exists: bool
    concern_exists: bool
    decision_absent: bool
    dataclasses_are_frozen: bool
    validation_error_is_exception: bool


def review_module_surface_observation() -> ReviewModuleSurfaceObservation:
    """Inspect the production review-result module's public schema surface."""

    review_result = load_review_result_module()
    classes = (review_result.Finding, review_result.ReviewResult)
    return ReviewModuleSurfaceObservation(
        schema_version_is_positive=(
            isinstance(review_result.SCHEMA_VERSION, int)
            and review_result.SCHEMA_VERSION >= 1
        ),
        severity_exists=hasattr(review_result, "Severity"),
        concern_exists=hasattr(review_result, "Concern"),
        decision_absent=not hasattr(review_result, "Decision"),
        dataclasses_are_frozen=all(
            dataclasses.is_dataclass(cls)
            and getattr(getattr(cls, "__dataclass_params__", None), "frozen", False)
            for cls in classes
        ),
        validation_error_is_exception=issubclass(
            review_result.ReviewResultValidationError,
            Exception,
        ),
    )


@dataclass(frozen=True)
class ReviewParseComplianceObservation:
    """Parser results across the complete closed compliance case set."""

    conforming_result_type: type[Any]
    expected_result_type: type[Any]
    empty_findings: tuple[Any, ...]
    missing_document_field: str
    missing_document_error: str
    unknown_severity: str
    unknown_severity_error: str
    unknown_concern: str
    unknown_concern_error: str
    malformed_error: str
    missing_finding_field: str
    missing_finding_error: str


def _review_validation_error(payload: str) -> str:
    review_result = load_review_result_module()
    try:
        review_result.parse_json(payload)
    except review_result.ReviewResultValidationError as exc:
        return str(exc)
    return ""


def review_parse_compliance_observation() -> ReviewParseComplianceObservation:
    """Exercise conforming and every closed schema-rejection behavior."""

    review_result = load_review_result_module()
    conforming = review_result.parse_json(json.dumps(make_review_result_dict()))
    empty = review_result.parse_json(
        json.dumps(make_review_result_dict(findings=[]))
    ).findings

    missing_document_field = review_result.DOCUMENT_FINDINGS_FIELD
    missing_document = make_review_result_dict()
    del missing_document[missing_document_field]

    unknown_severity = f"{next(iter(review_result.Severity)).value}-unknown"
    unknown_concern = f"{next(iter(review_result.Concern)).value}-unknown"

    malformed_payload = json.dumps(make_review_result_dict())[:-1]

    missing_finding_field = review_result.FINDING_ACTION_FIELD
    missing_finding = make_finding_dict()
    del missing_finding[missing_finding_field]
    return ReviewParseComplianceObservation(
        conforming_result_type=type(conforming),
        expected_result_type=review_result.ReviewResult,
        empty_findings=empty,
        missing_document_field=missing_document_field,
        missing_document_error=_review_validation_error(json.dumps(missing_document)),
        unknown_severity=unknown_severity,
        unknown_severity_error=_review_validation_error(
            json.dumps(
                make_review_result_dict(
                    findings=[make_finding_dict(severity=unknown_severity)]
                )
            )
        ),
        unknown_concern=unknown_concern,
        unknown_concern_error=_review_validation_error(
            json.dumps(
                make_review_result_dict(
                    findings=[make_finding_dict(concern=unknown_concern)]
                )
            )
        ),
        malformed_error=_review_validation_error(malformed_payload),
        missing_finding_field=missing_finding_field,
        missing_finding_error=_review_validation_error(
            json.dumps(make_review_result_dict(findings=[missing_finding]))
        ),
    )


def runtime_skill_rule_resolves() -> bool:
    """Validate the runtime skill citation against its declared section slug."""

    review_result = load_review_result_module()
    citation = review_rule_citations()[3]
    review_result._validate_slug(
        runtime_review_skill_path(),
        citation.rsplit(":", maxsplit=1)[1],
        citation,
    )
    return True


def root_rule_resolves_from_subdirectory() -> bool:
    """Parse a root-guide citation while cwd is below the repository root."""

    review_result = load_review_result_module()
    citations = review_rule_citations()
    subdirectory = (
        REPO_ROOT / pathlib.Path(citations[0].split(":", maxsplit=1)[0]).parent
    )
    previous = pathlib.Path.cwd()
    try:
        os.chdir(subdirectory)
        review_result.parse_json(
            json.dumps(
                make_review_result_dict(findings=[make_finding_dict(rule=citations[4])])
            )
        )
    finally:
        os.chdir(previous)
    return True


def declared_rule_slug_observation() -> frozenset[str]:
    """Return section identities discovered from the inert markdown corpus."""

    review_result = load_review_result_module()
    return frozenset(review_result._declared_rule_slugs(rule_slug_document()))


def declared_rule_slug_contract_holds() -> bool:
    """Compare discovered section identities with the inert corpus contract."""

    return declared_rule_slug_observation() == frozenset(
        {
            "constraints",
            "critical-rules",
            "narrative",
            "principles",
            "rules",
        }
    )


def review_run_metadata(
    *,
    pull_request: bool = False,
    missing_base_identity: bool = False,
) -> Any:
    """Return source-shaped journal metadata for review mapping evidence."""

    from outcomeeng_testing.harnesses.journal_projection import (
        load_journal_projection_module,
    )

    projection = load_journal_projection_module()
    fixture_path = (
        REVIEW_RUN_METADATA_PULL_REQUEST_FIXTURE
        if pull_request
        else REVIEW_RUN_METADATA_BRANCH_FIXTURE
    )
    metadata = projection.run_metadata_from_json(
        fixture_path.read_text(encoding="utf-8")
    )
    if missing_base_identity:
        return replace(metadata, base_sha="")
    return metadata


def review_finding(*, severity: Any) -> Any:
    """Return a source-constructed finding carrying ``severity``."""

    review_result = load_review_result_module()
    return review_result.parse_finding_json(
        json.dumps(make_finding_dict(severity=severity))
    )


def review_finding_payloads() -> tuple[dict[str, Any], ...]:
    """Return one source-constructed payload for every review severity."""

    review_result = load_review_result_module()
    return tuple(
        make_finding_dict(
            finding_id=review_result.format_finding_id(index),
            severity=severity,
        )
        for index, severity in enumerate(review_result.Severity, start=1)
    )


def streamed_review_events(
    metadata: Any,
    findings: tuple[Any, ...],
) -> list[dict[str, Any]]:
    """Assemble the source event prefix produced by a streaming review."""

    journal_emit = load_journal_emit_module()
    events = [
        journal_emit.scope_entered_event(
            metadata,
            now=REVIEW_EVENT_TIME,
            attempt=1,
        ),
    ]
    events.extend(
        journal_emit.finding_reported_event(
            finding,
            now=REVIEW_EVENT_TIME,
            attempt=1,
        )
        for finding in findings
    )
    events.append(
        journal_emit.run_completed_event(
            metadata,
            events,
            completed_at=REVIEW_COMPLETION_TIME,
            now=REVIEW_EVENT_TIME,
            attempt=1,
        ),
    )
    return events


def review_metadata_wire_json() -> str:
    """Serialize source-shaped review metadata to the streaming CLI wire."""

    return REVIEW_RUN_METADATA_BRANCH_FIXTURE.read_text(encoding="utf-8")


def write_review_skill_config(root: pathlib.Path, *, prompt: str) -> None:
    """Write the standalone review prompt consumed by config digesting."""

    references = root / "references"
    references.mkdir(parents=True)
    (references / "review-prompt.md").write_text(prompt, encoding="utf-8")


@dataclass
class ReviewMetadataHarness:
    """Injected collaborators for deterministic review metadata evidence."""

    metadata: Any = field(default_factory=review_run_metadata)
    base_ref: str | None = None
    head_ref: str | None = None
    branch_name: str | None = None
    config_digest: str | None = None

    def deps(
        self,
        *,
        source_branch: bool = False,
        source_target: bool = False,
        manifest_scope: bool = False,
        fail_scope: bool = False,
        review_scope_variant: str = "primary",
    ) -> Any:
        """Return production MetadataDeps configured for one evidence boundary."""

        journal_emit = load_journal_emit_module()
        base_ref_value = self.base_ref or self.metadata.base_ref
        head_ref_value = self.head_ref or journal_emit.DEFAULT_HEAD_REF
        branch_name_value = self.branch_name or self.metadata.branch_name
        config_digest = self.config_digest or self.metadata.config_digest
        source_scope = computed_review_scopes()[review_scope_variant]

        def review_scope(
            *,
            base_ref: str,
            head_ref: str,
            repo: pathlib.Path,
        ) -> dict[str, object]:
            del repo
            if fail_scope:
                raise subprocess.CalledProcessError(
                    128,
                    ["git", "diff", f"{base_ref}...{head_ref}"],
                )
            scope = dict(source_scope)
            scope[journal_emit.SCOPE_BASE_REF_FIELD] = base_ref
            scope[journal_emit.SCOPE_HEAD_REF_FIELD] = head_ref
            return scope

        return journal_emit.MetadataDeps(
            resolve_base_ref=lambda: base_ref_value,
            resolve_head_ref=lambda: head_ref_value,
            resolve_branch_name=(
                journal_emit._resolve_branch_name
                if source_branch
                else lambda: branch_name_value
            ),
            resolve_target_kind=(
                journal_emit._resolve_target_kind
                if source_target
                else lambda: self.metadata.target_kind
            ),
            resolve_pull_request_number=(
                journal_emit._resolve_pull_request_number
                if source_target
                else lambda _target: self.metadata.pull_request_number
            ),
            review_scope=review_scope,
            review_scope_from_manifest=(
                journal_emit._review_scope_from_manifest
                if manifest_scope
                else lambda _path: review_scope(
                    base_ref=base_ref_value,
                    head_ref=head_ref_value,
                    repo=pathlib.Path.cwd(),
                )
            ),
            branch_slug=journal_emit.changeset_scope.branch_slug,
            commit_oid=lambda ref, *, repo: (
                self.metadata.head_sha
                if ref == head_ref_value
                else self.metadata.base_sha
            ),
            config_digest=lambda: config_digest,
        )


def load_compute_diff_module() -> ModuleType:
    """Load the ``compute_diff`` script as a module via importlib."""

    cached = sys.modules.get("compute_diff")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("compute_diff", COMPUTE_DIFF_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load compute_diff from {COMPUTE_DIFF_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["compute_diff"] = module
    spec.loader.exec_module(module)
    return module


def load_journal_emit_module() -> ModuleType:
    """Load the review ``journal_emit`` adapter via importlib."""

    cached = sys.modules.get("review_changes_journal_emit")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "review_changes_journal_emit", JOURNAL_EMIT_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load journal_emit from {JOURNAL_EMIT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["review_changes_journal_emit"] = module
    spec.loader.exec_module(module)
    return module


def load_review_run_module() -> ModuleType:
    """Load the review runner module via importlib."""

    cached = sys.modules.get("review_run")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("review_run", REVIEW_RUN_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load review_run from {REVIEW_RUN_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["review_run"] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class ReviewContractModules:
    """Production modules exercised by the review evidence files."""

    journal_emit: ModuleType
    journal_projection: ModuleType
    review_result: ModuleType
    review_run: ModuleType


def review_contract_modules() -> ReviewContractModules:
    """Load the production review contracts behind one harness entrypoint."""

    from outcomeeng_testing.harnesses.journal_projection import (
        load_journal_projection_module,
    )

    return ReviewContractModules(
        journal_emit=load_journal_emit_module(),
        journal_projection=load_journal_projection_module(),
        review_result=load_review_result_module(),
        review_run=load_review_run_module(),
    )


def review_config_digests() -> tuple[str, str]:
    """Return both adapters' config identity for the authored review skill."""

    contracts = review_contract_modules()
    return (
        str(contracts.journal_emit.review_config_digest(SKILL_DIR)),
        str(contracts.review_run._review_config_digest()),
    )


@dataclass(frozen=True)
class ReviewSeverityProjectionObservation:
    """Observed and declared review-severity projection sequences."""

    actual_severities: tuple[Any, ...]
    expected_severities: tuple[Any, ...]
    actual_outcomes: tuple[Any, ...]
    expected_outcomes: tuple[Any, ...]


def review_severity_projection_observation() -> ReviewSeverityProjectionObservation:
    """Exercise the complete finite review-severity projection mapping."""

    contracts = review_contract_modules()
    review_result = contracts.review_result
    projection = contracts.journal_projection
    cases = (
        (
            review_result.Severity.BLOCKING,
            projection.Severity.REJECT,
            projection.Outcome.REJECTED,
        ),
        (
            review_result.Severity.DEBT,
            projection.Severity.WARNING,
            projection.Outcome.APPROVED,
        ),
    )
    events = tuple(
        contracts.journal_emit.finding_reported_event(
            review_finding(severity=severity),
            now=REVIEW_EVENT_TIME,
            attempt=1,
        )
        for severity, _expected_severity, _expected_outcome in cases
    )
    return ReviewSeverityProjectionObservation(
        actual_severities=tuple(event["data"]["severity"] for event in events),
        expected_severities=tuple(case[1] for case in cases),
        actual_outcomes=tuple(projection.compute_overall([event]) for event in events),
        expected_outcomes=tuple(case[2] for case in cases),
    )


def review_run_journal_env_keys() -> tuple[str, ...]:
    """Return the journal-selector environment keys owned by ``review_run``."""

    module = load_review_run_module()
    return tuple(cast("tuple[str, ...]", module.JOURNAL_ENV_KEYS))


def review_run_journal_env_key(name: str) -> str:
    """Return one named journal-selector environment key from ``review_run``."""

    module = load_review_run_module()
    value = getattr(module, name)
    if not isinstance(value, str):
        raise RuntimeError(f"review_run.{name} must be a string")
    return value


def journal_emit_env_key(name: str) -> str:
    """Return one named environment key from the journal adapter."""

    module = load_journal_emit_module()
    value = getattr(module, name)
    if not isinstance(value, str):
        raise RuntimeError(f"journal_emit.{name} must be a string")
    return value


def review_run_contract_value(name: str) -> str | tuple[str, ...]:
    """Return one public field contract owned by ``review_run``."""

    module = load_review_run_module()
    value = getattr(module, name)
    if isinstance(value, str):
        return value
    if isinstance(value, tuple) and all(isinstance(item, str) for item in value):
        return cast("tuple[str, ...]", value)
    raise RuntimeError(f"review_run.{name} must be a string or string tuple")


REVIEW_EVENT_TIME = "2026-06-23T00:00:06Z"
REVIEW_COMPLETION_TIME = "2026-06-23T00:00:05Z"
REVIEW_ENV_BASE_REF = journal_emit_env_key("ENV_BASE_REF")
REVIEW_ENV_BACKEND = review_run_journal_env_key("ENV_BACKEND")
REVIEW_ENV_BRANCH = review_run_journal_env_key("ENV_BRANCH")
REVIEW_ENV_TARGET_KIND = review_run_journal_env_key("ENV_TARGET_KIND")
REVIEW_ENV_PULL_REQUEST_NUMBER = review_run_journal_env_key(
    "ENV_PULL_REQUEST_NUMBER",
)
REVIEW_START_RUN_TOKEN = cast(
    "str", review_run_contract_value("START_RESULT_RUN_TOKEN")
)
REVIEW_START_STATE_PATH = cast(
    "str", review_run_contract_value("START_RESULT_STATE_PATH")
)
REVIEW_START_DIFF_PATH = cast(
    "str", review_run_contract_value("START_RESULT_DIFF_PATH")
)
REVIEW_START_MANIFEST_PATH = cast(
    "str", review_run_contract_value("START_RESULT_MANIFEST_PATH")
)
REVIEW_START_CHANGED_FILES = cast(
    "str", review_run_contract_value("START_RESULT_CHANGED_FILES")
)
REVIEW_START_FIELDS = cast(
    "tuple[str, ...]", review_run_contract_value("START_RESULT_FIELDS")
)
REVIEW_SUMMARY_FIELD = cast("str", review_run_contract_value("REVIEW_SUMMARY_FIELD"))
REVIEW_SUMMARY_BLOCKING_FIELD = cast(
    "str", review_run_contract_value("REVIEW_SUMMARY_BLOCKING_FIELD")
)
REVIEW_SUMMARY_DEBT_FIELD = cast(
    "str", review_run_contract_value("REVIEW_SUMMARY_DEBT_FIELD")
)
REVIEW_SUMMARY_OVERALL_FIELD = cast(
    "str", review_run_contract_value("REVIEW_SUMMARY_OVERALL_FIELD")
)
REVIEW_JOURNAL_COMMAND = cast(
    "tuple[str, ...]", review_run_contract_value("JOURNAL_COMMAND")
)
REVIEW_JOURNAL_TYPE = cast("str", review_run_contract_value("REVIEW_JOURNAL_TYPE"))
REVIEW_JOURNAL_START_CURSOR = cast(
    "str", review_run_contract_value("JOURNAL_START_CURSOR")
)
REVIEW_SCRIPT_FILENAMES = cast(
    "tuple[str, ...]", review_run_contract_value("REVIEW_SCRIPT_FILENAMES")
)
EXPECTED_REVIEW_JOURNAL_COMMAND = ("spx", "journal")
EXPECTED_REVIEW_JOURNAL_TYPE = "review"
EXPECTED_REVIEW_JOURNAL_START_CURSOR = "0"


def run_git(*args: str, cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    """Run git with isolated identity and signing configuration."""

    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    return subprocess.run(  # noqa: S603
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def init_review_git_repo(repo: pathlib.Path) -> str:
    """Create a feature branch carrying one committed review diff."""

    run_git("init", "-q", "-b", "main", str(repo), cwd=pathlib.Path.cwd())
    run_git("config", "commit.gpgsign", "false", cwd=repo)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    run_git("add", "README.md", cwd=repo)
    run_git("commit", "-q", "-m", "initial", cwd=repo)
    run_git("switch", "-c", "feature/x", cwd=repo)
    (repo / "README.md").write_text("hello\nworld\n", encoding="utf-8")
    run_git("add", "README.md", cwd=repo)
    run_git("commit", "-q", "-m", "add world", cwd=repo)
    return "main"


def init_renamed_review_git_repo(repo: pathlib.Path) -> str:
    """Create a feature branch carrying one committed rename."""

    run_git("init", "-q", "-b", "main", str(repo), cwd=pathlib.Path.cwd())
    run_git("config", "commit.gpgsign", "false", cwd=repo)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    run_git("add", "README.md", cwd=repo)
    run_git("commit", "-q", "-m", "initial", cwd=repo)
    run_git("switch", "-c", "feature/x", cwd=repo)
    run_git("mv", "README.md", "RENAMED.md", cwd=repo)
    run_git("commit", "-q", "-m", "rename readme", cwd=repo)
    return "main"


def isolated_review_env(cwd: pathlib.Path) -> dict[str, str]:
    """Return an isolated environment for review git subprocesses."""

    env = {
        **os.environ,
        "PWD": str(cwd),
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    }
    for key in (
        *review_run_journal_env_keys(),
        "GITHUB_ACTIONS",
        "GITHUB_BASE_REF",
        "GITHUB_EVENT_NAME",
        "GITHUB_EVENT_PATH",
        "GITHUB_HEAD_REF",
        "GITHUB_REF",
        "GITHUB_REF_NAME",
        "GITHUB_REPOSITORY",
    ):
        env.pop(key, None)
    env[REVIEW_ENV_BACKEND] = "local"
    return env


def stream_review_prefix(
    env: dict[str, str],
    metadata_json: str,
    findings: list[dict[str, object]],
    *,
    units: list[str],
) -> list[dict[str, object]]:
    """Drive the streaming review chain and return its sealed event prefix."""

    events: list[dict[str, object]] = []
    scope_entered = run_journal_emit_in_process(
        "scope-entered",
        "--now",
        REVIEW_EVENT_TIME,
        "--metadata",
        metadata_json,
        env=env,
    )
    if scope_entered.returncode != 0:
        raise AssertionError(scope_entered.stderr)
    events.append(json.loads(scope_entered.stdout))
    for unit in units:
        advanced = run_journal_emit_in_process(
            "scope-advanced",
            "--now",
            REVIEW_EVENT_TIME,
            "--unit",
            unit,
            env=env,
        )
        if advanced.returncode != 0:
            raise AssertionError(advanced.stderr)
        events.append(json.loads(advanced.stdout))
    for finding in findings:
        reported = run_journal_emit_in_process(
            "finding-reported",
            "--now",
            REVIEW_EVENT_TIME,
            stdin=json.dumps(finding),
            env=env,
        )
        if reported.returncode != 0:
            raise AssertionError(reported.stderr)
        events.append(json.loads(reported.stdout))
    completed = run_journal_emit_in_process(
        "run-completed",
        "--now",
        REVIEW_EVENT_TIME,
        "--completed-at",
        REVIEW_COMPLETION_TIME,
        "--metadata",
        metadata_json,
        stdin=json.dumps(events),
        env=env,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    events.append(json.loads(completed.stdout))
    return events


def set_origin_head(repo: pathlib.Path, branch: str) -> None:
    """Point the synthetic origin HEAD at an existing local branch."""

    run_git(
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        f"refs/remotes/origin/{branch}",
        cwd=repo,
    )
    revision = run_git("rev-parse", branch, cwd=repo).stdout.strip()
    run_git("update-ref", f"refs/remotes/origin/{branch}", revision, cwd=repo)


def add_secondary_review_branch(
    repo: pathlib.Path,
    branch: str,
    filename: str,
) -> None:
    """Create a secondary branch with one distinct committed file."""

    run_git("switch", "main", cwd=repo)
    run_git("switch", "-c", branch, cwd=repo)
    (repo / filename).write_text("secondary branch content\n", encoding="utf-8")
    run_git("add", filename, cwd=repo)
    run_git("commit", "-q", "-m", f"add {filename} on {branch}", cwd=repo)
    run_git("switch", "feature/x", cwd=repo)


def _module_main(module: ModuleType) -> Callable[[list[str] | None], int]:
    return cast("Callable[[list[str] | None], int]", module.main)


def run_compute_diff_in_process(
    *,
    repo: pathlib.Path,
    env: dict[str, str],
    args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``compute_diff.main`` in-process with CLI-shaped outputs.

    The script path is still loaded from authored plugin source and the same
    ``main([])`` entry point runs. Running in-process lets coverage observe the
    script's lines while preserving a ``CompletedProcess`` result shape for
    scenario tests.
    """

    module = load_compute_diff_module()
    stdout = io.StringIO()
    stderr = io.StringIO()
    old_cwd = pathlib.Path.cwd()
    script_args = args or []
    argv = [sys.executable, str(COMPUTE_DIFF_SCRIPT), *script_args]
    try:
        os.chdir(repo)
        with (
            configured_environment(env, clear=True),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            returncode = _module_main(module)(script_args)
    finally:
        os.chdir(old_cwd)
    return subprocess.CompletedProcess(
        argv,
        returncode,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )


def _computed_review_bundle(
    *,
    repo: pathlib.Path,
    root: pathlib.Path,
    env: dict[str, str],
    name: str,
) -> tuple[pathlib.Path, dict[str, object]]:
    """Produce and parse one real review-input bundle."""

    bundle_dir = root / name
    result = run_compute_diff_in_process(
        repo=repo,
        env=env,
        args=["--bundle-dir", str(bundle_dir)],
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    summary = json.loads(result.stdout)
    manifest_path = pathlib.Path(summary["manifest_path"])
    scope = load_journal_emit_module()._review_scope_from_manifest(manifest_path)
    return manifest_path, cast("dict[str, object]", scope)


def computed_review_scopes() -> dict[str, dict[str, object]]:
    """Return source-produced scopes with changed input and changed file variants."""

    with TemporaryDirectory() as temporary_directory:
        root = pathlib.Path(temporary_directory)
        repo = root / "repo"
        repo.mkdir()
        base_ref = init_review_git_repo(repo)
        set_origin_head(repo, base_ref)
        env = isolated_review_env(cwd=repo)
        env[REVIEW_ENV_BASE_REF] = f"origin/{base_ref}"
        env[load_journal_emit_module().ENV_HEAD_REF] = (
            load_journal_emit_module().DEFAULT_HEAD_REF
        )

        _manifest, primary = _computed_review_bundle(
            repo=repo,
            root=root,
            env=env,
            name="primary",
        )
        (repo / "README.md").write_text(
            "hello\nworld\nadditional review input\n",
            encoding="utf-8",
        )
        _manifest, changed_input = _computed_review_bundle(
            repo=repo,
            root=root,
            env=env,
            name="changed-input",
        )
        (repo / "ADDITIONAL.md").write_text(
            "additional changed file\n",
            encoding="utf-8",
        )
        _manifest, expanded_files = _computed_review_bundle(
            repo=repo,
            root=root,
            env=env,
            name="expanded-files",
        )
        return {
            "primary": primary,
            "changed-input": changed_input,
            "expanded-files": expanded_files,
        }


def run_journal_emit_in_process(
    *args: str,
    stdin: str | None = None,
    repo: pathlib.Path | None = None,
    env: dict[str, str] | None = None,
    metadata_deps: Any | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``journal_emit.main`` in-process with CLI-shaped outputs."""

    module = load_journal_emit_module()
    stdout = io.StringIO()
    stderr = io.StringIO()
    input_stream = io.StringIO(stdin or "")
    old_cwd = pathlib.Path.cwd()
    argv = [sys.executable, str(JOURNAL_EMIT_SCRIPT), *args]
    try:
        if repo is not None:
            os.chdir(repo)
        with (
            configured_stdin(input_stream),
            configured_environment(env or os.environ.copy(), clear=True),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            if metadata_deps is None:
                returncode = _module_main(module)(list(args))
            else:
                entrypoint = cast("Callable[..., int]", module.main)
                returncode = entrypoint(
                    list(args),
                    metadata_deps=metadata_deps,
                )
    finally:
        os.chdir(old_cwd)
    return subprocess.CompletedProcess(
        argv,
        returncode,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )


def run_script(
    script: pathlib.Path,
    *args: str,
    stdin: str | None = None,
    check: bool = False,
    env: dict[str, str] | None = None,
    cwd: pathlib.Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke a script as a subprocess and return the result.

    Captures stdout/stderr in text mode with optional stdin payload and
    optional explicit environment. ``check=False`` is the default so tests can
    inspect returncode explicitly; success-path tests pass ``check=True``.
    """
    return subprocess.run(  # noqa: S603 — script path comes from the harness, not user input
        [sys.executable, str(script), *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=check,
        env=env,
        cwd=cwd,
    )


def run_review_journal(
    runner: ReviewRunnerHarness,
    *args: str,
    env: dict[str, str] | None = None,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the real source-declared journal command in the isolated repository."""

    return subprocess.run(  # noqa: S603
        [*REVIEW_JOURNAL_COMMAND, *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        env=env or runner.env,
        cwd=runner.repo,
    )


def read_review_journal(
    runner: ReviewRunnerHarness,
    run_token: str,
) -> tuple[dict[str, Any], ...]:
    """Read one real journal run and validate its event-array response."""

    result = run_review_journal(
        runner,
        "read",
        "--type",
        REVIEW_JOURNAL_TYPE,
        "--run",
        run_token,
        "--from",
        REVIEW_JOURNAL_START_CURSOR,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    payload = json.loads(result.stdout)
    if not isinstance(payload, list) or not all(
        isinstance(event, dict) for event in payload
    ):
        raise AssertionError(f"spx journal read returned invalid events: {payload!r}")
    return tuple(cast("dict[str, Any]", event) for event in payload)


@dataclass(frozen=True)
class ReviewRunnerHarness:
    """Temporary repository and environments for one real journal scenario."""

    repo: pathlib.Path
    env: dict[str, str]
    later_env: dict[str, str]


@dataclass(frozen=True)
class ReviewChainObservation:
    """Outputs captured from one complete streaming review chain."""

    diff_result: subprocess.CompletedProcess[str]
    metadata_result: subprocess.CompletedProcess[str]
    changed_file: str
    findings: tuple[dict[str, Any], ...]
    events: tuple[dict[str, Any], ...]
    rendered: dict[str, str]


def _review_chain_observation(
    findings: tuple[dict[str, Any], ...],
) -> ReviewChainObservation:
    """Run the complete review adapter chain in an isolated git repository."""

    with TemporaryDirectory() as temporary_directory:
        repo = pathlib.Path(temporary_directory) / "repo"
        repo.mkdir()
        base_ref = init_review_git_repo(repo)
        env = isolated_review_env(cwd=repo)
        env[REVIEW_ENV_BASE_REF] = base_ref
        diff_result = run_compute_diff_in_process(repo=repo, env=env)
        metadata_result = run_journal_emit_in_process(
            "metadata",
            "--started-at",
            review_run_metadata().started_at,
            repo=repo,
            env=env,
        )
        changed_file = next(
            file_path
            for value in review_run_metadata().scope.values()
            if isinstance(value, list)
            for file_path in value
            if isinstance(file_path, str)
        )
        events = stream_review_prefix(
            env,
            metadata_result.stdout,
            list(findings),
            units=[changed_file],
        )
        rendered_result = run_journal_emit_in_process(
            "render",
            stdin=json.dumps(events),
            env=env,
        )
        return ReviewChainObservation(
            diff_result=diff_result,
            metadata_result=metadata_result,
            changed_file=changed_file,
            findings=findings,
            events=tuple(events),
            rendered=cast("dict[str, str]", json.loads(rendered_result.stdout)),
        )


def review_chain_with_finding_observation() -> ReviewChainObservation:
    """Capture one complete review carrying the source-constructed finding."""

    return _review_chain_observation((make_finding_dict(),))


def clean_review_chain_observation() -> ReviewChainObservation:
    """Capture one complete review carrying no findings."""

    return _review_chain_observation(())


@dataclass(frozen=True)
class MalformedRunnerFindingObservation:
    """Runner output and journal state after one malformed finding append."""

    returncode: int
    stderr: str
    missing_field: str
    event_types: tuple[str, ...]


def malformed_runner_finding_observation() -> MalformedRunnerFindingObservation:
    """Attempt one malformed append against an isolated runner journal."""

    review_result = load_review_result_module()
    with TemporaryDirectory() as temporary_directory:
        runner = review_runner_harness(pathlib.Path(temporary_directory))
        started = run_script(
            REVIEW_RUN_SCRIPT,
            "start",
            env=runner.env,
            cwd=runner.repo,
        )
        start_payload = json.loads(started.stdout)
        missing_field = review_result.FINDING_ACTION_FIELD
        malformed = make_finding_dict()
        del malformed[missing_field]
        appended = run_script(
            REVIEW_RUN_SCRIPT,
            "append-finding",
            "--state",
            start_payload[REVIEW_START_STATE_PATH],
            stdin=json.dumps(malformed),
            env=runner.env,
            cwd=runner.repo,
        )
        journal = read_review_journal(
            runner,
            start_payload[REVIEW_START_RUN_TOKEN],
        )
        event_types = tuple(event["type"] for event in journal)
        return MalformedRunnerFindingObservation(
            returncode=appended.returncode,
            stderr=appended.stderr,
            missing_field=missing_field,
            event_types=event_types,
        )


@dataclass(frozen=True)
class ReviewRunnerLifecycleObservation:
    """One complete runner lifecycle compared with production contracts."""

    start_contract_holds: bool
    namespace_is_preserved: bool
    finish_returns_raw_token: bool
    scratch_state_is_removed: bool
    journal_protocol_holds: bool
    finding_identity_is_preserved: bool
    terminal_rollup_holds: bool


def review_runner_lifecycle_observation() -> ReviewRunnerLifecycleObservation:
    """Run start, scope, findings, and finish through the public runner."""

    projection = review_contract_modules().journal_projection
    review_result = load_review_result_module()
    with TemporaryDirectory() as temporary_directory:
        runner = review_runner_harness(pathlib.Path(temporary_directory))
        started = run_script(
            REVIEW_RUN_SCRIPT,
            "start",
            env=runner.env,
            cwd=runner.repo,
        )
        start_payload = json.loads(started.stdout)
        state_path = pathlib.Path(start_payload[REVIEW_START_STATE_PATH])
        start_paths_exist = (
            pathlib.Path(start_payload[REVIEW_START_DIFF_PATH]).is_file()
            and pathlib.Path(start_payload[REVIEW_START_MANIFEST_PATH]).is_file()
        )
        scoped = run_script(
            REVIEW_RUN_SCRIPT,
            "append-scope",
            "--state",
            str(state_path),
            start_payload[REVIEW_START_CHANGED_FILES][0],
            env=runner.later_env,
            cwd=runner.repo,
        )
        findings = review_finding_payloads()
        appended = tuple(
            run_script(
                REVIEW_RUN_SCRIPT,
                "append-finding",
                "--state",
                str(state_path),
                stdin=json.dumps(finding),
                env=runner.later_env,
                cwd=runner.repo,
            )
            for finding in findings
        )
        finished = run_script(
            REVIEW_RUN_SCRIPT,
            "finish",
            "--state",
            str(state_path),
            env=runner.later_env,
            cwd=runner.repo,
        )
        state_removed = not state_path.exists()
        run_token = start_payload[REVIEW_START_RUN_TOKEN]
        journal = read_review_journal(runner, run_token)
        append_after_seal = run_review_journal(
            runner,
            "append",
            "--type",
            REVIEW_JOURNAL_TYPE,
            "--run",
            run_token,
            stdin=json.dumps(journal[-1]),
        )

    expected_event_types = (
        projection.SCOPE_ENTERED,
        projection.SCOPE_ADVANCED,
        *(projection.FINDING_REPORTED for _finding in findings),
        projection.RUN_COMPLETED,
    )
    event_types = tuple(event["type"] for event in journal)
    finding_events = tuple(
        event for event in journal if event["type"] == projection.FINDING_REPORTED
    )
    terminal_event = journal[-1]
    summary = terminal_event["data"][REVIEW_SUMMARY_FIELD]
    return ReviewRunnerLifecycleObservation(
        start_contract_holds=(
            started.returncode == 0
            and set(start_payload) == set(REVIEW_START_FIELDS)
            and start_paths_exist
            and isinstance(start_payload[REVIEW_START_CHANGED_FILES], list)
        ),
        namespace_is_preserved=(
            scoped.returncode == 0
            and all(result.returncode == 0 for result in appended)
            and finished.returncode == 0
        ),
        finish_returns_raw_token=(
            scoped.returncode == 0
            and all(result.returncode == 0 for result in appended)
            and finished.returncode == 0
            and finished.stdout == f"{start_payload[REVIEW_START_RUN_TOKEN]}\n"
        ),
        scratch_state_is_removed=state_removed,
        journal_protocol_holds=(
            append_after_seal.returncode != 0 and event_types == expected_event_types
        ),
        finding_identity_is_preserved=(
            [event["data"]["id"] for event in finding_events]
            == [finding["id"] for finding in findings]
        ),
        terminal_rollup_holds=(
            terminal_event["data"]["status"] == projection.JournalRunStatus.REJECTED
            and summary[REVIEW_SUMMARY_BLOCKING_FIELD]
            == sum(
                finding["severity"] == review_result.Severity.BLOCKING
                for finding in findings
            )
            and summary[REVIEW_SUMMARY_DEBT_FIELD]
            == sum(
                finding["severity"] == review_result.Severity.DEBT
                for finding in findings
            )
            and summary[REVIEW_SUMMARY_OVERALL_FIELD] == projection.Outcome.REJECTED
        ),
    )


@dataclass(frozen=True)
class ReviewRunnerCoverageObservation:
    """Runner refusal to seal an incompletely examined changeset."""

    finish_is_rejected: bool
    missing_scope_is_named: bool
    only_scope_entered_is_recorded: bool
    journal_remains_open: bool


def review_runner_coverage_observation() -> ReviewRunnerCoverageObservation:
    """Attempt to finish a run before appending its changed-file scope."""

    projection = review_contract_modules().journal_projection
    with TemporaryDirectory() as temporary_directory:
        runner = review_runner_harness(pathlib.Path(temporary_directory))
        started = run_script(
            REVIEW_RUN_SCRIPT,
            "start",
            env=runner.env,
            cwd=runner.repo,
        )
        start_payload = json.loads(started.stdout)
        missing_file = start_payload[REVIEW_START_CHANGED_FILES][0]
        finished = run_script(
            REVIEW_RUN_SCRIPT,
            "finish",
            "--state",
            start_payload[REVIEW_START_STATE_PATH],
            env=runner.env,
            cwd=runner.repo,
        )
        run_token = start_payload[REVIEW_START_RUN_TOKEN]
        journal = read_review_journal(runner, run_token)
        append_while_open = run_review_journal(
            runner,
            "append",
            "--type",
            REVIEW_JOURNAL_TYPE,
            "--run",
            run_token,
            stdin=json.dumps(
                projection.scope_advanced_event(
                    missing_file,
                    now=REVIEW_EVENT_TIME,
                    attempt=1,
                )
            ),
        )
    return ReviewRunnerCoverageObservation(
        finish_is_rejected=finished.returncode != 0,
        missing_scope_is_named=missing_file in finished.stderr,
        only_scope_entered_is_recorded=(
            tuple(event["type"] for event in journal) == (projection.SCOPE_ENTERED,)
        ),
        journal_remains_open=append_while_open.returncode == 0,
    )


@dataclass(frozen=True)
class ReviewRunnerRenameObservation:
    """Rename source and destination coverage at the runner boundary."""

    both_paths_are_required: bool
    destination_alone_is_rejected: bool
    source_is_named_as_missing: bool
    both_paths_allow_finish: bool


def review_runner_rename_observation() -> ReviewRunnerRenameObservation:
    """Exercise rename coverage through the public runner commands."""

    with TemporaryDirectory() as temporary_directory:
        runner = review_runner_harness(
            pathlib.Path(temporary_directory),
            renamed=True,
        )
        started = run_script(
            REVIEW_RUN_SCRIPT,
            "start",
            env=runner.env,
            cwd=runner.repo,
        )
        start_payload = json.loads(started.stdout)
        source, destination = start_payload[REVIEW_START_CHANGED_FILES]
        destination_scoped = run_script(
            REVIEW_RUN_SCRIPT,
            "append-scope",
            "--state",
            start_payload[REVIEW_START_STATE_PATH],
            destination,
            env=runner.env,
            cwd=runner.repo,
        )
        missing_source = run_script(
            REVIEW_RUN_SCRIPT,
            "finish",
            "--state",
            start_payload[REVIEW_START_STATE_PATH],
            env=runner.env,
            cwd=runner.repo,
        )
        source_scoped = run_script(
            REVIEW_RUN_SCRIPT,
            "append-scope",
            "--state",
            start_payload[REVIEW_START_STATE_PATH],
            source,
            env=runner.env,
            cwd=runner.repo,
        )
        finished = run_script(
            REVIEW_RUN_SCRIPT,
            "finish",
            "--state",
            start_payload[REVIEW_START_STATE_PATH],
            env=runner.env,
            cwd=runner.repo,
        )
    return ReviewRunnerRenameObservation(
        both_paths_are_required=(source != destination),
        destination_alone_is_rejected=(
            destination_scoped.returncode == 0 and missing_source.returncode != 0
        ),
        source_is_named_as_missing=source in missing_source.stderr,
        both_paths_allow_finish=(
            source_scoped.returncode == 0
            and finished.returncode == 0
            and finished.stdout == f"{start_payload[REVIEW_START_RUN_TOKEN]}\n"
        ),
    )


@dataclass(frozen=True)
class ComputeDiffScenarioObservation:
    """All source-declared ref and bundle scenarios for compute-diff."""

    explicit_base_selects_committed_diff: bool
    all_worktree_sections_are_included: bool
    bundle_paths_match_contract: bool
    bundle_summary_matches_content: bool
    bundle_manifest_identity_matches_source: bool
    bundle_section_ranges_match_content: bool
    invalid_bundle_destinations_are_rejected: bool
    origin_head_supplies_default_base: bool
    missing_base_sources_are_named: bool
    explicit_head_selects_alternate_diff: bool
    literal_head_is_the_default: bool
    stale_local_base_does_not_widen_diff: bool


def compute_diff_scenario_observation() -> ComputeDiffScenarioObservation:
    """Exercise compute-diff scenarios in isolated real Git repositories."""

    from outcomeeng_testing.harnesses.changeset_scope import (
        build_stale_local_base_repo,
    )

    compute_diff = load_compute_diff_module()
    with TemporaryDirectory() as temporary_directory:
        root = pathlib.Path(temporary_directory)

        explicit_repo = root / "explicit"
        explicit_repo.mkdir()
        explicit_base = init_review_git_repo(explicit_repo)
        explicit_env = isolated_review_env(cwd=explicit_repo)
        explicit_env[compute_diff.ENV_BASE_REF] = explicit_base
        explicit = run_compute_diff_in_process(repo=explicit_repo, env=explicit_env)

        worktree_repo = root / "worktree"
        worktree_repo.mkdir()
        worktree_base = init_review_git_repo(worktree_repo)
        worktree_env = isolated_review_env(cwd=worktree_repo)
        worktree_env[compute_diff.ENV_BASE_REF] = worktree_base
        (worktree_repo / "STAGED.md").write_text("staged\n", encoding="utf-8")
        run_git("add", "STAGED.md", cwd=worktree_repo)
        (worktree_repo / "README.md").write_text(
            "hello\nworld\nunstaged\n",
            encoding="utf-8",
        )
        (worktree_repo / "UNTRACKED.md").write_text(
            "untracked\n",
            encoding="utf-8",
        )
        worktree = run_compute_diff_in_process(
            repo=worktree_repo,
            env=worktree_env,
        )
        bundle_dir = root / "review-input"
        bundle = run_compute_diff_in_process(
            repo=worktree_repo,
            env=worktree_env,
            args=["--bundle-dir", str(bundle_dir)],
        )
        bundle_summary = json.loads(bundle.stdout)
        diff_path = pathlib.Path(bundle_summary["diff_path"])
        manifest_path = pathlib.Path(bundle_summary["manifest_path"])
        diff_text = diff_path.read_text(encoding="utf-8")
        diff_bytes = diff_text.encode("utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_titles = (
            compute_diff.DIFF_SECTION_COMMITTED,
            compute_diff.DIFF_SECTION_STAGED,
            compute_diff.DIFF_SECTION_UNSTAGED,
            compute_diff.DIFF_SECTION_UNTRACKED,
        )
        section_ranges_match = all(
            diff_bytes[
                section["byte_start"] : section["byte_start"] + section["byte_length"]
            ]
            .decode("utf-8")
            .startswith(f"### {section['title']}")
            and section["start_line"]
            == diff_bytes[: section["byte_start"]].decode("utf-8").count("\n") + 1
            for section in manifest["sections"]
        )

        bundle_file = root / "bundle-file"
        bundle_file.write_text("not a directory\n", encoding="utf-8")
        file_rejection = run_compute_diff_in_process(
            repo=worktree_repo,
            env=worktree_env,
            args=["--bundle-dir", str(bundle_file)],
        )
        inside_path = worktree_repo / ".review-input"
        inside_rejection = run_compute_diff_in_process(
            repo=worktree_repo,
            env=worktree_env,
            args=["--bundle-dir", str(inside_path)],
        )

        origin_repo = root / "origin-head"
        origin_repo.mkdir()
        origin_base = init_review_git_repo(origin_repo)
        set_origin_head(origin_repo, origin_base)
        origin_env = isolated_review_env(cwd=origin_repo)
        origin_env.pop(compute_diff.ENV_BASE_REF, None)
        origin_head = run_compute_diff_in_process(repo=origin_repo, env=origin_env)

        missing_repo = root / "missing-base"
        missing_repo.mkdir()
        init_review_git_repo(missing_repo)
        missing_env = isolated_review_env(cwd=missing_repo)
        missing_env.pop(compute_diff.ENV_BASE_REF, None)
        missing_base = run_compute_diff_in_process(
            repo=missing_repo,
            env=missing_env,
        )

        alternate_repo = root / "alternate-head"
        alternate_repo.mkdir()
        alternate_base = init_review_git_repo(alternate_repo)
        alternate_head = "feature/y"
        add_secondary_review_branch(
            alternate_repo,
            alternate_head,
            "SECONDARY.md",
        )
        alternate_env = isolated_review_env(cwd=alternate_repo)
        alternate_env[compute_diff.ENV_BASE_REF] = alternate_base
        alternate_env[compute_diff.ENV_HEAD_REF] = alternate_head
        explicit_head = run_compute_diff_in_process(
            repo=alternate_repo,
            env=alternate_env,
        )
        alternate_env.pop(compute_diff.ENV_HEAD_REF)
        default_head = run_compute_diff_in_process(
            repo=alternate_repo,
            env=alternate_env,
        )

        stale_repo_path = root / "stale-base"
        stale_repo_path.mkdir()
        stale = build_stale_local_base_repo(stale_repo_path)
        stale_env = isolated_review_env(cwd=stale.repo)
        stale_env.pop(compute_diff.ENV_BASE_REF, None)
        stale_result = run_compute_diff_in_process(
            repo=stale.repo,
            env=stale_env,
        )

    worktree_sections = tuple(f"### {title}" for title in expected_titles)
    return ComputeDiffScenarioObservation(
        explicit_base_selects_committed_diff=(
            explicit.returncode == 0 and "README.md" in explicit.stdout
        ),
        all_worktree_sections_are_included=(
            worktree.returncode == 0
            and all(section in worktree.stdout for section in worktree_sections)
            and all(
                value in worktree.stdout
                for value in (
                    "world",
                    "STAGED.md",
                    "unstaged",
                    "UNTRACKED.md",
                    "untracked",
                )
            )
        ),
        bundle_paths_match_contract=(
            bundle.returncode == 0
            and diff_path
            == bundle_dir.resolve(strict=False) / compute_diff.BUNDLE_DIFF_FILENAME
            and manifest_path
            == bundle_dir.resolve(strict=False) / compute_diff.BUNDLE_MANIFEST_FILENAME
        ),
        bundle_summary_matches_content=(
            bundle_summary["diff_bytes"] == len(diff_bytes)
            and bundle_summary["section_count"] == len(expected_titles)
        ),
        bundle_manifest_identity_matches_source=(
            manifest["schema_version"] == compute_diff.MANIFEST_SCHEMA_VERSION
            and manifest["base_ref"] == worktree_base
            and manifest["head_ref"] == compute_diff.DEFAULT_HEAD_REF
            and tuple(section["title"] for section in manifest["sections"])
            == expected_titles
        ),
        bundle_section_ranges_match_content=section_ranges_match,
        invalid_bundle_destinations_are_rejected=(
            file_rejection.returncode != 0
            and "--bundle-dir exists and is not a directory" in file_rejection.stderr
            and inside_rejection.returncode != 0
            and "--bundle-dir must be outside the git worktree"
            in inside_rejection.stderr
            and not inside_path.exists()
        ),
        origin_head_supplies_default_base=(
            origin_head.returncode == 0 and "README.md" in origin_head.stdout
        ),
        missing_base_sources_are_named=(
            missing_base.returncode != 0
            and compute_diff.ENV_BASE_REF in missing_base.stderr
            and "origin/HEAD" in missing_base.stderr
        ),
        explicit_head_selects_alternate_diff=(
            explicit_head.returncode == 0
            and "SECONDARY.md" in explicit_head.stdout
            and "world" not in explicit_head.stdout
        ),
        literal_head_is_the_default=(
            default_head.returncode == 0
            and "world" in default_head.stdout
            and "SECONDARY.md" not in default_head.stdout
        ),
        stale_local_base_does_not_widen_diff=(
            stale_result.returncode == 0
            and stale.feature_file in stale_result.stdout
            and stale.merged_file not in stale_result.stdout
        ),
    )


@dataclass(frozen=True)
class ReviewConfigDigestObservation:
    """Config identity behavior observed through production digest functions."""

    prompt_change_changes_digest: bool
    runner_and_adapter_share_digest: bool
    root_policy_change_preserves_digest: bool
    metadata_ignores_root_policy: bool


def review_config_digest_observation() -> ReviewConfigDigestObservation:
    """Exercise prompt-owned config identity outside the canonical test file."""

    journal_emit = load_journal_emit_module()
    projection = review_contract_modules().journal_projection
    with TemporaryDirectory() as temporary_directory:
        root = pathlib.Path(temporary_directory)
        first = root / "first"
        second = root / "second"
        write_review_skill_config(first, prompt="review prompt one")
        write_review_skill_config(second, prompt="review prompt two")
        prompt_change_changes_digest = journal_emit.review_config_digest(
            first
        ) != journal_emit.review_config_digest(second)

        stable_skill = root / "stable-skill"
        write_review_skill_config(stable_skill, prompt="stable review prompt")
        review_policy = root / "REVIEW.md"
        review_policy.write_text("first policy body", encoding="utf-8")
        first_digest = journal_emit.review_config_digest(stable_skill)
        review_policy.write_text("second policy body", encoding="utf-8")
        root_policy_change_preserves_digest = (
            first_digest == journal_emit.review_config_digest(stable_skill)
        )

        nested = root / "nested"
        nested.mkdir()
        old_cwd = pathlib.Path.cwd()
        try:
            os.chdir(nested)
            harness = ReviewMetadataHarness()
            metadata = journal_emit.metadata_for_worktree(
                started_at=harness.metadata.started_at,
                completed_at=harness.metadata.completed_at,
                deps=harness.deps(),
            )
        finally:
            os.chdir(old_cwd)

    return ReviewConfigDigestObservation(
        prompt_change_changes_digest=prompt_change_changes_digest,
        runner_and_adapter_share_digest=len(set(review_config_digests())) == 1,
        root_policy_change_preserves_digest=root_policy_change_preserves_digest,
        metadata_ignores_root_policy=(
            metadata[projection.RUN_STATE_CONFIG_DIGEST]
            == harness.metadata.config_digest
        ),
    )


@dataclass(frozen=True)
class ReviewMetadataObservation:
    """Metadata behavior observed through source-produced review bundles."""

    changed_file_set_changes_scope_hash: bool
    manifest_scope_matches_source_bundle: bool
    pull_request_identity_matches_environment: bool
    detached_branch_identity_matches_environment: bool
    changed_review_input_changes_scope_hash: bool
    metadata_cli_emits_source_identity: bool
    git_failure_is_reported_without_traceback: bool


def review_metadata_observation() -> ReviewMetadataObservation:
    """Exercise metadata mappings with real compute-diff bundle inputs."""

    contracts = review_contract_modules()
    journal_emit = contracts.journal_emit
    projection = contracts.journal_projection
    harness = ReviewMetadataHarness()
    pull_request_source = review_run_metadata(pull_request=True)
    detached_head_ref = f"origin/{harness.metadata.branch_name}"
    primary = journal_emit.metadata_for_worktree(
        started_at=harness.metadata.started_at,
        completed_at=harness.metadata.completed_at,
        deps=harness.deps(review_scope_variant="primary"),
    )
    changed_input = journal_emit.metadata_for_worktree(
        started_at=harness.metadata.started_at,
        completed_at=harness.metadata.completed_at,
        deps=harness.deps(review_scope_variant="changed-input"),
    )
    expanded_files = journal_emit.metadata_for_worktree(
        started_at=harness.metadata.started_at,
        completed_at=harness.metadata.completed_at,
        deps=harness.deps(review_scope_variant="expanded-files"),
    )

    with TemporaryDirectory() as temporary_directory:
        root = pathlib.Path(temporary_directory)
        repo = root / "repo"
        repo.mkdir()
        base_ref = init_review_git_repo(repo)
        set_origin_head(repo, base_ref)
        env = isolated_review_env(cwd=repo)
        env[REVIEW_ENV_BASE_REF] = f"origin/{base_ref}"
        manifest_path, source_scope = _computed_review_bundle(
            repo=repo,
            root=root,
            env=env,
            name="metadata-bundle",
        )
        manifest_metadata = journal_emit.metadata_for_worktree(
            started_at=harness.metadata.started_at,
            completed_at=harness.metadata.completed_at,
            review_manifest_path=manifest_path,
            deps=harness.deps(manifest_scope=True),
        )

        pull_request_env = {
            journal_emit.ENV_TARGET_KIND: str(
                projection.JournalTargetKind.PULL_REQUEST
            ),
            journal_emit.ENV_PULL_REQUEST_NUMBER: str(
                pull_request_source.pull_request_number
            ),
        }
        with configured_environment(pull_request_env, clear=False):
            pull_request_metadata = journal_emit.metadata_for_worktree(
                started_at=harness.metadata.started_at,
                completed_at=harness.metadata.completed_at,
                deps=harness.deps(source_target=True),
            )

        detached_env = {
            journal_emit.ENV_BASE_REF: harness.metadata.base_ref,
            journal_emit.ENV_HEAD_REF: detached_head_ref,
            journal_emit.ENV_BRANCH: harness.metadata.branch_name,
            **pull_request_env,
        }
        with configured_environment(detached_env, clear=False):
            detached_metadata = journal_emit.metadata_for_worktree(
                started_at=harness.metadata.started_at,
                completed_at=harness.metadata.completed_at,
                deps=harness.deps(source_branch=True, source_target=True),
            )

        cli_result = run_journal_emit_in_process(
            "metadata",
            "--started-at",
            harness.metadata.started_at,
            "--completed-at",
            harness.metadata.completed_at,
            "--manifest",
            str(manifest_path),
            repo=repo,
            env={
                journal_emit.ENV_BASE_REF: harness.metadata.base_ref,
                journal_emit.ENV_HEAD_REF: journal_emit.DEFAULT_HEAD_REF,
                journal_emit.ENV_BRANCH: harness.metadata.branch_name,
            },
            metadata_deps=harness.deps(source_branch=True, manifest_scope=True),
        )
        cli_metadata = json.loads(cli_result.stdout)

    failure = run_journal_emit_in_process(
        "metadata",
        "--started-at",
        harness.metadata.started_at,
        "--completed-at",
        harness.metadata.completed_at,
        metadata_deps=ReviewMetadataHarness(base_ref="origin/nope").deps(
            fail_scope=True
        ),
    )
    primary_scope = cast("dict[str, object]", primary[projection.RUN_STATE_SCOPE])
    changed_input_scope = cast(
        "dict[str, object]", changed_input[projection.RUN_STATE_SCOPE]
    )
    expanded_scope = cast(
        "dict[str, object]", expanded_files[projection.RUN_STATE_SCOPE]
    )
    return ReviewMetadataObservation(
        changed_file_set_changes_scope_hash=(
            primary_scope[journal_emit.SCOPE_CHANGED_FILES_FIELD]
            != expanded_scope[journal_emit.SCOPE_CHANGED_FILES_FIELD]
            and primary[projection.RUN_STATE_SCOPE_HASH]
            != expanded_files[projection.RUN_STATE_SCOPE_HASH]
        ),
        manifest_scope_matches_source_bundle=(
            manifest_metadata[projection.RUN_STATE_SCOPE] == source_scope
            and manifest_metadata[projection.RUN_STATE_BASE_REF]
            == source_scope[journal_emit.SCOPE_BASE_REF_FIELD]
        ),
        pull_request_identity_matches_environment=(
            pull_request_metadata[projection.RUN_STATE_TARGET_KIND]
            == projection.JournalTargetKind.PULL_REQUEST
            and pull_request_metadata[projection.RUN_STATE_PULL_REQUEST_NUMBER]
            == pull_request_source.pull_request_number
        ),
        detached_branch_identity_matches_environment=(
            detached_metadata[projection.RUN_STATE_BRANCH_NAME]
            == harness.metadata.branch_name
            and detached_metadata[projection.RUN_STATE_BRANCH_SLUG]
            == journal_emit.changeset_scope.branch_slug(harness.metadata.branch_name)
        ),
        changed_review_input_changes_scope_hash=(
            primary_scope[journal_emit.SCOPE_CHANGED_FILES_FIELD]
            == changed_input_scope[journal_emit.SCOPE_CHANGED_FILES_FIELD]
            and primary_scope[journal_emit.SCOPE_REVIEW_INPUT_SHA256_FIELD]
            != changed_input_scope[journal_emit.SCOPE_REVIEW_INPUT_SHA256_FIELD]
            and primary[projection.RUN_STATE_SCOPE_HASH]
            != changed_input[projection.RUN_STATE_SCOPE_HASH]
        ),
        metadata_cli_emits_source_identity=(
            cli_result.returncode == 0
            and cli_metadata[projection.RUN_STATE_BRANCH_NAME]
            == harness.metadata.branch_name
            and cli_metadata[projection.RUN_STATE_HEAD_SHA] == harness.metadata.head_sha
            and cli_metadata[projection.RUN_STATE_BASE_SHA] == harness.metadata.base_sha
            and cli_metadata[projection.RUN_STATE_SCOPE] == source_scope
        ),
        git_failure_is_reported_without_traceback=(
            failure.returncode != 0
            and "returned non-zero exit status 128" in failure.stderr
            and "Traceback" not in failure.stderr
        ),
    )


@dataclass(frozen=True)
class ReviewEventCliObservation:
    """CLI event mappings captured through the adapter entrypoint."""

    scope_entered_matches_contract: bool
    scope_advanced_matches_contract: bool
    conforming_finding_maps_to_event: bool
    malformed_finding_emits_only_error: bool
    completed_event_rolls_up_prefix: bool


def review_event_cli_observation() -> ReviewEventCliObservation:
    """Exercise every journal event subcommand behind one harness entrypoint."""

    contracts = review_contract_modules()
    journal_emit = contracts.journal_emit
    projection = contracts.journal_projection
    review_result = contracts.review_result
    metadata_json = review_metadata_wire_json()
    metadata = json.loads(metadata_json)
    scope_entered = run_journal_emit_in_process(
        "scope-entered",
        "--now",
        REVIEW_EVENT_TIME,
        "--metadata",
        metadata_json,
    )
    scope_entered_event = json.loads(scope_entered.stdout)
    changed_file = next(
        file_path
        for value in metadata[projection.RUN_STATE_SCOPE].values()
        if isinstance(value, list)
        for file_path in value
        if isinstance(file_path, str)
    )
    scope_advanced = run_journal_emit_in_process(
        "scope-advanced",
        "--now",
        REVIEW_EVENT_TIME,
        "--unit",
        changed_file,
    )
    scope_advanced_event = json.loads(scope_advanced.stdout)
    conforming = run_journal_emit_in_process(
        "finding-reported",
        "--now",
        REVIEW_EVENT_TIME,
        stdin=json.dumps(make_finding_dict()),
    )
    conforming_event = json.loads(conforming.stdout)
    missing_field = review_result.FINDING_ACTION_FIELD
    malformed_finding = make_finding_dict()
    del malformed_finding[missing_field]
    malformed = run_journal_emit_in_process(
        "finding-reported",
        "--now",
        REVIEW_EVENT_TIME,
        stdin=json.dumps(malformed_finding),
    )
    blocking = run_journal_emit_in_process(
        "finding-reported",
        "--now",
        REVIEW_EVENT_TIME,
        stdin=json.dumps(make_finding_dict(severity=review_result.Severity.BLOCKING)),
    )
    completed = run_journal_emit_in_process(
        "run-completed",
        "--now",
        REVIEW_EVENT_TIME,
        "--completed-at",
        REVIEW_COMPLETION_TIME,
        "--metadata",
        metadata_json,
        stdin=json.dumps([scope_entered_event, json.loads(blocking.stdout)]),
    )
    completed_event = json.loads(completed.stdout)
    return ReviewEventCliObservation(
        scope_entered_matches_contract=(
            scope_entered.returncode == 0
            and scope_entered_event["type"] == projection.SCOPE_ENTERED
            and scope_entered_event["data"]["target"] == journal_emit.DEFAULT_TARGET
            and scope_entered_event["data"][projection.RUN_STATE_HEAD_SHA]
            == metadata[projection.RUN_STATE_HEAD_SHA]
        ),
        scope_advanced_matches_contract=(
            scope_advanced.returncode == 0
            and scope_advanced_event["type"] == projection.SCOPE_ADVANCED
            and scope_advanced_event["data"]["unit"] == changed_file
        ),
        conforming_finding_maps_to_event=(
            conforming.returncode == 0
            and conforming_event["type"] == projection.FINDING_REPORTED
        ),
        malformed_finding_emits_only_error=(
            malformed.returncode != 0
            and missing_field in malformed.stderr
            and malformed.stdout.strip() == ""
        ),
        completed_event_rolls_up_prefix=(
            completed.returncode == 0
            and completed_event["type"] == projection.RUN_COMPLETED
            and completed_event["data"][projection.RUN_STATE_STARTED_AT]
            == metadata[projection.RUN_STATE_STARTED_AT]
            and completed_event["data"][projection.RUN_STATE_COMPLETED_AT]
            == REVIEW_COMPLETION_TIME
            and completed_event["data"][projection.RUN_STATE_STATUS]
            == projection.JournalRunStatus.REJECTED
        ),
    )


def review_runner_harness(
    tmp_path: pathlib.Path, *, renamed: bool = False
) -> ReviewRunnerHarness:
    """Create an isolated Git repository for the real journal backend."""

    repo = tmp_path / "repo"
    repo.mkdir()
    base_ref = (
        init_renamed_review_git_repo(repo) if renamed else init_review_git_repo(repo)
    )
    env = isolated_review_env(cwd=repo)
    env[REVIEW_ENV_BASE_REF] = base_ref
    later_env = env.copy()
    for key in review_run_journal_env_keys():
        later_env[key] = CONTAMINATING_JOURNAL_ENV_VALUE

    return ReviewRunnerHarness(
        repo=repo,
        env=env,
        later_env=later_env,
    )


_FORBIDDEN_NAME_CALLS = {"open"}
_FORBIDDEN_ATTR_CALLS = {
    ("os", "remove"),
    ("os", "rename"),
    ("os", "replace"),
    ("os", "unlink"),
    ("shutil", "rmtree"),
}
_FORBIDDEN_METHOD_NAMES = {
    "mkdir",
    "rename",
    "replace",
    "rmdir",
    "touch",
    "unlink",
    "write_bytes",
    "write_text",
}
_COMPUTE_DIFF_ALLOWED_WRITE_CALLS = {
    ("safe_bundle_dir", "mkdir"),
    ("diff_path", "write_text"),
    ("manifest_path", "write_text"),
}
_REVIEW_RUN_ALLOWED_WRITE_CALLS = {
    ("path", "write_text"),
    ("shutil", "rmtree"),
}
_WRITE_MODE_RE = re.compile(r"[wax+]")
_EXPECTED_REVIEW_SCRIPT_NAMES = frozenset(REVIEW_SCRIPT_FILENAMES)
_LOCAL_REVIEWING_CHANGES_MODULES = frozenset(
    pathlib.Path(filename).stem
    for filename in REVIEW_SCRIPT_FILENAMES
    if filename != "__init__.py"
)
_VIOLATING_SCRIPTS_DIR = REVIEW_FIXTURES_DIR / "violating_scripts"


def _review_script_files() -> tuple[pathlib.Path, ...]:
    return tuple(sorted(SCRIPTS_DIR.glob("*.py")))


def _top_level_name(module: str) -> str:
    return module.split(".", maxsplit=1)[0]


def _imported_modules(source: str) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules.extend(_top_level_name(alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(_top_level_name(node.module))
    return tuple(modules)


def _string_literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _call_string_argument(
    node: ast.Call,
    *,
    position: int,
    name: str,
) -> str | None:
    if len(node.args) > position:
        return _string_literal(node.args[position])
    for keyword in node.keywords:
        if keyword.arg == name:
            return _string_literal(keyword.value)
    return None


def _path_open_write_violation(
    node: ast.Call,
    func: ast.Attribute,
) -> str | None:
    if func.attr != "open":
        return None
    mode = _call_string_argument(node, position=0, name="mode") or "r"
    if _WRITE_MODE_RE.search(mode):
        return f"Path.open({mode!r}) at line {node.lineno}"
    return None


def _attribute_write_violation(
    node: ast.Call,
    func: ast.Attribute,
    *,
    allowed_calls: set[tuple[str, str]],
) -> str | None:
    if isinstance(func.value, ast.Name):
        owner = func.value.id
        call = (owner, func.attr)
        if call in allowed_calls:
            return None
        if call in _FORBIDDEN_ATTR_CALLS or func.attr in _FORBIDDEN_METHOD_NAMES:
            return f"{owner}.{func.attr} at line {node.lineno}"
    elif func.attr in _FORBIDDEN_METHOD_NAMES:
        return f"<expression>.{func.attr} at line {node.lineno}"
    return _path_open_write_violation(node, func)


def _direct_write_violations(script_path: pathlib.Path) -> tuple[str, ...]:
    allowed_calls: set[tuple[str, str]] = set()
    if script_path == COMPUTE_DIFF_SCRIPT:
        allowed_calls = _COMPUTE_DIFF_ALLOWED_WRITE_CALLS
    elif script_path == REVIEW_RUN_SCRIPT:
        allowed_calls = _REVIEW_RUN_ALLOWED_WRITE_CALLS
    violations: list[str] = []
    for node in ast.walk(ast.parse(script_path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_NAME_CALLS:
            mode = _call_string_argument(node, position=1, name="mode") or "r"
            if _WRITE_MODE_RE.search(mode):
                violations.append(f"{node.func.id}({mode!r}) at line {node.lineno}")
        elif isinstance(node.func, ast.Attribute):
            violation = _attribute_write_violation(
                node,
                node.func,
                allowed_calls=allowed_calls,
            )
            if violation:
                violations.append(violation)
    return tuple(violations)


def _runtime_uv_violations(script_path: pathlib.Path) -> tuple[str, ...]:
    return tuple(
        f"runtime reference to 'uv' at line {node.lineno}"
        for node in ast.walk(ast.parse(script_path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Constant) and node.value == "uv"
    )


@dataclass(frozen=True)
class ReviewScriptComplianceObservation:
    """Static compliance findings across the shipped review script set."""

    direct_writes: tuple[str, ...]
    non_stdlib_imports: tuple[str, ...]
    product_toolchain_imports: tuple[str, ...]
    runtime_uv_references: tuple[str, ...]
    alternate_schema_paths: tuple[str, ...]
    persistence_arguments: tuple[str, ...]
    unexpected_scripts: tuple[str, ...]
    parallel_scripts: tuple[str, ...]
    render_directory_exists: bool


def review_script_compliance_observation() -> ReviewScriptComplianceObservation:
    """Inspect every shipped review script against the governed boundaries."""

    scripts = _review_script_files()
    direct_writes = tuple(
        f"{script.name}: {violation}"
        for script in scripts
        for violation in _direct_write_violations(script)
    )
    imported = tuple(
        (script, module)
        for script in scripts
        for module in _imported_modules(script.read_text(encoding="utf-8"))
    )
    stdlib = set(sys.stdlib_module_names)
    non_stdlib = tuple(
        f"{script.name}: import {module!r}"
        for script, module in imported
        if module not in stdlib and module not in _LOCAL_REVIEWING_CHANGES_MODULES
    )
    product_imports = tuple(
        f"{script.name}: import {module!r}"
        for script, module in imported
        if module == "outcomeeng" or module.startswith("outcomeeng_")
    )
    runtime_uv = tuple(
        f"{script.name}: {violation}"
        for script in scripts
        for violation in _runtime_uv_violations(script)
    )
    alternate_schema = tuple(
        str(match.relative_to(SKILL_DIR))
        for pattern in ("*.schema.json", "*.xsd", "openapi.*", "schema.*")
        for match in SKILL_DIR.rglob(pattern)
        if "__pycache__" not in match.parts
    )
    compute_source = COMPUTE_DIFF_SCRIPT.read_text(encoding="utf-8")
    present_names = frozenset(path.name for path in scripts)
    parallel_names = frozenset({"render_review.py", "validate_review_result.py"})
    return ReviewScriptComplianceObservation(
        direct_writes=direct_writes,
        non_stdlib_imports=non_stdlib,
        product_toolchain_imports=product_imports,
        runtime_uv_references=runtime_uv,
        alternate_schema_paths=alternate_schema,
        persistence_arguments=tuple(
            argument for argument in ("--slug",) if argument in compute_source
        ),
        unexpected_scripts=tuple(sorted(present_names - _EXPECTED_REVIEW_SCRIPT_NAMES)),
        parallel_scripts=tuple(sorted(present_names & parallel_names)),
        render_directory_exists=(REVIEW_PROMPT_PATH.parent / "render").exists(),
    )


def violating_review_script_fixtures_detected() -> tuple[bool, ...]:
    """Return scanner detections for each inert violating script fixture."""

    direct_writes = _VIOLATING_SCRIPTS_DIR / "direct_writes.txt"
    non_stdlib = _VIOLATING_SCRIPTS_DIR / "non_stdlib_import.txt"
    product_import = _VIOLATING_SCRIPTS_DIR / "product_toolchain_import.txt"
    runtime_uv = _VIOLATING_SCRIPTS_DIR / "runtime_uv.txt"
    return (
        bool(_direct_write_violations(direct_writes)),
        any(
            module not in sys.stdlib_module_names
            and module not in _LOCAL_REVIEWING_CHANGES_MODULES
            for module in _imported_modules(non_stdlib.read_text(encoding="utf-8"))
        ),
        any(
            module == "outcomeeng" or module.startswith("outcomeeng_")
            for module in _imported_modules(product_import.read_text(encoding="utf-8"))
        ),
        bool(_runtime_uv_violations(runtime_uv)),
    )


@dataclass(frozen=True)
class ReviewRenderObservation:
    """Source finding and rendered journal projection from one complete prefix."""

    finding: dict[str, Any]
    finding_event: dict[str, Any]
    events: tuple[dict[str, Any], ...]
    rendered: dict[str, str]


def review_render_observation() -> ReviewRenderObservation:
    """Render one source-constructed finding through journal events."""

    contracts = review_contract_modules()
    metadata = review_run_metadata()
    finding = make_finding_dict()
    parsed = contracts.review_result.parse_finding_json(json.dumps(finding))
    finding_event = contracts.journal_emit.finding_reported_event(
        parsed,
        now=REVIEW_EVENT_TIME,
        attempt=1,
    )
    events = (finding_event,)
    completed = contracts.journal_emit.run_completed_event(
        metadata,
        list(events),
        completed_at=REVIEW_COMPLETION_TIME,
        now=REVIEW_EVENT_TIME,
        attempt=1,
    )
    prefix = (*events, completed)
    return ReviewRenderObservation(
        finding=finding,
        finding_event=finding_event,
        events=prefix,
        rendered=cast(
            "dict[str, str]",
            contracts.journal_emit.render_events(list(prefix)),
        ),
    )


def review_chain_with_finding_contract_holds() -> bool:
    """Return whether the complete finding-bearing chain matches its contracts."""

    observation = review_chain_with_finding_observation()
    contracts = review_contract_modules()
    return (
        observation.diff_result.returncode == 0
        and observation.changed_file in observation.diff_result.stdout
        and observation.metadata_result.returncode == 0
        and observation.rendered[contracts.journal_emit.RENDER_SURFACE_FIELD]
        == contracts.journal_projection.render_surface(list(observation.events))
        and observation.rendered[contracts.journal_emit.RENDER_OVERALL_FIELD]
        == str(contracts.journal_projection.compute_overall(list(observation.events)))
    )


def clean_review_chain_contract_holds() -> bool:
    """Return whether a clean review projects zero findings."""

    observation = clean_review_chain_observation()
    journal_emit = review_contract_modules().journal_emit
    expected_count = str(len(observation.findings))
    return (
        observation.rendered[journal_emit.RENDER_BLOCKING_FIELD] == expected_count
        and observation.rendered[journal_emit.RENDER_DEBT_FIELD] == expected_count
    )


def malformed_runner_finding_contract_holds() -> bool:
    """Return whether malformed findings stop before the real journal append."""

    observation = malformed_runner_finding_observation()
    projection = review_contract_modules().journal_projection
    return (
        observation.returncode != 0
        and observation.missing_field in observation.stderr
        and observation.event_types == (projection.SCOPE_ENTERED,)
    )


def review_runner_lifecycle_contract_holds() -> bool:
    """Return whether every real-journal runner lifecycle predicate holds."""

    return all(dataclasses.astuple(review_runner_lifecycle_observation()))


def review_journal_command_contract_holds() -> bool:
    """Return whether the runner invokes the independent journal command contract."""

    return REVIEW_JOURNAL_COMMAND == EXPECTED_REVIEW_JOURNAL_COMMAND


def review_journal_type_contract_holds() -> bool:
    """Return whether the runner writes the independent review namespace."""

    return REVIEW_JOURNAL_TYPE == EXPECTED_REVIEW_JOURNAL_TYPE


def review_journal_start_cursor_contract_holds() -> bool:
    """Return whether the runner reads the journal from the first event."""

    return REVIEW_JOURNAL_START_CURSOR == EXPECTED_REVIEW_JOURNAL_START_CURSOR


def review_runner_coverage_contract_holds() -> bool:
    """Return whether incomplete scope prevents real-journal sealing."""

    return all(dataclasses.astuple(review_runner_coverage_observation()))


def review_runner_rename_contract_holds() -> bool:
    """Return whether rename scope requires source and destination paths."""

    return all(dataclasses.astuple(review_runner_rename_observation()))


def compute_diff_scenario_contract_holds() -> bool:
    """Return whether every source-owned compute-diff scenario holds."""

    return all(dataclasses.astuple(compute_diff_scenario_observation()))


def review_wire_vocabulary_mapping_holds() -> bool:
    """Return whether both review enums map to their complete wire domains."""

    review_result = load_review_result_module()
    return {member.value for member in review_result.Severity} == {
        review_result.SEVERITY_BLOCKING,
        review_result.SEVERITY_DEBT,
    } and {member.value for member in review_result.Concern} == {
        review_result.CONCERN_CONSISTENCY,
        review_result.CONCERN_SECURITY,
        review_result.CONCERN_PERFORMANCE,
        review_result.CONCERN_EVIDENCE,
        review_result.CONCERN_ARCHITECTURE,
    }


def review_module_surface_contract_holds() -> bool:
    """Return whether the canonical module exposes only the governed surface."""

    return all(dataclasses.astuple(review_module_surface_observation()))


def review_parse_compliance_contract_holds() -> bool:
    """Return whether conforming and closed rejection cases match the schema."""

    observation = review_parse_compliance_observation()
    return (
        observation.conforming_result_type is observation.expected_result_type
        and not observation.empty_findings
        and observation.missing_document_field in observation.missing_document_error
        and observation.unknown_severity in observation.unknown_severity_error
        and observation.unknown_concern in observation.unknown_concern_error
        and bool(observation.malformed_error)
        and observation.missing_finding_field in observation.missing_finding_error
    )


def rule_citation_contract_holds() -> bool:
    """Return whether inert valid citations pass and a derived malformed one fails."""

    observation = rule_citation_observation()
    review_result = load_review_result_module()
    from outcomeeng_testing.generators.reviewing_changes import (
        valid_rule_citation_cases,
    )

    return (
        observation.accepted_rules == observation.expected_rules
        and observation.malformed_rule in observation.malformed_error
        and {case.family for case in valid_rule_citation_cases()}
        == set(review_result.RuleCitationFamily)
        and all(
            review_result.rule_citation_family(case.citation) is case.family
            for case in valid_rule_citation_cases()
        )
    )


def review_severity_projection_contract_holds() -> bool:
    """Return whether every review severity maps to the shared projection."""

    observation = review_severity_projection_observation()
    return (
        observation.actual_severities == observation.expected_severities
        and observation.actual_outcomes == observation.expected_outcomes
    )


def review_terminal_branch_identity_contract_holds() -> bool:
    """Return whether a terminal event preserves branch run identity."""

    contracts = review_contract_modules()
    metadata = review_run_metadata()
    event = contracts.journal_emit.run_completed_event(
        metadata,
        [],
        completed_at=REVIEW_COMPLETION_TIME,
        now=REVIEW_EVENT_TIME,
        attempt=1,
    )
    data = event["data"]
    projection = contracts.journal_projection
    return bool(
        event["type"] == projection.RUN_COMPLETED
        and data[projection.RUN_STATE_BRANCH_NAME] == metadata.branch_name
        and data[projection.RUN_STATE_BRANCH_SLUG] == metadata.branch_slug
        and data[projection.RUN_STATE_TARGET_KIND]
        == projection.JournalTargetKind.BRANCH
        and data[projection.RUN_STATE_HEAD_SHA] == metadata.head_sha
        and data[projection.RUN_STATE_BASE_REF] == metadata.base_ref
        and data[projection.RUN_STATE_BASE_SHA] == metadata.base_sha
        and data[projection.RUN_STATE_CONFIG_DIGEST] == metadata.config_digest
        and data[projection.RUN_STATE_PARTICIPANTS] == list(metadata.participants)
        and data[projection.RUN_STATE_SCOPE] == dict(metadata.scope)
        and data[projection.RUN_STATE_STARTED_AT] == metadata.started_at
        and data[projection.RUN_STATE_COMPLETED_AT] == REVIEW_COMPLETION_TIME
        and data[projection.RUN_STATE_STATUS] == projection.JournalRunStatus.APPROVED
    )


def review_terminal_pull_request_identity_contract_holds() -> bool:
    """Return whether a terminal event preserves pull-request identity."""

    contracts = review_contract_modules()
    metadata = review_run_metadata(pull_request=True)
    event = contracts.journal_emit.run_completed_event(
        metadata,
        [],
        completed_at=REVIEW_COMPLETION_TIME,
        now=REVIEW_EVENT_TIME,
        attempt=1,
    )
    projection = contracts.journal_projection
    return bool(
        event["data"][projection.RUN_STATE_TARGET_KIND]
        == projection.JournalTargetKind.PULL_REQUEST
        and event["data"][projection.RUN_STATE_PULL_REQUEST_NUMBER]
        == metadata.pull_request_number
    )


def review_render_count_mapping_holds() -> bool:
    """Return whether both finding severities render with the governed counts."""

    contracts = review_contract_modules()
    events = streamed_review_events(
        review_run_metadata(),
        tuple(
            review_finding(severity=severity)
            for severity in (
                contracts.review_result.Severity.BLOCKING,
                contracts.review_result.Severity.DEBT,
            )
        ),
    )
    rendered = contracts.journal_emit.render_events(events)
    return bool(
        rendered[contracts.journal_emit.RENDER_BLOCKING_FIELD] == "1"
        and rendered[contracts.journal_emit.RENDER_DEBT_FIELD] == "1"
        and rendered[contracts.journal_emit.RENDER_COUNT_LINE_FIELD]
        == "BLOCKING: 1, DEBT: 1"
        and rendered[contracts.journal_emit.RENDER_OVERALL_FIELD]
        == str(contracts.journal_projection.Outcome.REJECTED)
        and rendered[contracts.journal_emit.RENDER_SURFACE_FIELD]
        == contracts.journal_projection.render_surface(events)
    )


def missing_terminal_base_identity_is_rejected() -> bool:
    """Return whether the terminal adapter rejects absent base identity."""

    contracts = review_contract_modules()
    try:
        contracts.journal_emit.run_completed_event(
            review_run_metadata(missing_base_identity=True),
            [],
            completed_at=REVIEW_COMPLETION_TIME,
            now=REVIEW_EVENT_TIME,
            attempt=1,
        )
    except ValueError as exc:
        return contracts.journal_projection.RUN_STATE_BASE_SHA in str(exc)
    return False


def review_config_digest_contract_holds() -> bool:
    """Return whether every review configuration identity mapping holds."""

    return all(dataclasses.astuple(review_config_digest_observation()))


def review_metadata_contract_holds() -> bool:
    """Return whether every review metadata mapping holds."""

    return all(dataclasses.astuple(review_metadata_observation()))


def review_event_cli_contract_holds() -> bool:
    """Return whether every event CLI mapping holds."""

    return all(dataclasses.astuple(review_event_cli_observation()))


def review_script_set_contract_holds() -> bool:
    """Return whether the shipped script set has no alternate renderer."""

    observation = review_script_compliance_observation()
    return not observation.unexpected_scripts and not observation.parallel_scripts


def review_render_contract_holds() -> bool:
    """Return whether render output derives from the shared journal projection."""

    observation = review_render_observation()
    contracts = review_contract_modules()
    return observation.rendered[
        contracts.journal_emit.RENDER_SURFACE_FIELD
    ] == contracts.journal_projection.render_surface(
        list(observation.events)
    ) and observation.rendered[contracts.journal_emit.RENDER_OVERALL_FIELD] == str(
        contracts.journal_projection.compute_overall(list(observation.events))
    )
