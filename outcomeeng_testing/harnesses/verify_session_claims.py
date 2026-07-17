"""Infrastructure for the pickup claim verifier's ``l1`` evidence.

The harness loads the shipped standalone script, arranges source-owned
claim/relation pairs, runs real git operations in temporary repositories, and
uses an injected recording runner only for failure simulation, contract probes,
interaction protocols, and hidden-call observability. Synthetic identifiers are
generated per invocation; production vocabulary comes from the loaded script.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import pathlib
import subprocess
import sys
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from types import ModuleType
from typing import Protocol

from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
    handoff_git_env,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
VERIFY_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "pickup"
    / "scripts"
    / "verify_session_claims.py"
)

type ScriptMap = dict[tuple[str, ...], tuple[int, str, str]]


class ClaimVerdictLike(Protocol):
    kind: object
    subject: str
    verdict: object
    evidence: str


@dataclass(frozen=True)
class MappingEvidence:
    """Observed verdict paired with its source-owned expected relation."""

    kind: object
    relation: object
    actual: object
    expected: object


@dataclass
class RecordingRunner:
    """Run git for real, script unavailable dependencies, and record calls."""

    repo: pathlib.Path
    scripted: ScriptMap = field(default_factory=dict)
    calls: list[list[str]] = field(default_factory=list)

    def run(self, cmd: list[str]) -> tuple[int, str, str]:
        self.calls.append(list(cmd))
        command = tuple(cmd)
        for prefix, response in self.scripted.items():
            if command == prefix or command[: len(prefix)] == prefix:
                return response
        if cmd and cmd[0] == "git":
            proc = subprocess.run(cmd, cwd=self.repo, capture_output=True, text=True)
            return proc.returncode, proc.stdout, proc.stderr
        return (1, "", f"unconfigured command: {' '.join(cmd)}")


def load_verify_session_claims_module() -> ModuleType:
    """Load the shipped verifier from its hyphenated skill path."""
    cached = sys.modules.get("verify_session_claims")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "verify_session_claims", VERIFY_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load verify_session_claims from {VERIFY_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_session_claims"] = module
    spec.loader.exec_module(module)
    return module


def claim_mapping_evidence() -> tuple[MappingEvidence, ...]:
    """Exercise every source-owned claim-kind/relation pair."""
    module = load_verify_session_claims_module()
    return tuple(
        _exercise_claim_relation(module, kind, relation)
        for kind, relations in module.CLAIM_KIND_RELATIONS.items()
        for relation in relations
    )


def claim_mappings_hold() -> bool:
    """Check every source-owned claim-kind/relation pair in one entrypoint."""
    return all(
        evidence.actual is evidence.expected for evidence in claim_mapping_evidence()
    )


def _exercise_claim_relation(
    module: ModuleType, kind: object, relation: object
) -> MappingEvidence:
    with accepted_git_context() as repo:
        session_id = _generated_token()
        git_ref: str | None = None
        git_status: str | None = None
        specs: tuple[str, ...] = ()
        files: tuple[str, ...] = ()
        pr_numbers: tuple[str, ...] = ()
        scripts: ScriptMap = {}

        if kind is module.ClaimKind.SESSION_METADATA:
            scripts = _metadata_failure_script(module, session_id)
        elif kind is module.ClaimKind.GIT_REF:
            git_ref, scripts = _git_ref_arrangement(module, repo, relation)
        elif kind is module.ClaimKind.INJECTED_PATH:
            relative_path = _generated_relative_path()
            if relation is module.ClaimRelation.MATCHES:
                (repo / relative_path).write_text(_generated_token())
            files = (relative_path,)
        elif kind is module.ClaimKind.NODE_STATUS:
            spec = _generated_relative_path()
            specs = (spec,)
            scripts = _node_status_arrangement(module, spec, relation)
        elif kind is module.ClaimKind.UNCOMMITTED_STATE:
            git_status = module.GitStatus.CLEAN
            if relation is module.ClaimRelation.DIFFERS:
                (repo / _generated_relative_path()).write_text(_generated_token())
            elif relation is module.ClaimRelation.UNAVAILABLE:
                scripts = {
                    tuple(module.GIT_STATUS_COMMAND): (
                        module.COMMAND_UNAVAILABLE_EXIT,
                        "",
                        _generated_token(),
                    )
                }
        elif kind is module.ClaimKind.EXTERNAL_ID:
            number = _generated_number()
            pr_numbers = (number,)
            scripts = _external_arrangement(module, relation)
        else:
            raise AssertionError(f"unhandled claim kind: {kind}")

        scripts = (
            _session_command_scripts(
                module,
                session_id,
                git_ref=git_ref,
                git_status=git_status,
                specs=specs,
                files=files,
                pr_numbers=pr_numbers,
            )
            | scripts
        )
        runner = RecordingRunner(repo=repo, scripted=scripts)
        verdict = _verdict_for_kind(module.verify(session_id, repo, runner), kind)
        return MappingEvidence(
            kind=kind,
            relation=relation,
            actual=verdict.verdict,
            expected=module.verdict_for_relation(relation),
        )


def _git_ref_arrangement(
    module: ModuleType, repo: pathlib.Path, relation: object
) -> tuple[str, ScriptMap]:
    if relation is module.ClaimRelation.MATCHES:
        return _head_sha(repo), {}
    if relation is module.ClaimRelation.DIFFERS:
        return _unreachable_sha(repo), {}
    if relation is module.ClaimRelation.UNAVAILABLE:
        return _head_sha(repo), {
            tuple(module.GIT_VERIFY_REF_COMMAND): (
                module.COMMAND_UNAVAILABLE_EXIT,
                "",
                _generated_token(),
            )
        }
    raise AssertionError(f"unhandled git-ref relation: {relation}")


def _node_status_arrangement(
    module: ModuleType, spec: str, relation: object
) -> ScriptMap:
    if relation is module.ClaimRelation.OBSERVED:
        return {
            tuple(module.SPX_SPEC_STATUS_COMMAND): (
                0,
                _node_status_json(module, spec),
                "",
            )
        }
    if relation is module.ClaimRelation.UNAVAILABLE:
        return {
            tuple(module.SPX_SPEC_STATUS_COMMAND): (
                module.COMMAND_UNAVAILABLE_EXIT,
                "",
                _generated_token(),
            )
        }
    raise AssertionError(f"unhandled node-status relation: {relation}")


def _external_arrangement(module: ModuleType, relation: object) -> ScriptMap:
    if relation is module.ClaimRelation.OBSERVED:
        return {
            tuple(module.GH_PR_VIEW_COMMAND): (
                0,
                json.dumps({module.GH_PR_STATE_FIELD: _generated_token()}),
                "",
            )
        }
    if relation is module.ClaimRelation.UNAVAILABLE:
        return {
            tuple(module.GH_PR_VIEW_COMMAND): (
                module.COMMAND_UNAVAILABLE_EXIT,
                "",
                _generated_token(),
            )
        }
    raise AssertionError(f"unhandled external-id relation: {relation}")


def branch_reference_evidence() -> tuple[MappingEvidence, ...]:
    """Exercise normal, hex-like, full-hex, and absent origin branch refs."""
    module = load_verify_session_claims_module()
    evidence: list[MappingEvidence] = []
    with handoff_git_env() as env:
        branch_names = (
            env.push_work_branch(),
            env.push_work_branch(env.head_sha()[:7]),
            env.push_work_branch(env.head_sha()),
        )
        for branch in branch_names:
            evidence.append(
                _git_ref_evidence(
                    module, env.root, branch, module.ClaimRelation.MATCHES
                )
            )
        absent_branch = f"{env.default_branch}-{_generated_token()}"
        evidence.append(
            _git_ref_evidence(
                module, env.root, absent_branch, module.ClaimRelation.DIFFERS
            )
        )
    return tuple(evidence)


def branch_reference_mappings_hold() -> bool:
    """Check normal and hex-shaped origin branch reachability mappings."""
    return all(
        evidence.actual is evidence.expected for evidence in branch_reference_evidence()
    )


def _git_ref_evidence(
    module: ModuleType,
    repo: pathlib.Path,
    git_ref: str,
    relation: object,
) -> MappingEvidence:
    session_id = _generated_token()
    runner = RecordingRunner(
        repo=repo,
        scripted=_session_command_scripts(module, session_id, git_ref=git_ref),
    )
    verdict = _verdict_for_kind(
        module.verify(session_id, repo, runner), module.ClaimKind.GIT_REF
    )
    return MappingEvidence(
        kind=module.ClaimKind.GIT_REF,
        relation=relation,
        actual=verdict.verdict,
        expected=module.verdict_for_relation(relation),
    )


def observed_state_is_surfaced() -> bool:
    """Check that node and external observations retain generated current values."""
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        session_id = _generated_token()
        spec = _generated_relative_path()
        number = _generated_number()
        node_state = _generated_token()
        external_state = _generated_token()
        scripts = _session_command_scripts(
            module,
            session_id,
            specs=(spec,),
            pr_numbers=(number,),
        ) | {
            tuple(module.SPX_SPEC_STATUS_COMMAND): (
                0,
                _node_status_json(module, spec, status=node_state),
                "",
            ),
            tuple(module.GH_PR_VIEW_COMMAND): (
                0,
                json.dumps({module.GH_PR_STATE_FIELD: external_state}),
                "",
            ),
        }
        verdicts = module.verify(
            session_id, repo, RecordingRunner(repo=repo, scripted=scripts)
        )
        node = _verdict_for_kind(verdicts, module.ClaimKind.NODE_STATUS)
        external = _verdict_for_kind(verdicts, module.ClaimKind.EXTERNAL_ID)
        return node_state in node.evidence and external_state in external.evidence


def node_status_keeps_source_scalar_fields_only() -> bool:
    """Check that child and non-scalar data stay outside status evidence."""
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        session_id = _generated_token()
        spec = _generated_relative_path()
        status = _generated_token()
        payload = _node_status_payload(module, spec, status=status)
        generated_child_key = _generated_token()
        generated_non_scalar_key = _generated_token()
        payload[generated_child_key] = [{_generated_token(): _generated_token()}]
        payload[generated_non_scalar_key] = {_generated_token(): _generated_token()}
        scripts = _session_command_scripts(module, session_id, specs=(spec,)) | {
            tuple(module.SPX_SPEC_STATUS_COMMAND): (0, json.dumps(payload), "")
        }
        verdict = _verdict_for_kind(
            module.verify(
                session_id, repo, RecordingRunner(repo=repo, scripted=scripts)
            ),
            module.ClaimKind.NODE_STATUS,
        )
        evidence = json.loads(verdict.evidence)
        expected = {
            key: payload[key]
            for key in module.NODE_STATUS_SCALAR_FIELDS
            if key in payload
        }
        return isinstance(evidence, dict) and evidence == expected


def verify_accepts_injected_runner() -> bool:
    """Check that ``verify`` exposes a parameter typed as ``CommandRunner``."""
    module = load_verify_session_claims_module()
    return any(
        parameter.annotation in {"CommandRunner", module.CommandRunner}
        for parameter in inspect.signature(module.verify).parameters.values()
    )


def script_imports_are_stdlib_only() -> bool:
    tree = ast.parse(VERIFY_MODULE_PATH.read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    return not (roots - (sys.stdlib_module_names | {"__future__"}))


def external_calls_go_through_runner() -> bool:
    """Check that direct subprocess calls stay inside the source runner adapter."""
    module = load_verify_session_claims_module()
    tree = ast.parse(VERIFY_MODULE_PATH.read_text())
    owners = [
        _enclosing_method(tree, node)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == subprocess.__name__
    ]
    expected_owner = (
        module.SubprocessRunner.__name__,
        module.SubprocessRunner.run.__name__,
    )
    return bool(owners) and all(owner == expected_owner for owner in owners)


def _enclosing_method(tree: ast.AST, target: ast.AST) -> tuple[str, str] | None:
    for class_node in ast.walk(tree):
        if not isinstance(class_node, ast.ClassDef):
            continue
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and any(
                child is target for child in ast.walk(node)
            ):
                return class_node.name, node.name
    return None


def default_runner_failure_is_unverifiable() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        verdicts = module.verify(
            _generated_token(),
            repo,
            module.SubprocessRunner(repo, env={"PATH": ""}),
        )
        expected = module.verdict_for_relation(module.ClaimRelation.UNAVAILABLE)
        return (
            len(verdicts) == 1
            and verdicts[0].kind is module.ClaimKind.SESSION_METADATA
            and verdicts[0].verdict is expected
        )


def verification_is_read_only_and_uses_source_commands() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        session_id = _generated_token()
        spec = _generated_relative_path()
        number = _generated_number()
        before = _git_status(repo)
        scripts = _session_command_scripts(
            module,
            session_id,
            git_ref=_unreachable_sha(repo),
            git_status=module.GitStatus.CLEAN,
            specs=(spec,),
            pr_numbers=(number,),
        ) | {
            tuple(module.SPX_SPEC_STATUS_COMMAND): (
                0,
                _node_status_json(module, spec),
                "",
            ),
            tuple(module.GH_PR_VIEW_COMMAND): (
                0,
                json.dumps({module.GH_PR_STATE_FIELD: _generated_token()}),
                "",
            ),
        }
        runner = RecordingRunner(repo=repo, scripted=scripts)
        module.verify(session_id, repo, runner)
        return (
            not _unexpected_runner_calls(module, runner.calls)
            and _git_status(repo) == before
        )


def metadata_loading_uses_structured_session_api() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        session_id = _generated_token()
        runner = RecordingRunner(
            repo=repo,
            scripted=_session_command_scripts(
                module, session_id, git_ref=_head_sha(repo)
            ),
        )
        verdict = _verdict_for_kind(
            module.verify(session_id, repo, runner), module.ClaimKind.GIT_REF
        )
        commands = tuple(tuple(call) for call in runner.calls)
        return (
            tuple(_session_show_json_command(module, session_id)) in commands
            and tuple(_session_show_command(module, session_id)) in commands
            and verdict.verdict
            is module.verdict_for_relation(module.ClaimRelation.MATCHES)
        )


def _session_command_scripts(
    module: ModuleType,
    session_id: str,
    *,
    git_ref: str | None = None,
    git_status: str | None = None,
    specs: tuple[str, ...] = (),
    files: tuple[str, ...] = (),
    pr_numbers: tuple[str, ...] = (),
) -> ScriptMap:
    record = {
        module.SESSION_GIT_REF_FIELD: git_ref,
        module.SESSION_SPECS_FIELD: list(specs),
        module.SESSION_FILES_FIELD: list(files),
    }
    body: list[str] = []
    if git_status is not None:
        body.append(f"{module.SESSION_GIT_STATUS_LABEL}: {git_status}")
    body.extend(f"{module.PR_REFERENCE_PREFIXES[0]} #{number}" for number in pr_numbers)
    return {
        tuple(_session_show_json_command(module, session_id)): (
            0,
            json.dumps(record),
            "",
        ),
        tuple(_session_show_command(module, session_id)): (0, "\n".join(body), ""),
    }


def _metadata_failure_script(module: ModuleType, session_id: str) -> ScriptMap:
    return {
        tuple(_session_show_json_command(module, session_id)): (
            module.COMMAND_UNAVAILABLE_EXIT,
            "",
            _generated_token(),
        )
    }


def _session_show_json_command(module: ModuleType, session_id: str) -> list[str]:
    return [*module.SPX_SESSION_SHOW_COMMAND, "--json", session_id]


def _session_show_command(module: ModuleType, session_id: str) -> list[str]:
    return [*module.SPX_SESSION_SHOW_COMMAND, session_id]


def _node_status_payload(
    module: ModuleType, spec: str, *, status: str | None = None
) -> dict[str, object]:
    fields = tuple(module.NODE_STATUS_SCALAR_FIELDS)
    return {
        fields[0]: str(pathlib.PurePosixPath(spec).parent),
        fields[1]: spec,
        fields[2]: spec,
        fields[3]: status if status is not None else _generated_token(),
        fields[4]: _generated_token(),
        fields[5]: True,
    }


def _node_status_json(
    module: ModuleType, spec: str, *, status: str | None = None
) -> str:
    return json.dumps(_node_status_payload(module, spec, status=status))


def _verdict_for_kind(
    verdicts: Iterable[ClaimVerdictLike], kind: object
) -> ClaimVerdictLike:
    matching = [item for item in verdicts if item.kind == kind]
    if len(matching) != 1:
        raise AssertionError(f"expected one {kind} verdict: {matching}")
    return matching[0]


def _unexpected_runner_calls(
    module: ModuleType, calls: Iterable[list[str]]
) -> tuple[list[str], ...]:
    prefixes = (
        tuple(module.SPX_SESSION_SHOW_COMMAND),
        tuple(module.SPX_SPEC_STATUS_COMMAND),
        tuple(module.GIT_VERIFY_REF_COMMAND),
        tuple(module.GIT_STATUS_COMMAND),
        tuple(module.GH_PR_VIEW_COMMAND),
    )
    return tuple(
        call
        for call in calls
        if not any(tuple(call[: len(prefix)]) == prefix for prefix in prefixes)
    )


def _head_sha(repo: pathlib.Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _git_status(repo: pathlib.Path) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _unreachable_sha(repo: pathlib.Path) -> str:
    current = _head_sha(repo)
    while True:
        candidate = hashlib.sha1(uuid.uuid4().bytes, usedforsecurity=False).hexdigest()
        if candidate != current:
            return candidate


def _generated_relative_path() -> str:
    return f"{_generated_token()}.md"


def _generated_number() -> str:
    return str(uuid.uuid4().int)


def _generated_token() -> str:
    return uuid.uuid4().hex


__all__ = [
    "MappingEvidence",
    "RecordingRunner",
    "branch_reference_evidence",
    "branch_reference_mappings_hold",
    "claim_mapping_evidence",
    "claim_mappings_hold",
    "default_runner_failure_is_unverifiable",
    "external_calls_go_through_runner",
    "load_verify_session_claims_module",
    "metadata_loading_uses_structured_session_api",
    "node_status_keeps_source_scalar_fields_only",
    "observed_state_is_surfaced",
    "script_imports_are_stdlib_only",
    "verification_is_read_only_and_uses_source_commands",
    "verify_accepts_injected_runner",
]
