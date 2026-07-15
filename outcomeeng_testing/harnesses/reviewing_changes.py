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
- ``make_review_result_dict``. Factory that returns a synthetic
  ``review-result`` JSON-ready dict with every required field populated,
  ready to be mutated by callers to construct invalid documents for
  rejection-path tests.

The harness lives in ``outcomeeng_testing/harnesses/`` because shared test
scaffolding is production code with its home outside ``tests/`` and
outside ``spx/``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Callable, cast
from unittest.mock import patch

from hypothesis import given, seed, settings

from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

# Two ``parents`` hops land at the repository root: this file lives at
# ``outcomeeng_testing/harnesses/reviewing_changes.py``.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

SKILL_DIR = REPO_ROOT / "src" / "plugins" / "spec-tree" / "skills" / "review-changes"
SKILL_FILE = SKILL_DIR / "SKILL.md"
SCRIPTS_DIR = SKILL_DIR / "scripts"
REFERENCES_DIR = SKILL_DIR / "references"
REVIEW_PROMPT_PATH = REFERENCES_DIR / "review-prompt.md"

REVIEW_RESULT_MODULE_PATH = SCRIPTS_DIR / "review_result.py"
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


def load_review_result_module() -> ModuleType:
    """Load the ``review_result`` policy module via importlib.

    The review-changes scripts ship under ``src/plugins/`` (the authored
    plugin source directory) and are not importable as a package.
    Tests that introspect ``SCHEMA_VERSION``, the ``Severity`` /
    ``Concern`` enums, the frozen ``Finding`` /
    ``ReviewResult`` dataclasses, or the ``parse_json`` /
    ``ReviewResultValidationError`` entry points load the module here.

    Returns the already-loaded module on subsequent calls so the importlib
    loader runs at most once per test session.
    """
    cached = sys.modules.get("review_result")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "review_result", REVIEW_RESULT_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load review_result from {REVIEW_RESULT_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["review_result"] = module
    spec.loader.exec_module(module)
    return module


def review_rule_citations() -> tuple[str, ...]:
    """Derive one valid citation from each supported source family."""

    review_result = load_review_result_module()
    spec_text = REVIEW_SPEC_PATH.read_text(encoding="utf-8")
    assertion_kind = next(
        kind for kind in ("ALWAYS", "NEVER") if f"- {kind}:" in spec_text
    )
    spec_citation = f"{REVIEW_SPEC_PATH.relative_to(REPO_ROOT)}:{assertion_kind}:1"
    adr_path = next(iter(sorted(REVIEW_NODE_DIR.glob("*-*.adr.md"))))
    pdr_path = next(iter(sorted((REPO_ROOT / "spx").glob("*-*.pdr.md"))))

    agents_path = REPO_ROOT / "AGENTS.md"
    agents_slug = next(
        iter(
            sorted(
                review_result._declared_rule_slugs(
                    agents_path.read_text(encoding="utf-8"),
                ),
            ),
        ),
    )
    skill_slug = next(
        iter(
            sorted(
                review_result._declared_rule_slugs(
                    SKILL_FILE.read_text(encoding="utf-8"),
                ),
            ),
        ),
    )
    claude_path = REPO_ROOT / "CLAUDE.md"
    claude_slug = next(
        iter(
            sorted(
                review_result._declared_rule_slugs(
                    claude_path.read_text(encoding="utf-8"),
                ),
            ),
        ),
    )
    return (
        spec_citation,
        str(adr_path.relative_to(REPO_ROOT)),
        str(pdr_path.relative_to(REPO_ROOT)),
        f"plugins/spec-tree/skills/review-changes/SKILL.md:{skill_slug}",
        f"AGENTS.md:{agents_slug}",
        f"CLAUDE.md:{claude_slug}",
    )


def malformed_rule_citation() -> str:
    """Derive a malformed citation from a valid source-owned citation."""

    return f"{review_rule_citations()[0]}:invalid"


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
    options: dict[str, object] = {}
    if pull_request:
        options = {
            "target_kind": projection.JournalTargetKind.PULL_REQUEST,
            "pull_request_number": 123,
        }
    return projection.RunMetadata(
        target="working-diff",
        scope_hash="abc123def456",
        branch_name="work/example",
        branch_slug="work__example",
        head_sha="1" * 40,
        base_ref="main",
        base_sha="" if missing_base_identity else "2" * 40,
        config_digest="cfg-abc123",
        participants=("review",),
        scope={"include": ["README.md"]},
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:00Z",
        output_paths=(),
        **options,
    )


def review_finding(*, severity: Any, identifier: str) -> Any:
    """Return one parsed source-contract finding for journal projection."""

    review_result = load_review_result_module()
    return review_result.parse_finding_json(
        json.dumps(
            make_finding_dict(
                id=identifier,
                severity=severity,
                file="README.md",
                line=1,
                message=f"{identifier} evidence",
                action=f"{identifier} action",
            ),
        ),
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

    from outcomeeng_testing.harnesses.journal_projection import (
        load_journal_projection_module,
    )

    projection = load_journal_projection_module()
    metadata = review_run_metadata()
    return json.dumps(
        {
            "target": metadata.target,
            projection.RUN_STATE_SCOPE_HASH: metadata.scope_hash,
            projection.RUN_STATE_BRANCH_NAME: metadata.branch_name,
            projection.RUN_STATE_BRANCH_SLUG: metadata.branch_slug,
            projection.RUN_STATE_TARGET_KIND: str(
                projection.JournalTargetKind.BRANCH,
            ),
            projection.RUN_STATE_HEAD_SHA: metadata.head_sha,
            projection.RUN_STATE_BASE_REF: metadata.base_ref,
            projection.RUN_STATE_BASE_SHA: metadata.base_sha,
            projection.RUN_STATE_CONFIG_DIGEST: metadata.config_digest,
            projection.RUN_STATE_PARTICIPANTS: list(metadata.participants),
            projection.RUN_STATE_SCOPE: dict(metadata.scope),
            projection.RUN_STATE_STARTED_AT: metadata.started_at,
            projection.RUN_STATE_COMPLETED_AT: metadata.completed_at,
            projection.RUN_STATE_OUTPUT_PATHS: [],
        },
    )


def write_review_skill_config(root: pathlib.Path, *, prompt: str) -> None:
    """Write the standalone review prompt consumed by config digesting."""

    references = root / "references"
    references.mkdir(parents=True)
    (references / "review-prompt.md").write_text(prompt, encoding="utf-8")


def write_review_manifest(
    root: pathlib.Path,
    *,
    base_ref: str = "origin/main",
    head_ref: str = "HEAD",
    files: list[str] | None = None,
    diff_sha256: str = "a" * 64,
) -> pathlib.Path:
    """Write one source-schema review-input manifest."""

    journal_emit = load_journal_emit_module()
    manifest = {
        "schema_version": journal_emit.MANIFEST_SCHEMA_VERSION,
        "base_ref": base_ref,
        "head_ref": head_ref,
        "diff_path": "diff.md",
        "diff_sha256": diff_sha256,
        "diff_bytes": 1,
        "sections": [
            {
                "title": "Committed diff",
                "files": files or ["README.md"],
                "start_line": 1,
                "line_count": 1,
                "byte_start": 0,
                "byte_length": 1,
            },
        ],
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


@dataclass
class ReviewMetadataHarness:
    """Injected collaborators for deterministic review metadata evidence."""

    base_ref: str = "origin/main"
    head_ref: str = "HEAD"
    branch_name: str = "work/example"
    changed_files: list[str] = field(default_factory=lambda: ["README.md"])
    review_inputs: list[str] = field(
        default_factory=lambda: ["### Committed diff\n\nREADME change"],
    )
    config_digest: str = "cfg-abc123"

    def deps(
        self,
        *,
        source_branch: bool = False,
        source_target: bool = False,
        manifest_scope: bool = False,
        fail_scope: bool = False,
    ) -> Any:
        """Return production MetadataDeps configured for one evidence boundary."""

        journal_emit = load_journal_emit_module()

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
            review_input = (
                self.review_inputs.pop(0)
                if len(self.review_inputs) > 1
                else self.review_inputs[0]
            )
            return {
                "baseRef": base_ref,
                "headRef": head_ref,
                "changedFiles": list(self.changed_files),
                "reviewInputSha256": hashlib.sha256(
                    review_input.encode("utf-8"),
                ).hexdigest(),
            }

        return journal_emit.MetadataDeps(
            resolve_base_ref=lambda: self.base_ref,
            resolve_head_ref=lambda: self.head_ref,
            resolve_branch_name=(
                journal_emit._resolve_branch_name
                if source_branch
                else lambda: self.branch_name
            ),
            resolve_target_kind=(
                journal_emit._resolve_target_kind
                if source_target
                else lambda: journal_emit.jp.JournalTargetKind.BRANCH
            ),
            resolve_pull_request_number=(
                journal_emit._resolve_pull_request_number
                if source_target
                else lambda _target: None
            ),
            review_scope=review_scope,
            review_scope_from_manifest=(
                journal_emit._review_scope_from_manifest
                if manifest_scope
                else lambda _path: review_scope(
                    base_ref=self.base_ref,
                    head_ref=self.head_ref,
                    repo=pathlib.Path.cwd(),
                )
            ),
            branch_slug=lambda _branch: "work__example",
            commit_oid=lambda ref, *, repo: f"{ref}:sha",
            config_digest=lambda: self.config_digest,
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


REVIEW_EVENT_TIME = "2026-06-23T00:00:06Z"
REVIEW_COMPLETION_TIME = "2026-06-23T00:00:05Z"
REVIEW_ENV_BACKEND = review_run_journal_env_key("ENV_BACKEND")
REVIEW_ENV_BRANCH = review_run_journal_env_key("ENV_BRANCH")
REVIEW_ENV_TARGET_KIND = review_run_journal_env_key("ENV_TARGET_KIND")
REVIEW_ENV_PULL_REQUEST_NUMBER = review_run_journal_env_key(
    "ENV_PULL_REQUEST_NUMBER",
)


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

    return {
        **os.environ,
        "PWD": str(cwd),
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    }


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


def review_git_repo(tmp_path: pathlib.Path) -> tuple[pathlib.Path, str]:
    """Create the standard review repository under a pytest temporary path."""

    repo = tmp_path / "repo"
    repo.mkdir()
    return repo, init_review_git_repo(repo)


def review_git_repo_with_secondary_head(
    tmp_path: pathlib.Path,
) -> tuple[pathlib.Path, str, str]:
    """Create the standard review repository plus one alternate head."""

    repo, base_ref = review_git_repo(tmp_path)
    secondary = "feature/y"
    add_secondary_review_branch(repo, secondary, "SECONDARY.md")
    return repo, base_ref, secondary


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
            patch.dict(os.environ, env, clear=True),
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
            patch.object(sys, "stdin", input_stream),
            patch.dict(os.environ, env or os.environ.copy(), clear=True),
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


def write_fake_spx(bin_dir: pathlib.Path, journal_path: pathlib.Path) -> pathlib.Path:
    """Write a fake ``spx`` executable that enforces journal namespace continuity.

    The fake records the selector environment present at ``journal open`` and
    rejects later ``append``, ``read``, or ``seal`` calls whose ``--run`` token
    or selector differs. This makes the runner boundary test exercise the same
    class of failure as the real journal backend without reaching into the
    backend's filesystem layout.
    """

    script = bin_dir / "spx"
    script.write_text(
        """#!/usr/bin/env python3
import json
import os
import pathlib
import sys


def namespace():
    keys = json.loads(os.environ["SPX_FAKE_NAMESPACE_KEYS"])
    return {key: os.environ.get(key, "") for key in keys}


def option_value(args, name):
    try:
        index = args.index(name)
    except ValueError:
        return ""
    try:
        return args[index + 1]
    except IndexError:
        return ""


path = pathlib.Path(os.environ["SPX_FAKE_JOURNAL_PATH"])
if path.is_file():
    state = json.loads(path.read_text(encoding="utf-8"))
else:
    state = {"commands": [], "events": [], "sealed": False}

args = sys.argv[1:]
if len(args) < 2 or args[0] != "journal":
    sys.stderr.write("expected spx journal command\\n")
    raise SystemExit(2)

command = args[1]
current_namespace = namespace()
state["commands"].append(command)
if command == "open":
    state["namespace"] = current_namespace
    state["runToken"] = "run-001"
    path.write_text(json.dumps(state), encoding="utf-8")
    print(json.dumps({"runToken": "run-001"}))
elif option_value(args, "--run") != state.get("runToken"):
    path.write_text(json.dumps(state), encoding="utf-8")
    sys.stderr.write("journal run not found; open the run before operating on it\\n")
    raise SystemExit(4)
elif current_namespace != state.get("namespace"):
    path.write_text(json.dumps(state), encoding="utf-8")
    sys.stderr.write("journal run not found; open the run before operating on it\\n")
    raise SystemExit(4)
elif command == "append":
    if state["sealed"]:
        sys.stderr.write("run is sealed\\n")
        raise SystemExit(3)
    state["events"].append(json.load(sys.stdin))
    path.write_text(json.dumps(state), encoding="utf-8")
    print(json.dumps({"ok": True}))
elif command == "read":
    path.write_text(json.dumps(state), encoding="utf-8")
    print(json.dumps(state["events"]))
elif command == "seal":
    state["sealed"] = True
    path.write_text(json.dumps(state), encoding="utf-8")
    print(json.dumps({"ok": True}))
elif command == "render":
    path.write_text(json.dumps(state), encoding="utf-8")
    print(json.dumps(state["events"]))
else:
    sys.stderr.write(f"unknown command {command}\\n")
    raise SystemExit(2)
""",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def make_review_result_dict(
    *,
    findings: list[dict[str, Any]] | None = None,
    schema_version: int | None = None,
) -> dict[str, Any]:
    """Return a synthetic review-result dict with every required field.

    Default shape: one ``debt``-severity finding under the ``architecture``
    concern. A review carries findings only — no summary, acknowledgement,
    decision, or verdict field — so the dict has exactly ``schema_version``
    and ``findings``. The debt finding carries an ``action`` populated with
    a required change to satisfy the required-field check. The defaults make
    the conforming case the trivial caller; rejection-path tests mutate one
    field on the returned dict to construct each violation.

    ``schema_version`` defaults to the module-level ``SCHEMA_VERSION``
    from the loaded ``review_result`` module so tests automatically pick
    up future bumps without re-asserting the version.
    """
    review_result = load_review_result_module()
    version = (
        schema_version if schema_version is not None else review_result.SCHEMA_VERSION
    )
    if findings is None:
        findings = [
            {
                "id": "F-001",
                "concern": review_result.Concern.ARCHITECTURE,
                "severity": review_result.Severity.DEBT,
                "file": "example.py",
                "line": 10,
                "rule": review_rule_citations()[0],
                "message": "The identifier is not descriptive.",
                "action": "Rename the symbol to convey its role.",
            }
        ]
    return {
        "schema_version": version,
        "findings": findings,
    }


def make_finding_dict(**overrides: Any) -> dict[str, Any]:
    """Return one synthetic finding dict with every required field populated.

    The streaming review emits findings one at a time, so the per-finding
    validity gate (``review_result.parse_finding_json`` /
    ``journal_emit.py finding-reported``) parses a single finding document.
    The default is a ``debt``/``architecture`` finding with a valid rule
    citation; callers pass ``**overrides`` to vary a field or construct a
    rejection-path document.
    """
    review_result = load_review_result_module()
    finding = {
        "id": "F-001",
        "concern": review_result.Concern.ARCHITECTURE,
        "severity": review_result.Severity.DEBT,
        "file": "example.py",
        "line": 10,
        "rule": review_rule_citations()[0],
        "message": "The identifier is not descriptive.",
        "action": "Rename the symbol to convey its role.",
    }
    finding.update(overrides)
    return finding
