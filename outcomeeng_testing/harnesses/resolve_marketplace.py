"""Infrastructure for the /issue marketplace resolver's ``l1`` evidence.

The harness loads the shipped standalone script and owns the subprocess
invocation that drives it. Production vocabulary — field names, runtime
tokens, exit statuses, the none-available token — comes from the loaded
script rather than from any value restated here.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
from types import ModuleType

from hypothesis import settings

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
RESOLVER_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "issue"
    / "scripts"
    / "resolve_marketplace.py"
)


class ResolverHarnessError(RuntimeError):
    """The shipped resolver script could not be loaded."""


def _load_resolver() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "resolve_marketplace", RESOLVER_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ResolverHarnessError(
            f"no import spec for shipped resolver at {RESOLVER_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RESOLVER = _load_resolver()
"""The loaded shipped script; the only source of resolver vocabulary."""


def run_resolver_stdin(
    stdin: str,
    *,
    runtime: str,
    name: str | None = RESOLVER.DEFAULT_MARKETPLACE_NAME,
    cwd: pathlib.Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Drive the resolver over exactly these stdin bytes.

    ``name=None`` omits ``--name`` so the invocation takes the CLI default.
    ``cwd`` runs the resolver from that directory, so a caller can observe
    what the invocation leaves behind there.

    The name is attached with ``--name=`` so a value beginning with ``-``
    reaches the resolver instead of being read as another option.
    """
    name_argv = [] if name is None else [f"--name={name}"]
    return subprocess.run(
        [
            sys.executable,
            str(RESOLVER_MODULE_PATH),
            "--runtime",
            runtime,
            *name_argv,
        ],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        cwd=None if cwd is None else str(cwd),
    )


def run_resolver(
    payload: object,
    *,
    runtime: str,
    name: str | None = RESOLVER.DEFAULT_MARKETPLACE_NAME,
    cwd: pathlib.Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Serialize a JSON value and drive the resolver with it.

    Every JSON value serializes, a bare string included; a caller wanting
    stdin that is not a JSON document calls ``run_resolver_stdin``.
    """
    return run_resolver_stdin(json.dumps(payload), runtime=runtime, name=name, cwd=cwd)


def none_available_message(*, name: str, runtime: str) -> str:
    """The stderr line the resolver emits when nothing local resolves.

    Rendered from the production message template so a reword of that
    message moves the expectation with it.
    """
    # The resolver is loaded through importlib, so every attribute reaches
    # this module as Any; the annotations restate the type the source declares.
    template: str = RESOLVER.NOT_FOUND_MESSAGE
    available: str = RESOLVER.NO_LOCAL_MARKETPLACES
    return template.format(name=name, runtime=runtime, available=available)


def available_message(*, name: str, runtime: str, available: str) -> str:
    """The stderr line for a request that resolved nothing.

    ``available`` is the caller's own expectation of which marketplaces the
    listing resolves; the harness only renders it through the production
    message template.
    """
    template: str = RESOLVER.NOT_FOUND_MESSAGE
    return template.format(name=name, runtime=runtime, available=available)


def invalid_json_message_prefix() -> str:
    """The stable leading text of the production invalid-JSON message."""
    template: str = RESOLVER.INVALID_JSON_MESSAGE
    return template.split("{error}")[0]


resolver_property_run = settings(
    max_examples=40,
    deadline=None,
    print_blob=True,
)
"""Execution configuration for resolver property runs.

Every example spawns the resolver as a subprocess, so the run count is
bounded and the per-example deadline is lifted here rather than in an
executed test. ``print_blob`` emits the replay payload for a failing case.
"""
