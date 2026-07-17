"""Infrastructure for the pickup claim verifier's ``l1`` evidence.

The harness loads the shipped standalone script, arranges source-owned
claim/relation pairs, runs real git operations in temporary repositories, and
uses an injected recording runner only for failure simulation, contract probes,
interaction protocols, and hidden-call observability. Synthetic identifiers are
generated per invocation; production vocabulary comes from the loaded script.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import pathlib
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from types import ModuleType
from typing import Protocol

from outcomeeng_testing.generators.sessions import (
    generated_number,
    generated_relative_path,
    generated_sha,
    generated_token,
)
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


class ClaimHarnessError(RuntimeError):
    """Report an invalid source contract or ambiguous harness observation."""


@dataclass(frozen=True)
class ClaimMappingObservation:
    """Actual product output for one source-owned claim-kind/relation pair."""

    kind: object
    relation: object
    actual: ClaimVerdictLike


@dataclass(frozen=True)
class BranchReferenceObservation:
    """Actual product output for one generated origin-branch condition."""

    git_ref: str
    present_on_origin: bool
    actual: ClaimVerdictLike


@dataclass(frozen=True)
class ObservedStateObservation:
    """Generated live values and the product outputs that surfaced them."""

    node_state: str
    node: ClaimVerdictLike
    external_state: str
    external: ClaimVerdictLike


@dataclass(frozen=True)
class NodeStatusObservation:
    """Raw node-status payload paired with parsed verifier evidence."""

    payload: dict[str, object]
    evidence: object


@dataclass(frozen=True)
class ReadOnlyVerificationObservation:
    """Runner calls and git status observed around one verification pass."""

    calls: tuple[tuple[str, ...], ...]
    status_before: str
    status_after: str


@dataclass(frozen=True)
class MetadataLoadingObservation:
    """Commands and git-ref verdict observed during session loading."""

    session_id: str
    calls: tuple[tuple[str, ...], ...]
    actual: ClaimVerdictLike


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


def claim_mapping_observations() -> tuple[ClaimMappingObservation, ...]:
    """Exercise every source-owned claim-kind/relation pair."""
    module = load_verify_session_claims_module()
    return tuple(
        _exercise_claim_relation(module, kind, relation)
        for kind, relations in module.CLAIM_KIND_RELATIONS.items()
        for relation in relations
    )


def _exercise_claim_relation(
    module: ModuleType, kind: object, relation: object
) -> ClaimMappingObservation:
    with accepted_git_context() as repo:
        session_id = generated_token()
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
            relative_path = generated_relative_path()
            if relation is module.ClaimRelation.MATCHES:
                (repo / relative_path).write_text(generated_token())
            files = (relative_path,)
        elif kind is module.ClaimKind.NODE_STATUS:
            spec = generated_relative_path()
            specs = (spec,)
            scripts = _node_status_arrangement(module, spec, relation)
        elif kind is module.ClaimKind.UNCOMMITTED_STATE:
            git_status = module.GitStatus.CLEAN
            if relation is module.ClaimRelation.DIFFERS:
                (repo / generated_relative_path()).write_text(generated_token())
            elif relation is module.ClaimRelation.UNAVAILABLE:
                scripts = {
                    tuple(module.GIT_STATUS_COMMAND): (
                        module.COMMAND_UNAVAILABLE_EXIT,
                        "",
                        generated_token(),
                    )
                }
        elif kind is module.ClaimKind.EXTERNAL_ID:
            number = generated_number()
            pr_numbers = (number,)
            scripts = _external_arrangement(module, relation)
        else:
            raise ClaimHarnessError(f"unhandled claim kind: {kind}")

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
        actual = _observation_for_kind(module.verify(session_id, repo, runner), kind)
        return ClaimMappingObservation(
            kind=kind,
            relation=relation,
            actual=actual,
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
                generated_token(),
            )
        }
    raise ClaimHarnessError(f"unhandled git-ref relation: {relation}")


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
                generated_token(),
            )
        }
    raise ClaimHarnessError(f"unhandled node-status relation: {relation}")


def _external_arrangement(module: ModuleType, relation: object) -> ScriptMap:
    if relation is module.ClaimRelation.OBSERVED:
        return {
            tuple(module.GH_PR_VIEW_COMMAND): (
                0,
                json.dumps({module.GH_PR_STATE_FIELD: generated_token()}),
                "",
            )
        }
    if relation is module.ClaimRelation.UNAVAILABLE:
        return {
            tuple(module.GH_PR_VIEW_COMMAND): (
                module.COMMAND_UNAVAILABLE_EXIT,
                "",
                generated_token(),
            )
        }
    raise ClaimHarnessError(f"unhandled external-id relation: {relation}")


def branch_reference_observations() -> tuple[BranchReferenceObservation, ...]:
    """Exercise normal, hex-like, full-hex, and absent origin branch refs."""
    module = load_verify_session_claims_module()
    observations: list[BranchReferenceObservation] = []
    with handoff_git_env() as env:
        branch_names = (
            env.push_work_branch(),
            env.push_work_branch(env.head_sha()[:7]),
            env.push_work_branch(env.head_sha()),
        )
        for branch in branch_names:
            observations.append(
                _git_ref_observation(
                    module,
                    env.root,
                    branch,
                    present_on_origin=True,
                )
            )
        absent_branch = f"{env.default_branch}-{generated_token()}"
        observations.append(
            _git_ref_observation(
                module,
                env.root,
                absent_branch,
                present_on_origin=False,
            )
        )
    return tuple(observations)


def _git_ref_observation(
    module: ModuleType,
    repo: pathlib.Path,
    git_ref: str,
    *,
    present_on_origin: bool,
) -> BranchReferenceObservation:
    session_id = generated_token()
    runner = RecordingRunner(
        repo=repo,
        scripted=_session_command_scripts(module, session_id, git_ref=git_ref),
    )
    actual = _observation_for_kind(
        module.verify(session_id, repo, runner), module.ClaimKind.GIT_REF
    )
    return BranchReferenceObservation(
        git_ref=git_ref,
        present_on_origin=present_on_origin,
        actual=actual,
    )


def observed_state_observation() -> ObservedStateObservation:
    """Return generated current values and their emitted evidence strings."""
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        session_id = generated_token()
        spec = generated_relative_path()
        number = generated_number()
        node_state = generated_token()
        external_state = generated_token()
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
        node = _observation_for_kind(verdicts, module.ClaimKind.NODE_STATUS)
        external = _observation_for_kind(verdicts, module.ClaimKind.EXTERNAL_ID)
        return ObservedStateObservation(
            node_state=node_state,
            node=node,
            external_state=external_state,
            external=external,
        )


def node_status_observation() -> NodeStatusObservation:
    """Return a nested status payload and the verifier's parsed evidence."""
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        session_id = generated_token()
        spec = generated_relative_path()
        status = generated_token()
        payload = _node_status_payload(module, spec, status=status)
        generated_child_key = generated_token()
        generated_non_scalar_key = generated_token()
        payload[generated_child_key] = [{generated_token(): generated_token()}]
        payload[generated_non_scalar_key] = {generated_token(): generated_token()}
        scripts = _session_command_scripts(module, session_id, specs=(spec,)) | {
            tuple(module.SPX_SPEC_STATUS_COMMAND): (0, json.dumps(payload), "")
        }
        actual = _observation_for_kind(
            module.verify(
                session_id, repo, RecordingRunner(repo=repo, scripted=scripts)
            ),
            module.ClaimKind.NODE_STATUS,
        )
        return NodeStatusObservation(
            payload=payload,
            evidence=json.loads(actual.evidence),
        )


def verify_parameters() -> tuple[inspect.Parameter, ...]:
    """Return the public parameters exposed by ``verify``."""
    module = load_verify_session_claims_module()
    return tuple(inspect.signature(module.verify).parameters.values())


def script_import_roots() -> frozenset[str]:
    """Return every top-level import root used by the shipped script."""
    tree = ast.parse(VERIFY_MODULE_PATH.read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    return frozenset(roots)


def subprocess_call_owners() -> tuple[tuple[str, str] | None, ...]:
    """Return the enclosing class and method for direct subprocess calls."""
    tree = ast.parse(VERIFY_MODULE_PATH.read_text())
    return tuple(
        _enclosing_method(tree, node)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == subprocess.__name__
    )


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


def default_runner_failure_observations() -> tuple[ClaimVerdictLike, ...]:
    """Return verdicts observed when the default runner cannot launch commands."""
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        return tuple(
            module.verify(
                generated_token(),
                repo,
                module.SubprocessRunner(repo, env={"PATH": ""}),
            )
        )


def read_only_verification_observation() -> ReadOnlyVerificationObservation:
    """Return runner calls and repository status around one verification pass."""
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        session_id = generated_token()
        spec = generated_relative_path()
        number = generated_number()
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
                json.dumps({module.GH_PR_STATE_FIELD: generated_token()}),
                "",
            ),
        }
        runner = RecordingRunner(repo=repo, scripted=scripts)
        module.verify(session_id, repo, runner)
        return ReadOnlyVerificationObservation(
            calls=tuple(tuple(call) for call in runner.calls),
            status_before=before,
            status_after=_git_status(repo),
        )


def metadata_loading_observation() -> MetadataLoadingObservation:
    """Return session-loading calls and the resulting git-ref verdict."""
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        session_id = generated_token()
        runner = RecordingRunner(
            repo=repo,
            scripted=_session_command_scripts(
                module, session_id, git_ref=_head_sha(repo)
            ),
        )
        actual = _observation_for_kind(
            module.verify(session_id, repo, runner), module.ClaimKind.GIT_REF
        )
        return MetadataLoadingObservation(
            session_id=session_id,
            calls=tuple(tuple(call) for call in runner.calls),
            actual=actual,
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
            generated_token(),
        )
    }


def _session_show_json_command(module: ModuleType, session_id: str) -> list[str]:
    return [
        *module.SPX_SESSION_SHOW_COMMAND,
        module.SPX_SESSION_SHOW_JSON_FLAG,
        session_id,
    ]


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
        fields[3]: status if status is not None else generated_token(),
        fields[4]: generated_token(),
        fields[5]: True,
    }


def _node_status_json(
    module: ModuleType, spec: str, *, status: str | None = None
) -> str:
    return json.dumps(_node_status_payload(module, spec, status=status))


def _observation_for_kind(
    verdicts: Iterable[ClaimVerdictLike], kind: object
) -> ClaimVerdictLike:
    matching = [item for item in verdicts if item.kind == kind]
    if len(matching) != 1:
        raise ClaimHarnessError(f"expected one {kind} verdict, observed: {matching}")
    return matching[0]


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
        candidate = generated_sha()
        if candidate != current:
            return candidate


__all__ = [
    "BranchReferenceObservation",
    "ClaimHarnessError",
    "ClaimMappingObservation",
    "MetadataLoadingObservation",
    "NodeStatusObservation",
    "ObservedStateObservation",
    "ReadOnlyVerificationObservation",
    "RecordingRunner",
    "branch_reference_observations",
    "claim_mapping_observations",
    "default_runner_failure_observations",
    "load_verify_session_claims_module",
    "metadata_loading_observation",
    "node_status_observation",
    "observed_state_observation",
    "read_only_verification_observation",
    "script_import_roots",
    "subprocess_call_owners",
    "verify_parameters",
]
