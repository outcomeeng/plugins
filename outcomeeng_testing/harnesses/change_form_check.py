"""Harness for the change-standards form check.

Loads the form check module by path, builds a one-commit checkout from an inert
fixture tree, and observes the check function and the script on one request.
It returns observations; the linked tests own every predicate.
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Final

type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)

_REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[2]
_FIXTURE_ROOT: Final = (
    Path(__file__).resolve().parents[1] / "fixtures" / "change_standards"
)
_MODULE_NAME: Final = "form_check_under_test"
_GIT_ENVIRONMENT: Final = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "Fixture",
    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
    "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+0000",
    "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+0000",
}

FORM_CHECK_SCRIPT: Final = (
    _REPOSITORY_ROOT
    / "src/plugins/product-tree/skills/change-standards/scripts/form_check.py"
)
PASSING_DRAFT: Final = _FIXTURE_ROOT / "draft_adding_node.md"
DRAFT_WITH_UNNAMED_KEY: Final = _FIXTURE_ROOT / "draft_adding_node.with_unnamed_key.md"


@dataclass(frozen=True)
class FormCheckObservation:
    """What the check function and the script each returned for one request."""

    function_result: dict[str, JsonValue]
    script_result: dict[str, JsonValue]
    script_exit_code: int


def _json_object(text: str) -> dict[str, JsonValue]:
    value: JsonValue = json.loads(text)
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object, received {text!r}")
    return value


def _git(checkout: Path, *arguments: str) -> None:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is required to build the fixture checkout")
    subprocess.run(  # noqa: S603 -- array arguments, no shell, resolved executable
        [git, "-C", str(checkout), *arguments],
        check=True,
        capture_output=True,
        text=True,
        env=_GIT_ENVIRONMENT,
    )


@contextmanager
def loaded_form_check() -> Iterator[ModuleType]:
    """Load the form check module by path for the span of one test."""
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, FORM_CHECK_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {FORM_CHECK_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        del sys.modules[_MODULE_NAME]


@contextmanager
def checkout_with_one_commit() -> Iterator[Path]:
    """Yield a checkout root whose one commit holds the fixture tree."""
    with TemporaryDirectory() as directory:
        root = Path(directory)
        shutil.copytree(_FIXTURE_ROOT / "checkout" / "spx", root / "spx")
        _git(root, "init", "-b", "main")
        _git(root, "add", "-A")
        _git(root, "commit", "-m", "base")
        yield root


def judge_draft(
    form_check: ModuleType,
    *,
    draft: Path,
    checkout_root: Path,
    operation: str,
    stored_record: JsonValue,
) -> FormCheckObservation:
    """Run the check function and the script on one request and return both."""
    request = json.loads(
        json.dumps(
            {
                form_check.RequestField.DRAFT_PATH: str(draft),
                form_check.RequestField.CHECKOUT_ROOT: str(checkout_root),
                form_check.RequestField.OPERATION: operation,
                form_check.RequestField.STORED_RECORD: stored_record,
                form_check.RequestField.BLOCKER_RECORDS: [],
                form_check.RequestField.SIZE_LIMIT: form_check.GITHUB_SIZE_LIMIT,
            }
        )
    )
    function_result = _json_object(json.dumps(form_check.check(request)))
    completed = subprocess.run(  # noqa: S603 -- array arguments, no shell
        [sys.executable, str(FORM_CHECK_SCRIPT)],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        check=False,
    )
    return FormCheckObservation(
        function_result=function_result,
        script_result=_json_object(completed.stdout),
        script_exit_code=completed.returncode,
    )
