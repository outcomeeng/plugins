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
    """Current live values and the product outputs that surfaced them."""

    node_values: tuple[str, ...]
    node: ClaimVerdictLike
    external_state: str
    external: ClaimVerdictLike


@dataclass(frozen=True)
class NodeStatusObservation:
    """A real projection record paired with the verifier's node-status verdict."""

    node_path: str
    projected_record: dict[str, object]
    actual: ClaimVerdictLike


@dataclass(frozen=True)
class AbsentNodeObservation:
    """A node absent from the real projection and the verdict it produced."""

    node_path: str
    actual: ClaimVerdictLike


@dataclass(frozen=True)
class ReadOnlyVerificationObservation:
    """Runner calls and git status observed around one verification pass."""

    calls: tuple[tuple[str, ...], ...]
    status_before: str
    status_after: str


@dataclass(frozen=True)
class UnloadableSessionObservation:
    """One staged session-loading rejection and every verdict it produced."""

    condition: str
    verdicts: tuple[ClaimVerdictLike, ...]


@dataclass(frozen=True)
class SpecEntryObservation:
    """The verdict kinds one recorded spec entry produced."""

    spec_path: str
    kinds: tuple[object, ...]


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
    """Exercise every claim-kind/relation condition this harness can arrange."""
    module = load_verify_session_claims_module()
    return tuple(
        _exercise_claim_relation(module, kind, relation)
        for kind, relations in _arrangeable_claim_conditions(module)
        for relation in relations
    )


def unloadable_session_observations() -> tuple[UnloadableSessionObservation, ...]:
    """Stage every session-loading rejection this harness can arrange."""
    module = load_verify_session_claims_module()
    return tuple(
        _unloadable_observation(module, condition, stdout)
        for condition, stdout in _unloadable_session_payloads(module)
    )


def _unloadable_session_payloads(module: ModuleType) -> tuple[tuple[str, str], ...]:
    """Pair each rejection condition with the stdout that triggers it.

    The conditions are what this harness can stage against a successful
    ``spx session show --json`` call, not a reading of the verifier's own
    rejection branches.
    """
    ref = module.SESSION_GIT_REF_FIELD
    specs = module.SESSION_SPECS_FIELD
    files = module.SESSION_FILES_FIELD
    well_formed: dict[str, object] = {ref: None, specs: [], files: []}
    non_string = len(generated_token())
    return (
        ("unparseable json", "{" + generated_token()),
        ("empty record list", json.dumps([])),
        ("multiple record entries", json.dumps([well_formed, well_formed])),
        ("non-object record entry", json.dumps([generated_token()])),
        ("absent required field", json.dumps({specs: [], files: []})),
        ("non-string git ref", json.dumps(well_formed | {ref: non_string})),
        ("non-list specs", json.dumps(well_formed | {specs: generated_token()})),
        ("non-string path item", json.dumps(well_formed | {files: [non_string]})),
        (
            "absolute path",
            json.dumps(well_formed | {specs: [f"/{generated_relative_path()}"]}),
        ),
        (
            "parent-escaping path",
            json.dumps(well_formed | {files: [f"../{generated_relative_path()}"]}),
        ),
        ("empty path", json.dumps(well_formed | {specs: [""]})),
    )


def _unloadable_observation(
    module: ModuleType, condition: str, stdout: str
) -> UnloadableSessionObservation:
    with accepted_git_context() as repo:
        session_id = generated_token()
        runner = RecordingRunner(
            repo=repo,
            scripted={
                (
                    *module.SPX_SESSION_SHOW_COMMAND,
                    module.SPX_SESSION_SHOW_JSON_FLAG,
                    session_id,
                ): (0, stdout, ""),
                (*module.SPX_SESSION_SHOW_COMMAND, session_id): (
                    0,
                    generated_token(),
                    "",
                ),
            },
        )
        return UnloadableSessionObservation(
            condition=condition,
            verdicts=tuple(module.verify(session_id, repo, runner)),
        )


def spec_entry_observation() -> SpecEntryObservation:
    """Record which verdict kinds one recorded spec entry produces."""
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        session_id = generated_token()
        spec = projection_spec_path()
        runner = RecordingRunner(
            repo=repo,
            scripted=_session_command_scripts(module, session_id, specs=(spec,)),
        )
        return SpecEntryObservation(
            spec_path=spec,
            kinds=tuple(
                verdict.kind for verdict in module.verify(session_id, repo, runner)
            ),
        )


def _arrangeable_claim_conditions(
    module: ModuleType,
) -> tuple[tuple[object, tuple[object, ...]], ...]:
    """Pair each claim kind with the conditions the arrangement ladder builds.

    The pairing states what this harness can stage, not what the verifier's own
    validity table permits. Reading that table instead would let a narrowed
    table delete a case rather than fail one.
    """
    matches_differs = (module.ClaimRelation.MATCHES, module.ClaimRelation.DIFFERS)
    observed = (module.ClaimRelation.OBSERVED,)
    unavailable = (module.ClaimRelation.UNAVAILABLE,)
    return (
        (module.ClaimKind.SESSION_METADATA, unavailable),
        (module.ClaimKind.GIT_REF, matches_differs + unavailable),
        (module.ClaimKind.INJECTED_PATH, matches_differs),
        (module.ClaimKind.NODE_STATUS, observed + unavailable),
        (module.ClaimKind.UNCOMMITTED_STATE, matches_differs + unavailable),
        (module.ClaimKind.EXTERNAL_ID, observed + unavailable),
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
            specs = (projection_spec_path(),)
            scripts = _node_status_arrangement(module, relation)
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


def _node_status_arrangement(module: ModuleType, relation: object) -> ScriptMap:
    if relation is module.ClaimRelation.OBSERVED:
        return _projection_script(module)
    if relation is module.ClaimRelation.UNAVAILABLE:
        return {
            tuple(module.SPX_SPEC_STATUS_COMMAND): (
                module.COMMAND_UNAVAILABLE_EXIT,
                "",
                generated_token(),
            )
        }
    raise ClaimHarnessError(f"unhandled node-status relation: {relation}")


def projection_spec_path() -> str:
    """Return a spec path under a node the real projection carries."""
    node_id = sorted(spec_status_records())[0]
    return f"{spec_tree_root_name()}/{node_id}/{generated_token()}.md"


def _projection_script(module: ModuleType) -> ScriptMap:
    return {tuple(module.SPX_SPEC_STATUS_COMMAND): (0, spec_status_stdout(), "")}


def spec_status_stdout() -> str:
    """Return the real projection the installed spx CLI emits for this tree."""
    module = load_verify_session_claims_module()
    proc = subprocess.run(
        [
            *module.SPX_SPEC_STATUS_COMMAND,
            module.SPX_FORMAT_FLAG,
            module.SPX_JSON_FORMAT,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def spec_status_records() -> dict[str, dict[str, object]]:
    """Flatten every node record the real projection carries, keyed by its id."""
    module = load_verify_session_claims_module()
    payload = json.loads(spec_status_stdout())
    records: dict[str, dict[str, object]] = {}

    def collect(nodes: object) -> None:
        if not isinstance(nodes, list):
            return
        for entry in nodes:
            if not isinstance(entry, dict):
                continue
            records[str(entry[module.NODE_RECORD_ID_FIELD])] = entry
            collect(entry.get(module.NODE_RECORD_CHILDREN_FIELD))

    collect(payload[module.SPEC_STATUS_NODES_FIELD])
    if not records:
        raise ClaimHarnessError("the spec-status projection carries no node records")
    return records


def spec_tree_root_name() -> str:
    """Return the tree directory the product spec sits in, read from disk."""
    roots = sorted({path.parent.name for path in REPO_ROOT.glob("*/*.product.md")})
    if len(roots) != 1:
        raise ClaimHarnessError(f"expected one spec-tree root, observed: {roots}")
    return roots[0]


def node_status_observations() -> tuple[NodeStatusObservation, ...]:
    """Observe verdicts for a parent and a leaf node of the real projection."""
    module = load_verify_session_claims_module()
    records = spec_status_records()
    children_field = module.NODE_RECORD_CHILDREN_FIELD
    parents = [item for item in sorted(records.items()) if item[1].get(children_field)]
    leaves = [
        item for item in sorted(records.items()) if not item[1].get(children_field)
    ]
    if not parents or not leaves:
        raise ClaimHarnessError("the projection carries no parent and leaf node pair")
    return tuple(
        _node_status_observation(module, node_id, record)
        for node_id, record in (parents[0], leaves[0])
    )


def _node_status_observation(
    module: ModuleType, node_id: str, record: dict[str, object]
) -> NodeStatusObservation:
    node_path = f"{spec_tree_root_name()}/{node_id}"
    return NodeStatusObservation(
        node_path=node_path,
        projected_record=record,
        actual=_projection_verdict(module, node_path),
    )


def absent_node_status_observation() -> AbsentNodeObservation:
    """Observe the verdict for a node the real projection does not carry."""
    module = load_verify_session_claims_module()
    records = spec_status_records()
    while True:
        candidate = generated_relative_path()
        if candidate not in records:
            break
    node_path = f"{spec_tree_root_name()}/{candidate}"
    return AbsentNodeObservation(
        node_path=node_path,
        actual=_projection_verdict(module, node_path),
    )


def _projection_verdict(module: ModuleType, node_path: str) -> ClaimVerdictLike:
    with accepted_git_context() as repo:
        session_id = generated_token()
        spec = f"{node_path}/{generated_token()}.md"
        scripts = _session_command_scripts(
            module, session_id, specs=(spec,)
        ) | _projection_script(module)
        return _observation_for_kind(
            module.verify(
                session_id, repo, RecordingRunner(repo=repo, scripted=scripts)
            ),
            module.ClaimKind.NODE_STATUS,
        )


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
    """Exercise the origin-branch domain, including a commit-shaped branch name."""
    module = load_verify_session_claims_module()
    observations: list[BranchReferenceObservation] = []
    with handoff_git_env() as env:
        observations.append(
            _git_ref_observation(
                module,
                env.root,
                env.push_work_branch(generated_token()),
                present_on_origin=True,
            )
        )
        observations.append(
            _git_ref_observation(
                module,
                env.root,
                env.push_work_branch(generated_sha()),
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
    """Return the real node state, a generated PR state, and their evidence."""
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        session_id = generated_token()
        spec = projection_spec_path()
        number = generated_number()
        node_values = _projected_scalar_values(module, spec)
        external_state = generated_token()
        scripts = (
            _session_command_scripts(
                module,
                session_id,
                specs=(spec,),
                pr_numbers=(number,),
            )
            | _projection_script(module)
            | {
                tuple(module.GH_PR_VIEW_COMMAND): (
                    0,
                    json.dumps({module.GH_PR_STATE_FIELD: external_state}),
                    "",
                ),
            }
        )
        verdicts = module.verify(
            session_id, repo, RecordingRunner(repo=repo, scripted=scripts)
        )
        node = _observation_for_kind(verdicts, module.ClaimKind.NODE_STATUS)
        external = _observation_for_kind(verdicts, module.ClaimKind.EXTERNAL_ID)
        return ObservedStateObservation(
            node_values=node_values,
            node=node,
            external_state=external_state,
            external=external,
        )


def _projected_scalar_values(module: ModuleType, spec: str) -> tuple[str, ...]:
    """Render the real record's scalar values as they appear in JSON output."""
    node_id = str(pathlib.PurePosixPath(spec).parent.relative_to(spec_tree_root_name()))
    record = spec_status_records()[node_id]
    return tuple(
        json.dumps(value)
        for key, value in record.items()
        if key != module.NODE_RECORD_CHILDREN_FIELD
        and not isinstance(value, list | dict)
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
        spec = projection_spec_path()
        number = generated_number()
        before = _git_status(repo)
        scripts = (
            _session_command_scripts(
                module,
                session_id,
                git_ref=_unreachable_sha(repo),
                git_status=module.GitStatus.CLEAN,
                specs=(spec,),
                pr_numbers=(number,),
            )
            | _projection_script(module)
            | {
                tuple(module.GH_PR_VIEW_COMMAND): (
                    0,
                    json.dumps({module.GH_PR_STATE_FIELD: generated_token()}),
                    "",
                ),
            }
        )
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
    "AbsentNodeObservation",
    "BranchReferenceObservation",
    "ClaimHarnessError",
    "ClaimMappingObservation",
    "MetadataLoadingObservation",
    "NodeStatusObservation",
    "ObservedStateObservation",
    "ReadOnlyVerificationObservation",
    "RecordingRunner",
    "absent_node_status_observation",
    "branch_reference_observations",
    "claim_mapping_observations",
    "default_runner_failure_observations",
    "load_verify_session_claims_module",
    "metadata_loading_observation",
    "node_status_observations",
    "observed_state_observation",
    "projection_spec_path",
    "read_only_verification_observation",
    "script_import_roots",
    "spec_status_records",
    "spec_status_stdout",
    "spec_tree_root_name",
    "subprocess_call_owners",
    "verify_parameters",
]
