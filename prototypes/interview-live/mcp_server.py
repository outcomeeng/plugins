#!/usr/bin/env python3
"""MCP transport for the live spec-tree browser surface.

Realizes `spx/16-interfaces.enabler/21-browser.enabler/15-transport.adr.md`: Claude
Code owns the browser-interface server through the plugin's ``mcpServers`` config,
the agent receives each browser-side interaction through a blocking
``wait_for_interaction`` tool, and the browser renders agent-side updates over SSE
and posts its interactions to the same server. No agent-spawned background process,
no polling loop in the agent, no copy-paste, no public website — all localhost.

This is the MCP fold-in the prototype README names: it reuses ``state.py``,
``server.py``'s HTTP+SSE core, and ``shell.html`` unchanged, and replaces
``boot.py`` + ``poll_client.py``. Claude Code launches this process over stdio;
the process starts ``LiveServer`` in-process and exposes its operations as MCP
tools. The blocking ``wait_for_interaction`` call is how the runtime — not a poll
loop — holds the wait while the user looks at the browser and clicks, edits, or
notes.

stdlib only (MCP stdio = newline-delimited JSON-RPC 2.0). Tools talk to the
embedded HTTP server over localhost so the proven real-time semantics in
``server.py`` stay the single source of truth.

Register (project ``.mcp.json`` or a plugin's ``mcpServers``):

    {
      "mcpServers": {
        "spec-tree-surface": {
          "command": "python3",
          "args": ["<abs>/prototypes/interview-live/mcp_server.py",
                   "--seed", "<abs>/prototypes/interview-live/real-tree-seed.json"]
        }
      }
    }
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

from boot import _load_seed
from server import LiveServer

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "spec-tree-surface"
SERVER_VERSION = "0.1.0"
WAIT_TIMEOUT_MS = 270_000  # < the harness call ceiling; returns a keep-waiting sentinel


def log(message: str) -> None:
    # Diagnostics MUST go to stderr; stdout is the JSON-RPC channel.
    sys.stderr.write(f"[mcp_server] {message}\n")
    sys.stderr.flush()


# --- HTTP bridge to the embedded LiveServer ----------------------------------


class Surface:
    """Owns the LiveServer and exposes its operations over localhost HTTP."""

    def __init__(self, seed_path: str | None) -> None:
        self._server = LiveServer(_load_seed(seed_path), port=0).start()
        self.base_url = self._server.base_url
        self.token = self._server.token

    @property
    def open_url(self) -> str:
        return f"{self.base_url}/?token={self.token}"

    def _get(self, path: str, timeout_s: float) -> dict:
        url = f"{self.base_url}{path}{'&' if '?' in path else '?'}token={self.token}"
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}?token={self.token}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            return json.loads(err.read().decode("utf-8"))

    def wait_for_interaction(self, since: int) -> dict:
        # Blocks server-side until rev>since or the deadline yields {"type":"timeout"}.
        return self._get(
            f"/poll?since={since}&timeout={WAIT_TIMEOUT_MS}",
            WAIT_TIMEOUT_MS / 1000 + 10,
        )

    def present(self, questions: dict | None, tree: list | None) -> dict:
        results = {}
        if questions is not None:
            results["questions"] = self._post(
                "/reply", {"type": "set_questions", "questions": questions}
            )
        if tree is not None:
            results["tree"] = self._post("/reply", {"type": "set_tree", "tree": tree})
        return results or {"ok": True, "note": "nothing to present"}

    def shutdown(self) -> dict:
        return self._post("/shutdown", {})


# --- MCP tool definitions -----------------------------------------------------


TOOLS = [
    {
        "name": "get_surface_url",
        "description": "Return the localhost URL of the live spec-tree browser surface. Give it to the user to open; the surface streams agent updates and posts the user's clicks, edits, and notes back over this MCP server.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "wait_for_interaction",
        "description": 'Block until the user interacts with the surface (clicks, edits a node, reorders, answers a question, adds a note), then return that interaction as JSON. Pass the last revision you saw as `since`. Returns {"type":"timeout"} if the user is idle past the deadline — call again to keep waiting. This is the agent\'s inbox: nothing comes back without it.',
        "inputSchema": {
            "type": "object",
            "properties": {
                "since": {
                    "type": "integer",
                    "description": "Last revision seen (0 to start).",
                }
            },
        },
    },
    {
        "name": "present",
        "description": "Push agent-side state to the surface, which the browser renders live over SSE. Provide `questions` (the interview question set) and/or `tree` (the spec-tree nodes) to render.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "object",
                    "description": "Question set: {current, planned, settled}.",
                },
                "tree": {"type": "array", "description": "Spec-tree nodes to render."},
            },
        },
    },
    {
        "name": "shutdown_surface",
        "description": "Stop the browser surface server. Call when the session is done.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def dispatch_tool(surface: Surface, name: str, args: dict) -> dict:
    if name == "get_surface_url":
        return {"url": surface.open_url}
    if name == "wait_for_interaction":
        return surface.wait_for_interaction(int(args.get("since", 0)))
    if name == "present":
        return surface.present(args.get("questions"), args.get("tree"))
    if name == "shutdown_surface":
        return surface.shutdown()
    raise ValueError(f"unknown tool: {name}")


# --- MCP stdio JSON-RPC loop --------------------------------------------------


def write_message(message: dict) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def handle_request(surface: Surface, req: dict) -> dict | None:
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    if method in ("notifications/initialized", "initialized"):
        return None  # notification: no response
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            result = dispatch_tool(surface, name, args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
            }
        except Exception as exc:  # surface tool errors as MCP tool errors, not crashes
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"error: {exc}"}],
                    "isError": True,
                },
            }
    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"method not found: {method}"},
        }
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="MCP transport for the live spec-tree surface"
    )
    parser.add_argument(
        "--seed",
        default=None,
        help="seed JSON ({tree, planned}); e.g. real-tree-seed.json",
    )
    args = parser.parse_args(argv)

    surface = Surface(args.seed)
    log(f"surface up at {surface.open_url}")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            log(f"skipping non-JSON line: {line[:80]}")
            continue
        response = handle_request(surface, req)
        if response is not None:
            write_message(response)

    log("stdin closed; stopping surface")
    surface.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
