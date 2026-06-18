"""Script-model launch layer: boot the live server and publish its coordinates.

This is the *swappable* part of the design. In the script model the agent runs
this once to start the server, and a server-info file lets the poll client and
the browser find the port and token. An MCP-model launch layer would replace
this file entirely — Claude Code would own the process lifecycle — without
touching ``server.py`` or ``state.py``.

Usage::

    python3 boot.py [--port N] [--seed seed.json]

Prints a JSON line with ``port``, ``token``, ``url``, and ``infoFile``, then
forks the serving thread and blocks (so the process stays up for the
interview). The agent stops it with ``python3 poll_client.py --shutdown`` or by
killing the process.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from server import LiveServer
from state import Store, initial_state

RUN_DIR = Path(__file__).with_name(".run")
INFO_FILE = RUN_DIR / "server.json"


def _load_seed(path: str | None) -> Store:
    if not path:
        return Store()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "rev" in data and "questions" in data:
        return Store(data)
    # A bare {tree, planned} seed is wrapped into a fresh state document.
    return Store(initial_state(tree=data.get("tree"), planned=data.get("planned")))


def write_info(server: LiveServer) -> Path:
    RUN_DIR.mkdir(exist_ok=True)
    INFO_FILE.write_text(
        json.dumps(
            {
                "port": server.port,
                "token": server.token,
                "url": server.base_url,
                "infoFile": str(INFO_FILE),
            }
        ),
        encoding="utf-8",
    )
    return INFO_FILE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Boot the live interview server")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--seed", default=None)
    args = parser.parse_args(argv)

    server = LiveServer(_load_seed(args.seed), port=args.port).start()
    info_file = write_info(server)
    print(
        json.dumps(
            {
                "ok": True,
                "port": server.port,
                "token": server.token,
                "url": server.base_url,
                "openUrl": f"{server.base_url}/?token={server.token}",
                "infoFile": str(info_file),
            }
        )
    )
    sys.stdout.flush()

    # Keep the process alive until the server thread ends — a /shutdown request
    # stops serve_forever, which lets wait() return and this process exit.
    try:
        server.wait()
    except KeyboardInterrupt:
        server.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
