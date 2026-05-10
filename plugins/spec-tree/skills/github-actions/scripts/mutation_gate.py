"""Gate state-changing GitHub commands behind explicit user instruction.

Usage:
    uv run python mutation_gate.py check [--user-instructed] <command...>

`--user-instructed` must precede the command tokens; argparse's `REMAINDER`
captures everything after the first command token verbatim, so a flag
appearing after the command is treated as part of the command and silently
ignored.

When the command tokens match a gated pattern (e.g., `gh auth switch`,
`gh run rerun`), the script enforces the consent rule:

  - Without `--user-instructed`: exit 1, write a JSON error to stderr
    naming the missing flag and the gated subcommand.
  - With `--user-instructed`: exit 0, append one line to
    `${CLAUDE_PROJECT_DIR}/.spx/mutation-audit.log` recording the timestamp,
    current gh account, gate label, and gated command.

Commands that do not match any gated pattern pass through with exit 0 and
`gated: false` in the JSON payload on stdout.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import subprocess
import sys

SCHEMA_VERSION = 1
SUBPROCESS_TIMEOUT_SECONDS = 30

GATED_PATTERNS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("gh", "auth", "login"), "gh auth login"),
    (("gh", "auth", "switch"), "gh auth switch"),
    (("gh", "auth", "refresh"), "gh auth refresh"),
    (("gh", "auth", "logout"), "gh auth logout"),
    (("gh", "run", "rerun"), "gh run rerun"),
    (("gh", "run", "cancel"), "gh run cancel"),
    (("gh", "run", "delete"), "gh run delete"),
    (("gh", "workflow", "run"), "gh workflow run"),
    (("gh", "workflow", "enable"), "gh workflow enable"),
    (("gh", "workflow", "disable"), "gh workflow disable"),
)


def match_gate(tokens: list[str]) -> str | None:
    for prefix, label in GATED_PATTERNS:
        if len(tokens) >= len(prefix) and tuple(tokens[: len(prefix)]) == prefix:
            return label
    return None


def get_current_account() -> str:
    try:
        proc = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return "unknown"
    out = proc.stdout.strip()
    return out if proc.returncode == 0 and out else "unknown"


def audit_log_path() -> pathlib.Path:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return pathlib.Path(project_dir) / ".spx" / "mutation-audit.log"


def append_audit(label: str, command: str) -> pathlib.Path:
    path = audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    account = get_current_account()
    line = f"{timestamp}\t{account}\t{label}\t{command}\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
    return path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Gate state-changing gh/git commands behind explicit user instruction.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_check = sub.add_parser("check", help="check a command for the consent gate")
    p_check.add_argument(
        "--user-instructed",
        action="store_true",
        help="acknowledge that the user explicitly instructed this command in the same turn",
    )
    p_check.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="the command tokens to check (everything after `check`)",
    )

    args = parser.parse_args(argv[1:])
    tokens = list(args.command)
    if not tokens:
        sys.stderr.write(
            json.dumps(
                {"schema_version": SCHEMA_VERSION, "error": "no command provided"}
            )
            + "\n"
        )
        return 2

    if "--user-instructed" in tokens:
        sys.stderr.write(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "error": (
                        "--user-instructed must precede the command tokens "
                        "(argparse REMAINDER captures any flag appearing after the command)"
                    ),
                    "command": " ".join(tokens),
                },
            )
            + "\n"
        )
        return 2

    label = match_gate(tokens)
    command_str = " ".join(tokens)

    if label is None:
        sys.stdout.write(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "gated": False,
                    "command": command_str,
                    "error": None,
                },
                indent=2,
            )
            + "\n"
        )
        return 0

    if not args.user_instructed:
        sys.stderr.write(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "gated": True,
                    "label": label,
                    "command": command_str,
                    "missing_flag": "--user-instructed",
                    "error": (
                        f"{label!r} requires explicit user instruction; pass --user-instructed "
                        "once the user has explicitly authorized this command in the current turn"
                    ),
                },
                indent=2,
            )
            + "\n"
        )
        return 1

    audit_path = append_audit(label, command_str)
    sys.stdout.write(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "gated": True,
                "label": label,
                "command": command_str,
                "audit_log": str(audit_path),
                "error": None,
            },
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
