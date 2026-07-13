"""Real-Codex evidence for project-scoped plugin and agent resolution."""

from __future__ import annotations

import hashlib
import json
import os
import selectors
import subprocess
import time
import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from functools import cache, partial
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, cast

from outcomeeng.distribution.agents import convert_agents, render_agent_toml
from outcomeeng.distribution.codex_project import (
    CODEX_COMMAND,
    CODEX_HOME_ENV,
    CODEX_MARKETPLACE_RELATIVE_PATH,
    CONFIG_AGENTS_KEY,
    CONFIG_FILE_KEY,
    ENABLED_KEY,
    MARKETPLACE_ROOT_KEY,
    NAME_KEY,
    ProjectRuntimeError,
    ProjectRuntimePaths,
    build_project_runtime,
    project_runtime_paths,
)
from outcomeeng.distribution.marketplace_sources import (
    CODEX_PLUGIN_MANIFEST,
    PLUGIN_MANIFEST_FIELD_VERSION,
)

APP_SERVER_ARGV: Final = (CODEX_COMMAND, "app-server")
APP_SERVER_TIMEOUT_SECONDS: Final = 30
APP_SERVER_STOP_TIMEOUT_SECONDS: Final = 1
APP_SERVER_CLIENT_NAME: Final = "outcomeeng-project-runtime-test"
APP_SERVER_CLIENT_VERSION: Final = "1.0.0"
PROJECT_LAYER_TYPE: Final = "project"
HOME_ENV: Final = "HOME"
USER_CODEX_HOME_RELATIVE_PATH: Final = Path(".codex")
USER_MARKETPLACE_ROOT_RELATIVE_PATH: Final = Path("plugins/marketplaces")
USER_PLUGIN_CACHE_RELATIVE_PATH: Final = Path("plugins/cache")
USER_INSTALLED_VERSION: Final = "0.0.0"


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


@dataclass(frozen=True)
class SkillResolutionObservation:
    """Generated and resolved skill identities reported by Codex."""

    expected_digests: tuple[str, ...]
    resolved_digests: tuple[str, ...]
    errors: tuple[object, ...]


@dataclass(frozen=True)
class AgentResolutionObservation:
    """Generated and configured agent identities reported by Codex."""

    expected_names: tuple[str, ...]
    configured_names: tuple[str, ...]
    parsed_names: tuple[str, ...]
    project_layer_names: tuple[str, ...]
    expected_digests: tuple[str, ...]
    resolved_digests: tuple[str, ...]


@dataclass(frozen=True)
class ProjectCodexRuntimeObservation:
    """Observable checkout-local runtime state from one real Codex process."""

    skills: SkillResolutionObservation
    agents: AgentResolutionObservation
    user_state_before: tuple[tuple[str, str], ...]
    user_state_after: tuple[tuple[str, str], ...]
    generated_plugin_version: str
    seeded_user_plugin_version: str


def observe_project_codex_runtime() -> ProjectCodexRuntimeObservation:
    """Run real Codex and return checkout-local resolution observations."""
    return _observe_project_codex_runtime(Path.cwd().resolve())


@cache
def _observe_project_codex_runtime(
    source_root: Path,
) -> ProjectCodexRuntimeObservation:
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        project_root = temporary_root / "project"
        codex_home = temporary_root / "codex-home"
        user_home = temporary_root / "user-home"
        project_root.mkdir()
        paths = project_runtime_paths(
            project_root,
            source_root=source_root,
            codex_home=codex_home,
        )
        generated_version, seeded_version = _seed_distinct_user_codex_state(
            paths,
            user_home,
        )
        user_state_before = _directory_snapshot(
            user_home / USER_CODEX_HOME_RELATIVE_PATH
        )
        environment_overrides = {HOME_ENV: str(user_home)}
        build_project_runtime(
            project_root,
            source_root=source_root,
            codex_home=codex_home,
            command_runner=partial(
                _run_command,
                environment_overrides=environment_overrides,
            ),
        )
        responses = _run_app_server(paths, environment_overrides)
        return ProjectCodexRuntimeObservation(
            skills=_observe_skill_resolution(responses, paths),
            agents=_observe_agent_resolution(responses, paths),
            user_state_before=user_state_before,
            user_state_after=_directory_snapshot(
                user_home / USER_CODEX_HOME_RELATIVE_PATH
            ),
            generated_plugin_version=generated_version,
            seeded_user_plugin_version=seeded_version,
        )


def generated_skill_files(dist_root: Path) -> tuple[Path, ...]:
    """Return every generated skill entrypoint exposed by the local marketplace."""
    return tuple(sorted(dist_root.glob("*/skills/*/SKILL.md")))


def generated_agent_files(dist_root: Path) -> tuple[Path, ...]:
    """Return every generated custom-agent source exposed by the marketplace."""
    return tuple(sorted(dist_root.glob("*/agents/*.md")))


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
    environment_overrides: Mapping[str, str],
) -> Mapping[RequestId, Mapping[str, object]]:
    environment = {
        **os.environ,
        **environment_overrides,
        CODEX_HOME_ENV: str(paths.codex_home),
    }
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


def _observe_skill_resolution(
    responses: Mapping[RequestId, Mapping[str, object]],
    paths: ProjectRuntimePaths,
) -> SkillResolutionObservation:
    result = _response_result(responses, RequestId.SKILLS_LIST)
    project_entry = _single_mapping(
        entry
        for entry in _mapping_array(result, Field.DATA)
        if _resolved_path(entry, Field.CWD) == paths.project_root
    )
    errors = _required_array(project_entry, Field.ERRORS)
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
    return SkillResolutionObservation(
        expected_digests=tuple(
            _file_digest(path) for path in generated_skill_files(paths.dist_root)
        ),
        resolved_digests=tuple(_file_digest(path) for path in local_skill_files),
        errors=errors,
    )


def _observe_agent_resolution(
    responses: Mapping[RequestId, Mapping[str, object]],
    paths: ProjectRuntimePaths,
) -> AgentResolutionObservation:
    result = _response_result(responses, RequestId.CONFIG_READ)
    project_layer = _single_mapping(
        layer
        for layer in _mapping_array(result, Field.LAYERS)
        if _required_mapping(layer, NAME_KEY).get(Field.TYPE) == PROJECT_LAYER_TYPE
    )
    config = _required_mapping(project_layer, Field.CONFIG)
    project_layer_agents = _optional_mapping(config.get(CONFIG_AGENTS_KEY))
    agent_layer = _single_mapping(
        layer
        for layer in _mapping_array(result, Field.LAYERS)
        if CONFIG_AGENTS_KEY in _required_mapping(layer, Field.CONFIG)
    )
    configured_agents = _required_mapping(
        _required_mapping(agent_layer, Field.CONFIG),
        CONFIG_AGENTS_KEY,
    )
    converted_agents = convert_agents(paths.dist_root)
    expected_names = tuple(
        sorted(_required_string(agent.values, NAME_KEY) for agent in converted_agents)
    )
    parsed_names: list[str] = []
    resolved_digests: list[str] = []
    for name, value in configured_agents.items():
        binding = _as_mapping(value)
        agent_path = paths.codex_home / _required_string(
            binding,
            CONFIG_FILE_KEY,
        )
        with agent_path.open("rb") as stream:
            parsed_names.append(_required_string(tomllib.load(stream), NAME_KEY))
        resolved_digests.append(_file_digest(agent_path))
    return AgentResolutionObservation(
        expected_names=expected_names,
        configured_names=tuple(sorted(configured_agents)),
        parsed_names=tuple(sorted(parsed_names)),
        project_layer_names=tuple(sorted(project_layer_agents)),
        expected_digests=tuple(
            sorted(_text_digest(render_agent_toml(agent)) for agent in converted_agents)
        ),
        resolved_digests=tuple(sorted(resolved_digests)),
    )


def _seed_distinct_user_codex_state(
    paths: ProjectRuntimePaths,
    user_home: Path,
) -> tuple[str, str]:
    user_codex_home = user_home / USER_CODEX_HOME_RELATIVE_PATH
    with (paths.source_root / CODEX_MARKETPLACE_RELATIVE_PATH).open("rb") as stream:
        marketplace = _as_mapping(json.load(stream))
    marketplace_name = _required_string(marketplace, NAME_KEY)
    plugin_manifest = _first_path(paths.dist_root.glob(f"*/{CODEX_PLUGIN_MANIFEST}"))
    with plugin_manifest.open("rb") as stream:
        generated_plugin = _as_mapping(json.load(stream))
    plugin_name = _required_string(generated_plugin, NAME_KEY)
    generated_version = _required_string(
        generated_plugin,
        PLUGIN_MANIFEST_FIELD_VERSION,
    )
    registration_path = (
        user_codex_home
        / USER_MARKETPLACE_ROOT_RELATIVE_PATH
        / marketplace_name
        / "registration.json"
    )
    registration_path.parent.mkdir(parents=True)
    registration_path.write_text(
        json.dumps(
            {
                NAME_KEY: marketplace_name,
                MARKETPLACE_ROOT_KEY: str(paths.source_root),
            }
        ),
        encoding="utf-8",
    )
    cache_manifest = (
        user_codex_home
        / USER_PLUGIN_CACHE_RELATIVE_PATH
        / marketplace_name
        / plugin_name
        / USER_INSTALLED_VERSION
        / CODEX_PLUGIN_MANIFEST
    )
    cache_manifest.parent.mkdir(parents=True)
    cache_manifest.write_text(
        json.dumps(
            {
                NAME_KEY: plugin_name,
                PLUGIN_MANIFEST_FIELD_VERSION: USER_INSTALLED_VERSION,
            }
        ),
        encoding="utf-8",
    )
    return generated_version, USER_INSTALLED_VERSION


def _run_command(
    argv: Iterable[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    environment_overrides: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        tuple(argv),
        cwd=cwd,
        env={**env, **environment_overrides},
        text=True,
        capture_output=True,
        check=False,
    )


def _directory_snapshot(root: Path) -> tuple[tuple[str, str], ...]:
    return tuple(
        (str(path.relative_to(root)), _file_digest(path))
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


def _first_path(paths: Iterable[Path]) -> Path:
    items = tuple(sorted(paths))
    if not items:
        raise ProjectRuntimeError("generated Codex marketplace has no plugin manifest")
    return items[0]


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


def _optional_mapping(value: object) -> Mapping[str, object]:
    if value is None:
        return {}
    return _as_mapping(value)


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


def _text_digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
