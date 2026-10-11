"""Drive an assertion-audit run through the pinned published SPX release.

The payload objects and the selectors come from the ``/audit-assertions`` skill
text itself, rendered with the run's own values, so the observations describe the
shape the skill states. The harness returns exit statuses and the CLI's own
reports; the linked tests decide what they mean.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, cast

from outcomeeng.validation.assertion_audit_contract import (
    ASSERTION_AUDIT_SKILL_NAME,
    ASSERTION_AUDITOR_AGENT_NAME,
    assertion_audit_unit_key,
)
from outcomeeng.validation.implementation_audit_contract import (
    RUN_TOKEN_FIELD,
    AuditTerminalStatus,
)
from outcomeeng.validation.spx_version import (
    REQUIRED_SPX_VERSION,
    SPX_PACKAGE_NAME,
    minimum_release_package_command,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
SKILL_PATH: Final = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "audit-assertions"
    / "SKILL.md"
)
PLUGIN_MANIFEST_PATH: Final = (
    REPO_ROOT / "src" / "plugins" / "spec-tree" / ".claude-plugin" / "plugin.json"
)
NODE_SPEC_PATH: Final = (
    "spx/21-spec-tree.enabler/68-audit.enabler/"
    "32-audit-assertions.enabler/audit-assertions.md"
)

DESIGNATOR: Final = "ordinal-1"
FINDING_RULE: Final = "subject-unnamed"
FINDING_SEVERITY: Final = "blocking"
FINDING_MESSAGE: Final = "the assertion names no identifiable subject"
FINDING_OBSERVED: Final = "no subject named"
FINDING_EXPECTED: Final = "a named subject"

_RUN_DRIVER: Final = {
    "producerKind": "agent",
    "agentName": ASSERTION_AUDITOR_AGENT_NAME,
    "agentOwningPluginName": "spec-tree",
    "skillName": ASSERTION_AUDIT_SKILL_NAME,
    "skillOwningPluginName": "spec-tree",
    "invocationRole": "run-driver",
}
_JSON_BLOCK: Final = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
_START_SELECTORS: Final = re.compile(
    r"spx verification run start (--verification-type \S+ --scope-type \S+) --scope <path>"
)
_PLACEHOLDER: Final = re.compile(r"<([^<>]+)>")
_EXPECTED_PRODUCER_PLACEHOLDER: Final = (
    "the unit's expectedProducer object, repeated exactly"
)


@dataclass(frozen=True)
class SpxResult:
    """One SPX invocation's exit status and last JSON line."""

    exit_status: int
    report: Mapping[str, object] | None


@dataclass(frozen=True)
class ScopeUnitRecording:
    """One scope unit rendered from the skill and recorded on a started run."""

    unit_key: str
    scope_add: SpxResult
    rendered_scope_units: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class SealedRunObservation:
    """One unit and one finding recorded, the run finished, and the projection read."""

    unit_key: str
    scope_add: SpxResult
    finding_add: SpxResult
    finish: SpxResult
    rendered_scope_units: tuple[Mapping[str, object], ...]


def observe_scope_unit_recording() -> ScopeUnitRecording:
    """Record one scope unit rendered from the skill's payload on a started run."""
    with TemporaryDirectory() as temporary_directory:
        context = _start_run(Path(temporary_directory))
        scope_add = _add_scope_unit(context)
        rendered = _render_scope_units(context)
    return ScopeUnitRecording(
        unit_key=context.unit_key,
        scope_add=scope_add,
        rendered_scope_units=rendered,
    )


def observe_sealed_run_with_finding() -> SealedRunObservation:
    """Record one unit and one finding rendered from the skill, then finish the run."""
    with TemporaryDirectory() as temporary_directory:
        context = _start_run(Path(temporary_directory))
        scope_add = _add_scope_unit(context)
        finding_add = _add_finding(context)
        finish = _spx(
            context,
            ("finish",),
            ("--terminal-status", AuditTerminalStatus.REJECTED.value),
        )
        rendered = _render_scope_units(context)
    return SealedRunObservation(
        unit_key=context.unit_key,
        scope_add=scope_add,
        finding_add=finding_add,
        finish=finish,
        rendered_scope_units=rendered,
    )


@dataclass(frozen=True)
class _RunContext:
    repository: Path
    spx_command: tuple[str, ...]
    selectors: tuple[str, ...]
    run_token: str
    unit_key: str
    bindings: Mapping[str, str]
    scope_template: Mapping[str, object]
    finding_template: Mapping[str, object]
    scope_payload: Mapping[str, object]


def _start_run(repository: Path) -> _RunContext:
    skill_text = SKILL_PATH.read_text(encoding="utf-8")
    scope_template, finding_template = _payload_templates(skill_text)
    selectors = _selectors(skill_text)
    spec_file = repository / NODE_SPEC_PATH
    spec_file.parent.mkdir(parents=True)
    spec_file.write_text(
        (REPO_ROOT / NODE_SPEC_PATH).read_text(encoding="utf-8"), encoding="utf-8"
    )
    unit_key = assertion_audit_unit_key(DESIGNATOR, NODE_SPEC_PATH)
    bindings = _bindings(unit_key)
    scope_payload = cast(Mapping[str, object], _render(scope_template, bindings))
    spx_command = _floor_release_command()
    started = _run_spx(
        repository,
        (*spx_command, "verification", "run", "start", *selectors),
        ("--input", NODE_SPEC_PATH),
    )
    if started.report is None or started.exit_status != 0:
        raise RuntimeError("the run could not start on the pinned SPX release")
    run_token = started.report.get(RUN_TOKEN_FIELD)
    if not isinstance(run_token, str):
        raise RuntimeError("the started run returned no run token")
    return _RunContext(
        repository=repository,
        spx_command=spx_command,
        selectors=selectors,
        run_token=run_token,
        unit_key=unit_key,
        bindings=bindings,
        scope_template=scope_template,
        finding_template=finding_template,
        scope_payload=scope_payload,
    )


def _add_scope_unit(context: _RunContext) -> SpxResult:
    return _spx(
        context,
        ("scope", "add"),
        ("--payload", "stdin", "--idempotency-key", context.unit_key),
        payload=context.scope_payload,
    )


def _add_finding(context: _RunContext) -> SpxResult:
    bindings = {
        **context.bindings,
        _EXPECTED_PRODUCER_PLACEHOLDER: "",
    }
    finding = cast(dict[str, object], _render(context.finding_template, bindings))
    finding["producerIdentity"] = context.scope_payload["expectedProducer"]
    return _spx(
        context,
        ("finding", "add"),
        (
            "--payload",
            "stdin",
            "--idempotency-key",
            f"{context.unit_key}:{FINDING_RULE}",
        ),
        payload=finding,
    )


def _render_scope_units(context: _RunContext) -> tuple[Mapping[str, object], ...]:
    rendered = _spx(context, ("render",), ())
    units = (rendered.report or {}).get("auditScopeUnits", [])
    return tuple(cast(Mapping[str, object], unit) for unit in cast(list[object], units))


def _spx(
    context: _RunContext,
    action: tuple[str, ...],
    options: tuple[str, ...],
    *,
    payload: Mapping[str, object] | None = None,
) -> SpxResult:
    return _run_spx(
        context.repository,
        (*context.spx_command, "verification", "run", *action, *context.selectors),
        ("--run", context.run_token, *options),
        payload=payload,
    )


def _run_spx(
    repository: Path,
    command: tuple[str, ...],
    options: Sequence[str],
    *,
    payload: Mapping[str, object] | None = None,
) -> SpxResult:
    input_text = None if payload is None else f"{json.dumps(payload)}\n"
    finished = subprocess.run(
        (*command, *options),
        cwd=repository,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    lines = [line for line in finished.stdout.splitlines() if line.strip()]
    report: Mapping[str, object] | None = None
    if lines:
        parsed = cast(object, json.loads(lines[-1]))
        if isinstance(parsed, dict):
            report = cast(dict[str, object], parsed)
    return SpxResult(exit_status=finished.returncode, report=report)


def _payload_templates(
    skill_text: str,
) -> tuple[Mapping[str, object], Mapping[str, object]]:
    section = skill_text.split("<persistence_contract>")[1].split(
        "</persistence_contract>"
    )[0]
    blocks = [
        cast(dict[str, object], json.loads(block))
        for block in _JSON_BLOCK.findall(section)
    ]
    scope = next(block for block in blocks if "auditClass" in block)
    finding = next(block for block in blocks if "producerIdentity" in block)
    return scope, finding


def _selectors(skill_text: str) -> tuple[str, ...]:
    match = _START_SELECTORS.search(skill_text)
    if match is None:
        raise RuntimeError("the skill states no run start command")
    return (*match.group(1).split(), "--scope", NODE_SPEC_PATH)


def _bindings(unit_key: str) -> Mapping[str, str]:
    return {
        "unit-key": unit_key,
        "accepted-unit-key": unit_key,
        "path": NODE_SPEC_PATH,
        "designator": DESIGNATOR,
        "subject-path-and-line-or-section": f"{NODE_SPEC_PATH}:1",
        "violated-rule-id": FINDING_RULE,
        "blocking-or-debt": FINDING_SEVERITY,
        "finding-message": FINDING_MESSAGE,
        "observed-state": FINDING_OBSERVED,
        "state the assertion requires": FINDING_EXPECTED,
        **{f"runDriver.{field}": value for field, value in _RUN_DRIVER.items()},
        **_provenance_bindings(),
    }


def _provenance_bindings() -> Mapping[str, str]:
    manifest = cast(
        dict[str, object],
        json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8")),
    )
    version = manifest["version"]
    if not isinstance(version, str):
        raise TypeError("plugin manifest carries no version string")
    return {"spec-tree-plugin-version": version}


def _render(value: object, bindings: Mapping[str, str]) -> object:
    if isinstance(value, str):
        return _PLACEHOLDER.sub(lambda match: bindings[match.group(1)], value)
    if isinstance(value, dict):
        return {key: _render(item, bindings) for key, item in value.items()}
    if isinstance(value, list):
        return [_render(item, bindings) for item in value]
    return value


def _floor_release_command() -> tuple[str, ...]:
    package_spec = f"{SPX_PACKAGE_NAME}@{REQUIRED_SPX_VERSION}"
    command = minimum_release_package_command(package_spec)
    version = subprocess.run(
        (*command, "--version"),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    if version != REQUIRED_SPX_VERSION:
        raise RuntimeError(
            f"floor release command returned {version}, expected {REQUIRED_SPX_VERSION}"
        )
    return command
