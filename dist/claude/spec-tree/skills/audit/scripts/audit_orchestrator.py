"""Audit-orchestration helpers shipped with the spec-tree plugin.

Hosts the deterministic computations that the ``/audit`` skill and the
``audit-orchestrator`` agent cannot reliably execute in-process from prose:
scope hashing, branch slug derivation, base-ref detection, git plumbing, and
the content-based identity used for regression detection across audit runs.

Exposes a stdlib ``argparse`` CLI so the ``/audit`` skill can drive
each helper from shell. Subcommands: ``base-ref``, ``current-branch``,
``branch-slug``, ``remote-tracking-ref``, ``commit-oid``, ``scope-hash``,
``config-digest``, ``branch-scope``, ``modified-since``, ``sha-reachable``,
``verdict-diff``. Library callers continue to import the functions directly
via ``importlib.util`` (per the marketplace skill-co-located Python
convention); the CLI is a thin wrapper around the same surface.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
from types import ModuleType

NULL_BYTE = b"\x00"
SCOPE_HASH_LENGTH = 12
CONFIG_DIGEST_PREFIX = b"audit-config-v1\x00"
MODIFIED_SINCE_RANGE_TEMPLATE = "{prior_sha}..HEAD"
COMMIT_PEEL_SUFFIX = "^{commit}"


def _load_changeset_scope() -> ModuleType:
    """Load the shared ``changeset_scope`` module via ``importlib``.

    The git-derivation primitives — base-ref detection, current-branch
    detection, branch-scope, diff-range expansion, slug — live in the
    changeset-scope skill; this module imports them rather than redefining
    them.
    """
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cached
    path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "scope-changeset"
        / "scripts"
        / "changeset_scope.py"
    )
    spec = importlib.util.spec_from_file_location("changeset_scope", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load changeset_scope from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return module


_changeset_scope = _load_changeset_scope()

# Shared git-derivation primitives — defined once in changeset_scope, imported
# here. ``is`` identity holds, so the auditing CLI and the thread-store slug /
# base-ref re-export resolve the same objects.
BaseRefNotConfiguredError = _changeset_scope.BaseRefNotConfiguredError
DetachedHeadError = _changeset_scope.DetachedHeadError
expand_diff_range = _changeset_scope.expand_diff_range
branch_scope = _changeset_scope.branch_scope
commit_oid = _changeset_scope.commit_oid
detect_base_ref = _changeset_scope.detect_base_ref
detect_current_branch = _changeset_scope.detect_current_branch
remote_tracking_ref = _changeset_scope.remote_tracking_ref
branch_slug = _changeset_scope.branch_slug


def compute_scope_hash(files: list[tuple[str, str]]) -> str:
    """Return a deterministic, collision-resistant hex digest of the file list.

    Each ``(path, content)`` pair is encoded as
    ``path\\0<byte_count>\\0<content>`` before being fed to SHA-256. Without
    the byte-count prefix, distinct file lists can serialize to the same
    byte stream because the path-terminator nullbyte alone does not
    delimit the content/next-path boundary; for example
    ``[("a.ts", ""), ("a.tsb", "x")]`` and
    ``[("a.ts", "a.ts"), ("b", "x")]`` both produce
    ``a.ts\\0a.tsb\\0x`` under the unprefixed framing.

    Returns the first ``SCOPE_HASH_LENGTH = 12`` characters (48 bits) of
    the SHA-256 hex digest. The truncation is collision-resistant for the
    scope-identity use case — a single branch's diff history typically
    contains at most thousands of distinct scopes, well below the 48-bit
    birthday bound (~16M distinct scopes before a collision becomes
    plausible). The framing — not the truncation — is what prevents two
    distinct file lists with the same serialized bytes from colliding;
    see the worked example above. The caller is responsible for sorting
    ``files`` deterministically before calling this function; the hash
    is sensitive to order.
    """
    digest = hashlib.sha256()
    for path, content in files:
        content_bytes = content.encode("utf-8")
        digest.update(path.encode("utf-8"))
        digest.update(NULL_BYTE)
        digest.update(str(len(content_bytes)).encode("ascii"))
        digest.update(NULL_BYTE)
        digest.update(content_bytes)
    return digest.hexdigest()[:SCOPE_HASH_LENGTH]


def compute_config_digest(payload: str) -> str:
    """Return a stable digest of the audit run's configuration payload.

    The payload is the caller's serialized description of the validation
    command, test command, overlays, and language partitions that shaped the
    run. It is separate from the frozen-scope hash because configuration can
    change while the audited file list stays the same.
    """
    digest = hashlib.sha256()
    digest.update(CONFIG_DIGEST_PREFIX)
    digest.update(payload.encode("utf-8"))
    return digest.hexdigest()


def uncommitted_scope(
    *,
    patterns: list[str] | None = None,
    repo: pathlib.Path,
) -> list[str]:
    """Return uncommitted, staged, and untracked file paths relative to HEAD.

    ``git diff --name-only HEAD`` enumerates modified-and-staged files
    only — it never lists untracked files (those that have not yet been
    ``git add``-ed). A developer who creates a new file and runs the
    audit before staging it would see an empty scope under
    ``expand_diff_range("HEAD")``. This helper closes that gap by
    unioning ``git diff --name-only HEAD`` with
    ``git ls-files --others --exclude-standard`` and de-duplicating
    while preserving git's order: modified/staged paths first (as git
    diff returns them), then untracked paths (as ``ls-files`` returns
    them, alphabetised by git). Paths matched by ``.gitignore`` are
    excluded by ``--exclude-standard`` so build artefacts do not
    pollute the scope.

    ``patterns`` filters both halves: each pathspec is applied to the
    ``git diff`` call and to the ``ls-files`` call so a new ``foo.ts``
    file and an existing modified ``bar.ts`` are both retained under
    ``patterns=["*.ts"]``.
    """
    modified = expand_diff_range("HEAD", patterns=patterns, repo=repo)
    untracked_cmd = ["git", "ls-files", "--others", "--exclude-standard"]
    if patterns:
        untracked_cmd.append("--")
        untracked_cmd.extend(patterns)
    untracked_result = subprocess.run(  # noqa: S603 — fixed argv, no shell, patterns caller-controlled
        untracked_cmd,
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    untracked = [line for line in untracked_result.stdout.splitlines() if line]
    # ``modified`` and ``untracked`` are disjoint by construction
    # (untracked files cannot appear in ``git diff HEAD``), but a defensive
    # ``dict.fromkeys`` round-trip is cheap insurance against future git
    # behaviour changes and keeps the order ``modified, untracked``.
    return list(dict.fromkeys([*modified, *untracked]))


def modified_since(
    prior_sha: str,
    *,
    patterns: list[str] | None = None,
    repo: pathlib.Path,
) -> list[str]:
    """Return files changed between ``prior_sha`` and HEAD.

    Composes the diff range ``<prior_sha>..HEAD`` (two-dot tree-diff)
    and delegates to :func:`expand_diff_range`. The two-dot form is
    deliberate and contrasts with :func:`branch_scope`'s three-dot
    form: re-run scope must include any file currently differing
    between the prior state and HEAD's tree, including deletions of
    files that existed only on a divergent prior history. Three-dot
    would mask those by routing through the merge-base.

    The caller is responsible for confirming ``prior_sha`` is reachable
    in the local clone before invoking this helper; an unreachable
    SHA raises :class:`subprocess.CalledProcessError` from the
    underlying git invocation.

    ``patterns`` filters the result by pathspec when provided; empty
    or ``None`` returns every file in the range.
    """
    range_spec = MODIFIED_SINCE_RANGE_TEMPLATE.format(prior_sha=prior_sha)
    return expand_diff_range(range_spec, patterns=patterns, repo=repo)


def is_sha_reachable(sha: str, *, repo: pathlib.Path) -> bool:
    """Return ``True`` iff ``sha`` resolves to a commit object in ``repo``.

    Runs ``git rev-parse --verify --quiet <sha>^{commit}``. The
    ``^{commit}`` peel restricts the resolution to commit objects so a
    tree SHA, blob SHA, or tag-pointing-at-non-commit returns ``False``
    even though bare ``git rev-parse <sha>`` would succeed on those.
    The caller composes ``<sha>..HEAD`` ranges downstream; a tree SHA
    would compose to a syntactically valid range and produce garbage
    file lists without this commit-type guard.

    Detects the "prior-run SHA unreachable" failure mode where a state
    file's SHA was force-pushed away or never fetched into the local
    clone. The caller's re-run protocol falls back to a full
    branch-scope scan when this returns ``False``.

    Any non-zero exit from git (unknown SHA, malformed input, non-commit
    object) maps to ``False``; the helper does not propagate
    :class:`subprocess.CalledProcessError` because every error path
    means the same thing to the caller — the SHA cannot be used.
    """
    try:
        subprocess.run(  # noqa: S603 — fixed argv, no shell, sha is caller-controlled
            [
                "git",
                "rev-parse",
                "--verify",
                "--quiet",
                f"{sha}{COMMIT_PEEL_SUFFIX}",
            ],
            cwd=repo,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return False
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _add_repo_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo",
        default=".",
        type=pathlib.Path,
        help="Git repository root (default: current directory).",
    )


def _add_pattern_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        help="Pathspec pattern to filter the result. May be repeated.",
    )


def _cmd_base_ref(args: argparse.Namespace) -> int:
    sys.stdout.write(detect_base_ref(args.repo) + "\n")
    return 0


def _cmd_current_branch(args: argparse.Namespace) -> int:
    try:
        branch = detect_current_branch(args.repo)
    except DetachedHeadError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    sys.stdout.write(branch + "\n")
    return 0


def _cmd_branch_slug(args: argparse.Namespace) -> int:
    sys.stdout.write(branch_slug(args.branch, args.state_dir) + "\n")
    return 0


def _cmd_remote_tracking_ref(args: argparse.Namespace) -> int:
    sys.stdout.write(remote_tracking_ref(args.base) + "\n")
    return 0


def _cmd_commit_oid(args: argparse.Namespace) -> int:
    try:
        oid = commit_oid(args.ref, repo=args.repo)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"{args.ref} does not resolve to a commit: {exc}\n")
        return 1
    sys.stdout.write(oid + "\n")
    return 0


def _cmd_scope_hash(args: argparse.Namespace) -> int:
    paths = [line for line in sys.stdin.read().splitlines() if line]
    pairs: list[tuple[str, str]] = []
    for path in paths:
        absolute = args.repo / path
        content = absolute.read_text(encoding="utf-8") if absolute.is_file() else ""
        pairs.append((path, content))
    sys.stdout.write(compute_scope_hash(pairs) + "\n")
    return 0


def _cmd_config_digest(_: argparse.Namespace) -> int:
    sys.stdout.write(compute_config_digest(sys.stdin.read()) + "\n")
    return 0


def _cmd_branch_scope(args: argparse.Namespace) -> int:
    files = branch_scope(args.base, patterns=args.pattern or None, repo=args.repo)
    sys.stdout.write("\n".join(files) + ("\n" if files else ""))
    return 0


def _cmd_modified_since(args: argparse.Namespace) -> int:
    files = modified_since(args.since, patterns=args.pattern or None, repo=args.repo)
    sys.stdout.write("\n".join(files) + ("\n" if files else ""))
    return 0


def _cmd_sha_reachable(args: argparse.Namespace) -> int:
    return 0 if is_sha_reachable(args.sha, repo=args.repo) else 1


def _collect_open_findings(verdict_dict: dict[str, object]) -> list[dict[str, object]]:
    """Walk a verdict's rows and children recursively and return every open finding.

    Open findings are those carried in row arrays of the wrapper and any
    child verdict. The verdict-level ``resolved`` and ``reopened`` arrays
    on a prior verdict are NOT open findings — they are state markers
    used by the diff caller, not currently-failing concerns.

    Identity-collision note: callers that index the result by
    ``_finding_identity`` (file, line, rule, message) into a dict will
    silently keep only the last finding of any colliding tuple. Distinct
    findings sharing the same identity tuple in one verdict indicates a
    producer bug, not a consumer concern.
    """
    collected: list[dict[str, object]] = []
    for row in verdict_dict.get("rows", []) or []:
        if isinstance(row, dict):
            for finding in row.get("findings", []) or []:
                if isinstance(finding, dict):
                    collected.append(finding)
    for child in verdict_dict.get("children", []) or []:
        if isinstance(child, dict):
            collected.extend(_collect_open_findings(child))
    return collected


def _finding_identity(
    finding: dict[str, object],
) -> tuple[str, int | None, str, str]:
    """Return the content-identity tuple for a finding.

    Identity is ``(file, line, rule, message)`` — the producer-stable
    description of *what* the finding flags. ``id`` and ``severity`` are
    deliberately excluded: ``id`` is producer-assigned and varies across
    runs; ``severity`` may legitimately upgrade or downgrade across runs
    without being a different finding. Two findings with the same
    identity tuple are the same concern across runs.
    """
    raw_line = finding.get("line")
    line = (
        raw_line
        if isinstance(raw_line, int) and not isinstance(raw_line, bool)
        else None
    )
    return (
        str(finding.get("file", "")),
        line,
        str(finding.get("rule", "")),
        str(finding.get("message", "")),
    )


def compute_verdict_diff(
    *,
    prior: dict[str, object] | None,
    current: dict[str, object],
) -> dict[str, object]:
    """Return the current verdict enriched with ``resolved`` and ``reopened``.

    The diff carries forward state across runs by content-identity:

    - ``resolved`` = (prior.resolved ∪ {findings present in prior.open
      and absent from current.open}) − {findings present in current.open}.
      The set grows monotonically across runs except for findings that
      are reopened.
    - ``reopened`` = current.open ∩ prior.resolved. A finding that was
      previously resolved and is now open again surfaces in this set.

    When ``prior`` is ``None`` (first run on a new PR), both arrays are
    empty and the current verdict is returned with empty ``resolved`` and
    ``reopened`` lists.

    The function does not mutate ``current``; it returns a new dict that
    is the same shape as ``current`` with the two arrays populated.
    """
    enriched = dict(current)
    enriched["resolved"] = []
    enriched["reopened"] = []
    if prior is None:
        return enriched
    prior_open = _collect_open_findings(prior)
    current_open = _collect_open_findings(current)
    prior_resolved_raw = prior.get("resolved", []) or []
    prior_resolved: list[dict[str, object]] = [
        f for f in prior_resolved_raw if isinstance(f, dict)
    ]
    prior_open_by_identity = {_finding_identity(f): f for f in prior_open}
    current_open_by_identity = {_finding_identity(f): f for f in current_open}
    prior_resolved_by_identity = {_finding_identity(f): f for f in prior_resolved}
    newly_resolved_keys = sorted(
        set(prior_open_by_identity) - set(current_open_by_identity),
        key=_identity_sort_key,
    )
    newly_resolved = [prior_open_by_identity[k] for k in newly_resolved_keys]
    carried_resolved_keys = sorted(
        set(prior_resolved_by_identity) - set(current_open_by_identity),
        key=_identity_sort_key,
    )
    carried_resolved = [prior_resolved_by_identity[k] for k in carried_resolved_keys]
    enriched["resolved"] = carried_resolved + newly_resolved
    reopened_keys = sorted(
        set(current_open_by_identity) & set(prior_resolved_by_identity),
        key=_identity_sort_key,
    )
    enriched["reopened"] = [current_open_by_identity[k] for k in reopened_keys]
    return enriched


def _identity_sort_key(
    identity: tuple[str, int | None, str, str],
) -> tuple[str, int, int, str, str]:
    """Return a None-safe sort key for finding identity tuples.

    Python 3 cannot compare ``None`` to ``int`` directly, so the line
    component is split into a presence bit (0 for None, 1 for int) and a
    numeric value (0 when None). Findings with no line sort before
    findings with a line within the same file, then by numeric line.
    """
    file_, line, rule, message = identity
    has_line = 0 if line is None else 1
    line_value = 0 if line is None else line
    return (file_, has_line, line_value, rule, message)


def _cmd_verdict_diff(args: argparse.Namespace) -> int:
    """CLI: enrich a current verdict with resolved/reopened computed from a prior.

    Reads the current verdict on stdin (JSON), reads the optional prior
    verdict from ``--prior`` (a path; absent means first-run), writes
    the enriched verdict JSON to stdout. Exit codes: 0 on success,
    1 on JSON parse failure, 2 on missing required structure.
    """
    try:
        current = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"verdict-diff: invalid current JSON on stdin: {exc}\n")
        return 1
    if not isinstance(current, dict):
        sys.stderr.write("verdict-diff: current verdict must be a JSON object\n")
        return 2
    prior: dict[str, object] | None = None
    if args.prior is not None:
        try:
            prior_text = args.prior.read_text(encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"verdict-diff: cannot read prior verdict: {exc}\n")
            return 1
        try:
            prior_loaded = json.loads(prior_text)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"verdict-diff: invalid prior JSON: {exc}\n")
            return 1
        if not isinstance(prior_loaded, dict):
            sys.stderr.write("verdict-diff: prior verdict must be a JSON object\n")
            return 2
        prior = prior_loaded
    enriched = compute_verdict_diff(prior=prior, current=current)
    json.dump(enriched, sys.stdout)
    sys.stdout.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the argparse parser exposing every CLI subcommand."""
    parser = argparse.ArgumentParser(
        prog="audit_orchestrator",
        description=(
            "Git, scope-hashing, config-digest, and verdict-diff helpers for "
            "the /audit skill."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    base_ref = subparsers.add_parser(
        "base-ref", help="Print the bare base-branch name (default 'main')."
    )
    _add_repo_arg(base_ref)
    base_ref.set_defaults(func=_cmd_base_ref)

    current_branch = subparsers.add_parser(
        "current-branch", help="Print the current branch (exit 2 on detached HEAD)."
    )
    _add_repo_arg(current_branch)
    current_branch.set_defaults(func=_cmd_current_branch)

    branch_slug_cmd = subparsers.add_parser(
        "branch-slug",
        help="Derive the branch slug for the given branch.",
    )
    branch_slug_cmd.add_argument("--branch", required=True)
    branch_slug_cmd.add_argument("--state-dir", type=pathlib.Path)
    branch_slug_cmd.set_defaults(func=_cmd_branch_slug)

    remote_tracking_ref_cmd = subparsers.add_parser(
        "remote-tracking-ref",
        help="Compose the remote-tracking ref for a bare base name.",
    )
    remote_tracking_ref_cmd.add_argument("--base", required=True)
    remote_tracking_ref_cmd.set_defaults(func=_cmd_remote_tracking_ref)

    commit_oid_cmd = subparsers.add_parser(
        "commit-oid", help="Resolve a ref to the full object ID of a commit."
    )
    commit_oid_cmd.add_argument("--ref", required=True)
    _add_repo_arg(commit_oid_cmd)
    commit_oid_cmd.set_defaults(func=_cmd_commit_oid)

    scope_hash = subparsers.add_parser(
        "scope-hash",
        help=(
            "Read newline-separated file paths from stdin, hash them with "
            "their on-disk content, print the 12-char scope hash."
        ),
    )
    _add_repo_arg(scope_hash)
    scope_hash.set_defaults(func=_cmd_scope_hash)

    config_digest = subparsers.add_parser(
        "config-digest",
        help="Read the audit configuration payload from stdin and print its digest.",
    )
    config_digest.set_defaults(func=_cmd_config_digest)

    branch_scope_cmd = subparsers.add_parser(
        "branch-scope",
        help="Print files changed on this branch vs origin/<base> (three-dot).",
    )
    branch_scope_cmd.add_argument("--base", required=True)
    _add_repo_arg(branch_scope_cmd)
    _add_pattern_arg(branch_scope_cmd)
    branch_scope_cmd.set_defaults(func=_cmd_branch_scope)

    modified_since_cmd = subparsers.add_parser(
        "modified-since",
        help="Print files changed between --since SHA and HEAD (two-dot).",
    )
    modified_since_cmd.add_argument("--since", required=True)
    _add_repo_arg(modified_since_cmd)
    _add_pattern_arg(modified_since_cmd)
    modified_since_cmd.set_defaults(func=_cmd_modified_since)

    sha_reachable_cmd = subparsers.add_parser(
        "sha-reachable",
        help="Exit 0 if SHA resolves to a commit object; 1 otherwise.",
    )
    sha_reachable_cmd.add_argument("--sha", required=True)
    _add_repo_arg(sha_reachable_cmd)
    sha_reachable_cmd.set_defaults(func=_cmd_sha_reachable)

    verdict_diff_cmd = subparsers.add_parser(
        "verdict-diff",
        help=(
            "Read a current verdict on stdin and an optional prior verdict "
            "from --prior; print the current verdict enriched with "
            "resolved/reopened arrays computed by content identity."
        ),
    )
    verdict_diff_cmd.add_argument(
        "--prior",
        type=pathlib.Path,
        default=None,
        help="Path to prior verdict JSON. Omit for first-run (no prior).",
    )
    verdict_diff_cmd.set_defaults(func=_cmd_verdict_diff)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
