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

import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from types import ModuleType
from typing import Any, Callable, cast
from unittest.mock import patch

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

# Fixture rule citation: a real path-style citation that satisfies the
# parser's rule-form check. Points at this verification skill's own spec so the citation
# is stable and self-contained — no external rule required.
FIXTURE_RULE_CITATION = (
    "spx/21-spec-tree.enabler/68-reviewing.enabler/"
    "21-reviewing-changes.enabler/reviewing-changes.md:ALWAYS:1"
)
FIXTURE_ADR_RULE_CITATION = (
    "spx/21-spec-tree.enabler/68-reviewing.enabler/"
    "21-reviewing-changes.enabler/21-script-decomposition.adr.md"
)
FIXTURE_AGENTS_RULE_CITATION = "AGENTS.md:critical-rules"
FIXTURE_SKILL_RULE_CITATION = (
    "plugins/spec-tree/skills/review-changes/SKILL.md:api-surface"
)
FIXTURE_MALFORMED_RULE_CITATION = "record this in ISSUES.md"

# One real citation per accepted family, keyed by the family name the
# ``review_result`` module declares in ``RULE_CITATION_FAMILIES``. Each value
# resolves against this checkout, so acceptance exercises the parser's file and
# slug verification, not only its grammar.
RULE_CITATION_EXEMPLARS: dict[str, str] = {
    "spec-assertion": FIXTURE_RULE_CITATION,
    "decision": FIXTURE_ADR_RULE_CITATION,
    "plugin-skill": FIXTURE_SKILL_RULE_CITATION,
    "root-rule": FIXTURE_AGENTS_RULE_CITATION,
}


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
            returncode = _module_main(module)(list(args))
    finally:
        os.chdir(old_cwd)
    return subprocess.CompletedProcess(
        argv,
        returncode,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )


def run_git(*args: str, cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    """Run ``git`` rooted at ``cwd`` with workstation configuration suppressed.

    The invocation blanks global and system config and pins the author and
    committer identity so a synthetic repository never inherits operator
    identity or commit-signing settings.
    """
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    return subprocess.run(  # noqa: S603 — args come from the harness, not user input
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def init_repo_with_branch(repo: pathlib.Path) -> str:
    """Create a synthetic repository with ``main`` and a feature branch.

    The feature branch changes ``README.md``. Returns the base ref name.
    """
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


def init_repo_with_committed_rename(repo: pathlib.Path) -> str:
    """Create a synthetic repository whose feature branch renames a tracked file."""
    run_git("init", "-q", "-b", "main", str(repo), cwd=pathlib.Path.cwd())
    run_git("config", "commit.gpgsign", "false", cwd=repo)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    run_git("add", "README.md", cwd=repo)
    run_git("commit", "-q", "-m", "initial", cwd=repo)
    run_git("switch", "-c", "feature/x", cwd=repo)
    run_git("mv", "README.md", "RENAMED.md", cwd=repo)
    run_git("commit", "-q", "-m", "rename readme", cwd=repo)
    return "main"


def isolated_git_env(cwd: pathlib.Path) -> dict[str, str]:
    """Return a subprocess environment whose git reads no workstation config."""
    return {
        **os.environ,
        "PWD": str(cwd),
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    }


def runner_env(
    tmp_path: pathlib.Path, repo: pathlib.Path, base_ref: str
) -> tuple[dict[str, str], pathlib.Path]:
    """Return an environment that routes ``review_run.py`` at a fake ``spx``.

    Writes the fake ``spx`` under ``tmp_path/bin`` and points it at a fresh
    journal file; returns the environment and that journal path. The caller
    owns cleanup through the ``tmp_path`` fixture.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    journal_path = tmp_path / "journal.json"
    write_fake_spx(bin_dir, journal_path)
    env = isolated_git_env(repo)
    env["SPX_VERIFY_BASE_REF"] = base_ref
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["SPX_FAKE_JOURNAL_PATH"] = str(journal_path)
    env["SPX_FAKE_NAMESPACE_KEYS"] = json.dumps(review_run_journal_env_keys())
    return env, journal_path


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
                "rule": FIXTURE_RULE_CITATION,
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
        "rule": FIXTURE_RULE_CITATION,
        "message": "The identifier is not descriptive.",
        "action": "Rename the symbol to convey its role.",
    }
    finding.update(overrides)
    return finding
