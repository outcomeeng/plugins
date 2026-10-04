"""Read one position's mail through the coding-agents mail adapter.

The adapter takes its project key from the repository of its working
directory, so running it inside the channel's bare repository reads that
channel.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

# The mail adapter ships in a sibling skill of this plugin.
MAIL = Path(__file__).resolve().parents[2] / "operate-agent-mail/scripts/agent_mail.py"
ADAPTER_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class Record:
    id: int
    sender: str
    subject: str
    correlation: str | None


class MailError(RuntimeError):
    pass


def inbox(channel: str, agent: str, limit: int = 30) -> list[Record]:
    request = {
        "schemaVersion": 1,
        "operation": "inbox",
        "arguments": {
            "agent": agent,
            "unreadOnly": False,
            "includeBodies": False,
            "limit": limit,
        },
    }
    try:
        completed = subprocess.run(
            ["python3", str(MAIL), "run"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            cwd=channel,
            timeout=ADAPTER_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise MailError(
            f"no answer within {ADAPTER_TIMEOUT_SECONDS}s reading the mail of {channel}"
        ) from error
    except OSError as error:
        raise MailError(f"cannot read the mail of {channel}: {error}") from error
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise MailError(
            f"unreadable result: {completed.stderr.strip()[:200]}"
        ) from error
    if result.get("status") != "succeeded":
        raise MailError(f"{result.get('status')}: {result.get('detail')}")
    if result.get("projectKey") != channel:
        raise MailError(f"adapter resolved {result.get('projectKey')}, not {channel}")
    return [
        Record(
            id=int(record["id"]),
            sender=record.get("sender", "?"),
            subject=record.get("subject", ""),
            correlation=record.get("correlation"),
        )
        for record in result["data"].get("records", [])
    ]
