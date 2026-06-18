"""Stdlib HTTP server hosting the live interview loop.

The transport layer wrapped around ``state.Store``. Everything here is Python
3.11 stdlib: ``http.server.ThreadingHTTPServer`` gives one thread per request,
so a long-lived SSE connection and a blocking long-poll coexist with the small
POST mutations a single local user produces.

The real-time spine is one ``threading.Condition`` guarding the store. Mutating
routes (``/event`` from the browser, ``/reply`` from the agent) apply under the
lock and ``notify_all``. Waiting routes (``/poll`` for the agent, ``/events``
SSE for the browser) block on the condition until ``rev`` advances past the
revision the caller already has, or a timeout fires.

Routes (all require ``?token=`` matching the session token; bind is 127.0.0.1):

    GET  /                       -> the HTML shell with initial state injected
    GET  /state                  -> {"rev", "state"}
    POST /event                  -> apply a browser interaction; {"ok","rev"} | {"conflict"}
    POST /reply                  -> apply an agent mutation (set_questions, set_tree, ...)
    GET  /poll?since=R&timeout=MS -> long-poll for the agent; events since R, or {"type":"timeout"}
    GET  /events?since=R         -> SSE stream for the browser; one frame per new rev
    POST /shutdown               -> graceful stop (the swappable launch layer calls this)

This module is import-safe: constructing a :class:`LiveServer` binds a socket
but does not serve until ``serve_forever`` runs (tests drive it on port 0 in a
background thread).
"""

from __future__ import annotations

import json
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from state import Store

SHELL_PATH = Path(__file__).with_name("shell.html")
PER_REQUEST_TIMEOUT_MS = 270_000  # mirrors impeccable: stay under client header caps
SSE_KEEPALIVE_SECONDS = 15.0


class LiveSession:
    """Store + synchronization primitive shared across request threads."""

    def __init__(self, store: Store, token: str) -> None:
        self.store = store
        self.token = token
        self.cond = threading.Condition()

    def apply(self, event: dict):
        with self.cond:
            result = self.store.apply(event)
            if result.ok:
                self.cond.notify_all()
            return result

    def snapshot(self) -> tuple[int, dict]:
        with self.cond:
            return self.store.rev, self.store.snapshot()

    def wait_past(self, since: int, timeout_s: float) -> tuple[int, dict, list]:
        """Block until rev > since or timeout. Return (rev, state, new_events)."""
        deadline = time.monotonic() + timeout_s
        with self.cond:
            while self.store.rev <= since:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return self.store.rev, self.store.snapshot(), []
                self.cond.wait(remaining)
            new_events = [e for e in self.store.journal if e["rev"] > since]
            return self.store.rev, self.store.snapshot(), new_events


def _shell_bytes() -> bytes:
    # The page bootstraps itself by reading ?token= from the URL and fetching
    # /state, so the served HTML needs no per-request injection.
    return SHELL_PATH.read_bytes()


def make_handler(session: LiveSession):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        # Quiet logging keeps the spike output readable; flip for debugging.
        def log_message(self, *_args) -> None:  # noqa: D401
            pass

        # --- helpers ----------------------------------------------------

        def _query(self) -> dict:
            return parse_qs(urlparse(self.path).query)

        def _path(self) -> str:
            return urlparse(self.path).path

        def _authed(self, query: dict) -> bool:
            return query.get("token", [None])[0] == session.token

        def _send_json(self, code: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _read_body(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))

        # --- GET --------------------------------------------------------

        def do_GET(self) -> None:
            path = self._path()
            query = self._query()

            if path == "/":
                body = _shell_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return

            if not self._authed(query):
                self._send_json(401, {"error": "bad_token"})
                return

            if path == "/state":
                rev, state = session.snapshot()
                self._send_json(200, {"rev": rev, "state": state})
                return

            if path == "/poll":
                since = int(query.get("since", ["0"])[0])
                timeout_ms = min(
                    int(query.get("timeout", [str(PER_REQUEST_TIMEOUT_MS)])[0]),
                    PER_REQUEST_TIMEOUT_MS,
                )
                rev, state, events = session.wait_past(since, timeout_ms / 1000)
                if rev <= since:
                    self._send_json(200, {"type": "timeout", "rev": rev})
                else:
                    self._send_json(
                        200,
                        {
                            "type": "update",
                            "rev": rev,
                            "events": events,
                            "state": state,
                        },
                    )
                return

            if path == "/events":
                self._serve_sse(int(query.get("since", ["0"])[0]))
                return

            self._send_json(404, {"error": "not_found"})

        def _serve_sse(self, since: int) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                while True:
                    rev, state, events = session.wait_past(since, SSE_KEEPALIVE_SECONDS)
                    if rev <= since:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                        continue
                    frame = json.dumps({"rev": rev, "events": events, "state": state})
                    self.wfile.write(f"data: {frame}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    since = rev
            except (BrokenPipeError, ConnectionResetError):
                return  # browser navigated away; let the thread end

        # --- POST -------------------------------------------------------

        def do_POST(self) -> None:
            path = self._path()
            query = self._query()
            if not self._authed(query):
                self._send_json(401, {"error": "bad_token"})
                return

            if path in ("/event", "/reply"):
                try:
                    event = self._read_body()
                except (ValueError, json.JSONDecodeError):
                    self._send_json(400, {"error": "bad_json"})
                    return
                result = session.apply(event)
                if result.ok:
                    self._send_json(
                        200, {"ok": True, "rev": result.rev, "event": result.event}
                    )
                else:
                    self._send_json(
                        409,
                        {"ok": False, "rev": result.rev, "conflict": result.conflict},
                    )
                return

            if path == "/shutdown":
                self._send_json(200, {"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return

            self._send_json(404, {"error": "not_found"})

    return Handler


class LiveServer:
    """Owns the bound socket and the background serving thread."""

    def __init__(
        self,
        store: Store | None = None,
        *,
        token: str | None = None,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        self.session = LiveSession(store or Store(), token or secrets.token_urlsafe(16))
        self._httpd = ThreadingHTTPServer((host, port), make_handler(self.session))
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    @property
    def token(self) -> str:
        return self.session.token

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self) -> "LiveServer":
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def wait(self) -> None:
        """Block until the serving thread ends (e.g. via a /shutdown request)."""
        if self._thread:
            self._thread.join()
        self._httpd.server_close()

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=5)
