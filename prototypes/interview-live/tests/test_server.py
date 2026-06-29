"""Integration tests for the live server transport.

Each test boots a real :class:`LiveServer` on an ephemeral port in a background
thread and drives it over HTTP, then stops it — no process outlives the test.
These cover the real-time spine: token auth, long-poll wakeup, SSE delivery,
conflict status codes, and clean shutdown.
"""

from __future__ import annotations

import json
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.client import HTTPConnection
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import LiveServer  # noqa: E402
from state import Store, initial_state  # noqa: E402


def seeded_store() -> Store:
    tree = [
        {
            "id": "a",
            "slug": "infra",
            "kind": "enabler",
            "order": 10,
            "title": "Infra",
            "children": [],
        }
    ]
    return Store(initial_state(tree=tree))


class ServerTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.server = LiveServer(seeded_store(), token="tkn").start()
        self.base = self.server.base_url

    def tearDown(self) -> None:
        self.server.stop()

    def get(self, path: str, timeout: float = 5.0) -> tuple[int, dict]:
        try:
            with urllib.request.urlopen(self.base + path, timeout=timeout) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            with e:
                return e.code, json.loads(e.read().decode())

    def post(self, path: str, body: dict) -> tuple[int, dict]:
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            with e:
                return e.code, json.loads(e.read().decode())


class AuthAndState(ServerTestBase):
    def test_state_requires_token(self) -> None:
        code, body = self.get("/state")
        self.assertEqual(code, 401)
        self.assertEqual(body["error"], "bad_token")

    def test_state_returns_seed(self) -> None:
        code, body = self.get("/state?token=tkn")
        self.assertEqual(code, 200)
        self.assertEqual(body["rev"], 0)
        self.assertEqual(body["state"]["tree"][0]["title"], "Infra")

    def test_event_bumps_rev(self) -> None:
        code, body = self.post(
            "/event?token=tkn", {"type": "tree_rename", "nodeId": "a", "title": "X"}
        )
        self.assertEqual(code, 200)
        self.assertEqual(body["rev"], 1)

    def test_conflict_returns_409(self) -> None:
        code, body = self.post(
            "/event?token=tkn", {"type": "tree_rename", "nodeId": "ghost", "title": "X"}
        )
        self.assertEqual(code, 409)
        self.assertEqual(body["conflict"], "missing_node")

    def test_shell_served_without_token(self) -> None:
        # The page is public; it reads ?token= from the URL and fetches /state.
        with urllib.request.urlopen(self.base + "/", timeout=5) as r:
            self.assertEqual(r.status, 200)
            html = r.read().decode()
        self.assertIn('id="tree"', html)
        self.assertIn("/events?token=", html)


class LongPoll(ServerTestBase):
    def test_poll_times_out_when_idle(self) -> None:
        start = time.monotonic()
        code, body = self.get("/poll?token=tkn&since=0&timeout=300", timeout=5)
        self.assertEqual(code, 200)
        self.assertEqual(body["type"], "timeout")
        self.assertLess(time.monotonic() - start, 3)

    def test_poll_wakes_on_event(self) -> None:
        result: dict = {}

        def poller() -> None:
            _code, body = self.get("/poll?token=tkn&since=0&timeout=5000")
            result["body"] = body

        t = threading.Thread(target=poller)
        t.start()
        time.sleep(0.2)  # let the poll block
        self.post(
            "/event?token=tkn",
            {"type": "tree_rename", "nodeId": "a", "title": "Renamed"},
        )
        t.join(timeout=5)

        self.assertEqual(result["body"]["type"], "update")
        self.assertEqual(result["body"]["rev"], 1)
        self.assertEqual(len(result["body"]["events"]), 1)
        self.assertEqual(result["body"]["state"]["tree"][0]["title"], "Renamed")

    def test_agent_reply_wakes_browser_poll(self) -> None:
        """An agent /reply mutation must wake a waiting browser/poll listener."""
        result: dict = {}

        def poller() -> None:
            _c, body = self.get("/poll?token=tkn&since=0&timeout=5000")
            result["body"] = body

        t = threading.Thread(target=poller)
        t.start()
        time.sleep(0.2)
        self.post(
            "/reply?token=tkn",
            {
                "type": "set_questions",
                "questions": {
                    "planned": [],
                    "current": {
                        "id": "q1",
                        "text": "Ready?",
                        "options": ["yes"],
                        "choice": None,
                    },
                    "settled": [],
                },
            },
        )
        t.join(timeout=5)
        self.assertEqual(result["body"]["state"]["questions"]["current"]["id"], "q1")


class SSE(ServerTestBase):
    def test_sse_delivers_a_frame_on_mutation(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.server.port, timeout=5)
        conn.request("GET", "/events?token=tkn&since=0")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.getheader("Content-Type"), "text/event-stream")

        time.sleep(0.2)
        self.post(
            "/event?token=tkn",
            {
                "type": "tree_add",
                "parentId": None,
                "kind": "outcome",
                "title": "New outcome",
            },
        )

        frame = self._read_data_frame(resp)
        payload = json.loads(frame)
        self.assertEqual(payload["rev"], 1)
        self.assertEqual(payload["state"]["tree"][-1]["title"], "New outcome")
        conn.close()

    def _read_data_frame(self, resp, deadline: float = 5.0) -> str:
        """Read SSE lines until a ``data:`` frame arrives; skip keepalives.

        Reads a line at a time (the socket carries the connection timeout) rather
        than byte-at-a-time; keepalive comment lines do not start with ``data: ``.
        """
        end = time.monotonic() + deadline
        while time.monotonic() < end:
            line = resp.readline()
            if not line:
                break
            decoded = line.decode().rstrip("\n")
            if decoded.startswith("data: "):
                return decoded[len("data: ") :]
        raise AssertionError("no SSE data frame arrived")


if __name__ == "__main__":
    unittest.main()
