"""Read one position's mail through the typed inbox operation of the mail adapter.

The adapter takes its project key from the repository of its working
directory, so its commands run inside the channel's repository to read that
channel.
"""

from __future__ import annotations

import functools
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import cast

import environment

MAIL_ADAPTER = ("operate-agent-mail", "agent_mail")
INBOX_LIMIT = 30


@dataclass(frozen=True)
class Record:
    id: int
    sender: str
    subject: str
    correlation: str | None


class MailError(RuntimeError):
    pass


@functools.cache
def _adapter() -> ModuleType:
    return environment.sibling_adapter(*MAIL_ADAPTER)


@dataclass(frozen=True)
class ChannelRunner:
    """The adapter's command runner, run with the channel as working directory.

    It runs exactly the argument vectors the adapter builds, under the
    adapter's own bound, and builds none of its own.
    """

    channel: str
    timeout_seconds: int

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        env: Mapping[str, str] | None = None,
    ) -> object:
        completed = subprocess.run(
            argv,
            input=stdin,
            stdin=subprocess.DEVNULL if stdin is None else None,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
            cwd=self.channel,
            env=None if env is None else dict(env),
        )
        return _adapter().CommandResult(
            completed.returncode, completed.stdout, completed.stderr
        )


def inbox(channel: str, agent: str, limit: int = INBOX_LIMIT) -> list[Record]:
    """The records of `agent`'s inbox in the channel's store, or MailError naming the channel."""
    adapter = _adapter()
    if not Path(channel).is_dir():
        raise MailError(f"{channel}: no channel directory")
    request = adapter.operation_request(
        adapter.Operation.INBOX,
        agent=agent,
        unread_only=False,
        include_bodies=False,
        limit=limit,
    )
    runner = ChannelRunner(channel, adapter.COMMAND_TIMEOUT_SECONDS)
    result = cast(dict[str, object], adapter.execute(request, runner))
    if result.get(adapter.STATUS_FIELD) != adapter.ExecutionStatus.SUCCEEDED:
        raise MailError(
            f"{channel}: {result.get(adapter.STATUS_FIELD)}: {result.get(adapter.DETAIL_FIELD)}"
        )
    if result.get(adapter.PROJECT_KEY_FIELD) != channel:
        raise MailError(
            f"{channel}: adapter resolved {result.get(adapter.PROJECT_KEY_FIELD)}"
        )
    data = cast(Mapping[str, object], result.get(adapter.DATA_FIELD))
    records = cast(list[Mapping[str, object]], data.get(adapter.RECORDS_FIELD, []))
    return [
        Record(
            id=cast(int, record[adapter.RECORD_ID_FIELD]),
            sender=str(record[adapter.SENDER_FIELD]),
            subject=str(record[adapter.RECORD_SUBJECT_FIELD]),
            correlation=cast(str | None, record.get(adapter.CORRELATION_FIELD)),
        )
        for record in records
    ]
