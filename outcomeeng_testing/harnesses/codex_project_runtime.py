"""Real-Codex evidence for project-scoped plugin and agent resolution."""

from __future__ import annotations

import hashlib
import json
import os
import selectors
import subprocess
import time
import tomllib
from collections import Counter
from collections.abc import Iterable, Mapping
from enum import IntEnum, StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, cast

from outcomeeng.distribution.agents import convert_agents
from outcomeeng.distribution.codex_project import (
    CODEX_COMMAND,
    CODEX_HOME_ENV,
    CONFIG_AGENTS_KEY,
    CONFIG_FILE_KEY,
    ENABLED_KEY,
    NAME_KEY,
    ProjectRuntimeError,
    ProjectRuntimePaths,
    build_project_runtime,
    project_runtime_paths,
)

APP_SERVER_ARGV: Final = (CODEX_COMMAND, "app-server")
APP_SERVER_TIMEOUT_SECONDS: Final = 30
APP_SERVER_STOP_TIMEOUT_SECONDS: Final = 1
APP_SERVER_CLIENT_NAME: Final = "outcomeeng-project-runtime-test"
APP_SERVER_CLIENT_VERSION: Final = "1.0.0"
PROJECT_LAYER_TYPE: Final = "project"


class RequestId(IntEnum):
    """Correlate the bounded app-server requests used by this harness."""

    INITIALIZE = 1
    SKILLS_LIST = 2
    CONFIG_READ = 3


class Method(StrEnum):
    """Codex app-server methods exercised by this harness."""

    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    SKILLS_LIST = "skills/list"
    CONFIG_READ = "config/read"


class Field(StrEnum):
    """Codex app-server protocol fields consumed by this harness."""

    CLIENT_INFO = "clientInfo"
    CONFIG = "config"
    CWD = "cwd"
    CWDS = "cwds"
    DATA = "data"
    ERRORS = "errors"
    FORCE_RELOAD = "forceReload"
    ID = "id"
    INCLUDE_LAYERS = "includeLayers"
    LAYERS = "layers"
    METHOD = "method"
    PARAMS = "params"
    PATH = "path"
    RESULT = "result"
    SKILLS = "skills"
    TYPE = "type"
    VERSION = "version"


def project_codex_runtime_resolves_worktree_artifacts() -> bool:
    """Run real Codex against isolated checkout-local plugin state."""
    source_root = Path.cwd().resolve()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        project_root = temporary_root / "project"
        codex_home = temporary_root / "codex-home"
        project_root.mkdir()
        paths = project_runtime_paths(
            project_root,
            source_root=source_root,
            codex_home=codex_home,
        )
        build_project_runtime(
            project_root,
            source_root=source_root,
            codex_home=codex_home,
        )
        responses = _run_app_server(paths)
        _assert_skill_resolution(responses, paths)
        _assert_agent_resolution(responses, paths)
    return True


def generated_skill_files(dist_root: Path) -> tuple[Path, ...]:
    """Return every generated skill entrypoint exposed by the local marketplace."""
    return tuple(sorted(dist_root.glob("*/skills/*/SKILL.md")))


def _requests(project_root: Path) -> tuple[Mapping[str, object], ...]:
    return (
        {
            Field.ID: RequestId.INITIALIZE,
            Field.METHOD: Method.INITIALIZE,
            Field.PARAMS: {
                Field.CLIENT_INFO: {
                    NAME_KEY: APP_SERVER_CLIENT_NAME,
                    Field.VERSION: APP_SERVER_CLIENT_VERSION,
                }
            },
        },
        {Field.METHOD: Method.INITIALIZED},
        {
            Field.ID: RequestId.SKILLS_LIST,
            Field.METHOD: Method.SKILLS_LIST,
            Field.PARAMS: {
                Field.CWDS: [str(project_root)],
                Field.FORCE_RELOAD: True,
            },
        },
        {
            Field.ID: RequestId.CONFIG_READ,
            Field.METHOD: Method.CONFIG_READ,
            Field.PARAMS: {
                Field.CWD: str(project_root),
                Field.INCLUDE_LAYERS: True,
            },
        },
    )


def _run_app_server(
    paths: ProjectRuntimePaths,
) -> Mapping[RequestId, Mapping[str, object]]:
    environment = {**os.environ, CODEX_HOME_ENV: str(paths.codex_home)}
    process = subprocess.Popen(
        APP_SERVER_ARGV,
        cwd=paths.project_root,
        env=environment,
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    responses: dict[RequestId, Mapping[str, object]] = {}
    deadline = time.monotonic() + APP_SERVER_TIMEOUT_SECONDS
    try:
        for request in _requests(paths.project_root):
            _write_request(process, request)
            request_id = request.get(Field.ID)
            if isinstance(request_id, RequestId):
                responses[request_id] = _read_response(
                    process,
                    request_id,
                    deadline,
                )
        return responses
    finally:
        _stop_process(process)


def _write_request(
    process: subprocess.Popen[str],
    request: Mapping[str, object],
) -> None:
    if process.stdin is None:
        raise ProjectRuntimeError("Codex app-server stdin is unavailable")
    process.stdin.write(f"{json.dumps(request)}\n")
    process.stdin.flush()


def _read_response(
    process: subprocess.Popen[str],
    request_id: RequestId,
    deadline: float,
) -> Mapping[str, object]:
    if process.stdout is None:
        raise ProjectRuntimeError("Codex app-server stdout is unavailable")
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not selector.select(remaining):
                raise ProjectRuntimeError(
                    f"Codex app-server timed out waiting for request {request_id}"
                )
            line = process.stdout.readline()
            if not line:
                stderr = process.stderr.read().strip() if process.stderr else ""
                raise ProjectRuntimeError(
                    f"Codex app-server exited before request {request_id}: {stderr}"
                )
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ProjectRuntimeError(
                    "Codex app-server returned invalid JSON"
                ) from exc
            if isinstance(payload, dict) and payload.get(Field.ID) == request_id:
                return cast(Mapping[str, object], payload)


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.stdin is not None:
        process.stdin.close()
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=APP_SERVER_STOP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=APP_SERVER_STOP_TIMEOUT_SECONDS)


def _assert_skill_resolution(
    responses: Mapping[RequestId, Mapping[str, object]],
    paths: ProjectRuntimePaths,
) -> None:
    result = _response_result(responses, RequestId.SKILLS_LIST)
    project_entry = _single_mapping(
        entry
        for entry in _mapping_array(result, Field.DATA)
        if _resolved_path(entry, Field.CWD) == paths.project_root
    )
    if _required_array(project_entry, Field.ERRORS):
        raise ProjectRuntimeError("Codex reported project skill loading errors")
    resolved = {
        _resolved_path(skill, Field.PATH)
        for skill in _mapping_array(project_entry, Field.SKILLS)
        if skill.get(ENABLED_KEY) is True
    }
    local_skill_files = tuple(
        path
        for path in resolved
        if path.is_file() and path.is_relative_to(paths.codex_home)
    )
    expected_digests = Counter(
        _file_digest(path) for path in generated_skill_files(paths.dist_root)
    )
    resolved_digests = Counter(_file_digest(path) for path in local_skill_files)
    missing = expected_digests - resolved_digests
    if missing:
        raise ProjectRuntimeError(
            f"Codex omitted {sum(missing.values())} checkout-local generated skills"
        )


def _assert_agent_resolution(
    responses: Mapping[RequestId, Mapping[str, object]],
    paths: ProjectRuntimePaths,
) -> None:
    result = _response_result(responses, RequestId.CONFIG_READ)
    project_layer = _single_mapping(
        layer
        for layer in _mapping_array(result, Field.LAYERS)
        if _required_mapping(layer, NAME_KEY).get(Field.TYPE) == PROJECT_LAYER_TYPE
    )
    config = _required_mapping(project_layer, Field.CONFIG)
    if CONFIG_AGENTS_KEY in config:
        raise ProjectRuntimeError("Codex project layer contains local agent bindings")
    agent_layer = _single_mapping(
        layer
        for layer in _mapping_array(result, Field.LAYERS)
        if CONFIG_AGENTS_KEY in _required_mapping(layer, Field.CONFIG)
    )
    configured_agents = _required_mapping(
        _required_mapping(agent_layer, Field.CONFIG),
        CONFIG_AGENTS_KEY,
    )
    expected_names = {
        _required_string(agent.values, NAME_KEY)
        for agent in convert_agents(paths.dist_root)
    }
    if set(configured_agents) != expected_names:
        raise ProjectRuntimeError("Codex project layer omitted generated custom agents")
    for name, value in configured_agents.items():
        binding = _as_mapping(value)
        agent_path = paths.codex_home / _required_string(
            binding,
            CONFIG_FILE_KEY,
        )
        if not agent_path.is_file():
            raise ProjectRuntimeError(f"custom agent file is missing for {name!r}")
        with agent_path.open("rb") as stream:
            tomllib.load(stream)


def _response_result(
    responses: Mapping[RequestId, Mapping[str, object]],
    response_id: RequestId,
) -> Mapping[str, object]:
    response = responses.get(response_id)
    if response is None:
        raise ProjectRuntimeError(
            f"Codex returned no response for request {response_id}; "
            f"received request ids {sorted(responses)}"
        )
    return _required_mapping(response, Field.RESULT)


def _resolved_path(values: Mapping[str, object], key: str) -> Path:
    return Path(_required_string(values, key)).resolve()


def _required_string(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ProjectRuntimeError(f"Codex response field {key!r} is not a string")
    return value


def _required_mapping(
    values: Mapping[str, object],
    key: str,
) -> Mapping[str, object]:
    return _as_mapping(values.get(key))


def _as_mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ProjectRuntimeError("Codex response field is not an object")
    return cast(Mapping[str, object], value)


def _required_array(
    values: Mapping[str, object],
    key: str,
) -> tuple[object, ...]:
    value = values.get(key)
    if not isinstance(value, list):
        raise ProjectRuntimeError(f"Codex response field {key!r} is not an array")
    return tuple(value)


def _mapping_array(
    values: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, object], ...]:
    return tuple(_as_mapping(item) for item in _required_array(values, key))


def _single_mapping(
    values: Iterable[Mapping[str, object]],
) -> Mapping[str, object]:
    items = tuple(values)
    if len(items) != 1:
        raise ProjectRuntimeError(
            f"expected one Codex response entry, found {len(items)}"
        )
    return items[0]


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
