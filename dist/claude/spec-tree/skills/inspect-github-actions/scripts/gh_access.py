"""Detect repository identity, host, and gh authentication state.

Usage:
    python3 gh_access.py [OWNER/REPO]

If OWNER/REPO is omitted, the helper parses `git remote get-url origin` to
detect it. The host is parsed from the remote URL (github.com or a GitHub
Enterprise hostname).

Output: a single JSON object on stdout with these fields:
    schema_version      int
    owner_repo          str | null
    host                str | null
    current_account     str | null
    has_access          bool
    available_accounts  list[str]
    is_tty              bool
    error               str | null

Exit codes:
    0 — success; JSON written to stdout
    1 — non-fatal error; JSON written to stdout with `error` field set
    2 — argument parse error written to stderr (no JSON on stdout)

The helper consolidates owner/repo detection, host detection, account
identity, repo access probe, and authenticated-account enumeration into one
atomic call so the agent can decide whether to prompt for an account switch
on a single JSON read.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from typing import Any

SCHEMA_VERSION = 1
SUBPROCESS_TIMEOUT_SECONDS = 30

# Two URL forms cover every remote shape:
#   - `git@host:owner/repo[.git][/]` — the SCP-style form, no scheme, no port
#   - `[scheme://[user@]]host[:port]/owner/repo[.git][/]` — http/https/ssh
# Repo names may contain dots (e.g. `awesome.actions`), so the regex uses a
# lazy `.+?` match for repo plus an explicit optional `\.git` suffix.
_SCP_REMOTE_RE = re.compile(
    r"""
    ^
    git@
    (?P<host>[^:]+)
    :
    (?P<owner>[^/]+)
    /
    (?P<repo>.+?)
    (?:\.git)?
    /?
    $
    """,
    re.VERBOSE,
)
_URL_REMOTE_RE = re.compile(
    r"""
    ^
    (?:(?:https?|ssh)://(?:git@)?)?
    (?P<host>[^/:]+)
    (?::\d+)?
    /
    (?P<owner>[^/]+)
    /
    (?P<repo>.+?)
    (?:\.git)?
    /?
    $
    """,
    re.VERBOSE,
)


def _run(cmd: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"subprocess timed out after {exc.timeout}s: {' '.join(cmd)}"
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def detect_remote_url() -> str | None:
    code, out, _ = _run(["git", "remote", "get-url", "origin"])
    return out if code == 0 and out else None


def parse_remote(remote: str) -> tuple[str, str] | None:
    """Parse a remote URL into (host, "owner/repo"). SSH ports are stripped."""
    cleaned = remote.strip()
    match = _SCP_REMOTE_RE.match(cleaned) or _URL_REMOTE_RE.match(cleaned)
    if not match:
        return None
    return match["host"], f"{match['owner']}/{match['repo']}"


def get_current_account() -> str | None:
    code, out, _ = _run(["gh", "api", "user", "--jq", ".login"])
    return out if code == 0 and out else None


def check_repo_access(owner_repo: str) -> bool:
    code, _, _ = _run(["gh", "api", f"repos/{owner_repo}", "--jq", ".name"])
    return code == 0


def get_available_accounts() -> list[str]:
    """Return all logins authenticated with `gh`, across all hosts.

    Consumes `gh auth status --json hosts` (structured output, stable since
    gh 2.40+). Returns an empty list when gh is unauthenticated or the
    output cannot be parsed.
    """
    code, out, _ = _run(["gh", "auth", "status", "--json", "hosts"])
    if code != 0 or not out:
        return []
    try:
        data: dict[str, Any] = json.loads(out)
    except json.JSONDecodeError:
        return []
    accounts: list[str] = []
    for host_entries in data.get("hosts", {}).values():
        if not isinstance(host_entries, list):
            continue
        for entry in host_entries:
            login = entry.get("login") if isinstance(entry, dict) else None
            if isinstance(login, str) and login and login not in accounts:
                accounts.append(login)
    return accounts


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Detect repository identity, host, and gh authentication state."
    )
    parser.add_argument(
        "owner_repo",
        nargs="?",
        help="OWNER/REPO; auto-detected from git remote if omitted",
    )
    args = parser.parse_args(argv[1:])

    error: str | None = None
    host: str | None = None
    owner_repo: str | None = args.owner_repo

    if owner_repo is None:
        remote = detect_remote_url()
        if remote is None:
            error = "no git remote 'origin' found and no OWNER/REPO argument provided"
        else:
            parsed = parse_remote(remote)
            if parsed is None:
                error = f"could not parse git remote: {remote!r}"
            else:
                host, owner_repo = parsed
    elif "/" not in owner_repo:
        error = f"invalid OWNER/REPO argument: {owner_repo!r}"
        owner_repo = None
    else:
        remote = detect_remote_url()
        if remote is not None:
            parsed = parse_remote(remote)
            if parsed is not None:
                host = parsed[0]
        if host is None:
            # Explicit OWNER/REPO without a parseable remote: default to the
            # gh CLI's default host. GitHub Enterprise users should invoke
            # gh_access.py from inside a checkout whose remote names the
            # enterprise host so detect_remote_url() picks it up.
            host = "github.com"

    has_access = check_repo_access(owner_repo) if owner_repo else False

    result = {
        "schema_version": SCHEMA_VERSION,
        "owner_repo": owner_repo,
        "host": host,
        "current_account": get_current_account(),
        "has_access": has_access,
        "available_accounts": get_available_accounts(),
        "is_tty": sys.stdin.isatty() and sys.stdout.isatty(),
        "error": error,
    }
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0 if error is None else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
