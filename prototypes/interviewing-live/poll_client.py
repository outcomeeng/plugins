"""Agent-side transport: long-poll the server for the next user interaction.

This is the second swappable piece. The agent runs this as a one-shot command
(in Claude Code, as a background task whose completion the harness reports):

    python3 poll_client.py --since R        # block until rev>R, print the update JSON, exit
    python3 poll_client.py --reply '<json>' # apply an agent mutation (set_questions, ...)
    python3 poll_client.py --shutdown       # stop the server

The one-shot contract mirrors impeccable's portable poll: block, print one JSON
object, exit — re-run to keep listening. An MCP-model transport would replace
this with a blocking ``wait_for_interaction`` tool call returning the same JSON,
so the handling logic in the skill body stays identical.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

INFO_FILE = Path(__file__).with_name(".run") / "server.json"
DEFAULT_TIMEOUT_MS = 270_000


def read_info() -> dict:
    if not INFO_FILE.exists():
        sys.stderr.write("No running live server. Start one with: python3 boot.py\n")
        raise SystemExit(1)
    return json.loads(INFO_FILE.read_text(encoding="utf-8"))


def _get(url: str, timeout_s: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return json.loads(err.read().decode("utf-8"))


def poll(info: dict, since: int, timeout_ms: int) -> dict:
    url = f"{info['url']}/poll?token={info['token']}&since={since}&timeout={timeout_ms}"
    # Add slack so the client outlives the server's own poll deadline.
    return _get(url, timeout_ms / 1000 + 10)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Poll the live interview server")
    parser.add_argument("--since", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_MS)
    parser.add_argument("--reply", default=None, help="JSON event to apply via /reply")
    parser.add_argument("--shutdown", action="store_true")
    args = parser.parse_args(argv)

    info = read_info()

    if args.shutdown:
        print(json.dumps(_post(f"{info['url']}/shutdown?token={info['token']}", {})))
        return 0

    if args.reply is not None:
        event = json.loads(args.reply)
        result = _post(f"{info['url']}/reply?token={info['token']}", event)
        print(json.dumps(result))
        return 0

    print(json.dumps(poll(info, args.since, args.timeout)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
