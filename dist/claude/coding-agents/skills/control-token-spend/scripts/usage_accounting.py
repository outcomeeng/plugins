"""Bounded local transcript accounting and advisory spending signals."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any, Final

# Native transcript content and exported evidence are heterogeneous JSON boundaries.
Json = dict[str, Any]
UTC: Final = dt.timezone.utc
SCHEMA_VERSION: Final = 1
ALERT_ENV: Final = "SPX_USAGE_ALERT_USD"
BUDGET_ENV: Final = "SPX_USAGE_WEEKLY_BUDGET_USD"
RESET_ENV: Final = "SPX_USAGE_RESET_AT"
DEFAULT_ALERT: Final = Decimal("20")
DEFAULT_ROOT: Final = (
    Path.home() / "Library/Application Support/Outcome Engineering/usage-control"
)
DEFAULT_PROJECTS: Final = Path.home() / ".claude/projects"
WEEK: Final = dt.timedelta(days=7)
QUARTER: Final = dt.timedelta(minutes=15)
HOUR: Final = dt.timedelta(hours=1)
FIELDS: Final = (
    "input_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
    "output_tokens",
)
TOKEN_KEYS: Final = ("uncached_input", "cache_read", "cache_write", "output")
PRICE_SOURCE: Final = "https://platform.claude.com/docs/en/about-claude/pricing"
PRICE_DATE: Final = "2026-10-09"
MILLION: Final = Decimal(1_000_000)
MAX_CHUNK: Final = 8 * 1024 * 1024
MAX_BYTES: Final = 32 * 1024 * 1024
MAX_LINE: Final = 2 * 1024 * 1024
MAX_ENTRIES: Final = 20_000
MAX_FILES: Final = 128
MAX_SECONDS: Final = 30
MAX_QUERY_ROWS: Final = 100_000
MAX_GROUPS: Final = 2_000
MAX_GAPS: Final = 200
MAX_REGISTERED_FILES: Final = 50_000
MAX_REGISTERED_DIRECTORIES: Final = 10_000
EXCERPT_CHARS: Final = 2_000
MAX_BEHAVIOR: Final = 20_000
RETENTION_DAYS: Final = 14
ANCHOR_BYTES: Final = 256
STATE_NAME: Final = "state.sqlite3"
LOCK_NAME: Final = "worker.lock"


class SignalKind(str, Enum):
    ROLLING_THRESHOLD = "rolling_threshold"
    WEEKLY_BUDGET = "weekly_budget"
    WEEKLY_PACE = "weekly_pace"


def iso(value: dt.datetime) -> str:
    return (
        value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    )


def timestamp(raw: str, field: str = "timestamp") -> dt.datetime:
    try:
        value = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(
            f"{field}: use an ISO 8601 timestamp with an explicit UTC offset; received {raw!r}"
        ) from error
    if value.tzinfo is None:
        raise ValueError(f"{field}: timezone is required; use a timestamp ending in Z")
    return value.astimezone(UTC)


def money(raw: str, field: str) -> Decimal:
    try:
        value = Decimal(raw)
    except InvalidOperation as error:
        raise ValueError(
            f"{field}: use a positive finite decimal; received {raw!r}"
        ) from error
    if not value.is_finite() or value <= 0:
        raise ValueError(f"{field}: use a positive finite decimal; received {raw!r}")
    return value


@dataclass(frozen=True)
class Config:
    root: Path
    projects: Path
    reset: dt.datetime
    alert: Decimal = DEFAULT_ALERT
    weekly_budget: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.root.is_absolute() or not self.projects.is_absolute():
            raise ValueError("root and projects: use absolute resolved paths")
        object.__setattr__(self, "root", self.root.resolve())
        object.__setattr__(self, "projects", self.projects.resolve())
        if self.root.is_relative_to(self.projects) or self.projects.is_relative_to(
            self.root
        ):
            raise ValueError(
                "root and projects: use disjoint state and transcript directories"
            )
        if self.reset.tzinfo is None or self.reset.utcoffset() != dt.timedelta(0):
            raise ValueError(f"{RESET_ENV}: use an aware UTC reset timestamp")
        money(str(self.alert), ALERT_ENV)
        if self.weekly_budget is not None:
            money(str(self.weekly_budget), BUDGET_ENV)

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str], root: Path, projects: Path
    ) -> Config:
        raw = environment.get(RESET_ENV)
        if not raw:
            raise ValueError(
                f"{RESET_ENV}: supply the UTC weekly reset timestamp, for example 2026-10-09T00:00:00Z"
            )
        reset = timestamp(raw, RESET_ENV)
        if not raw.endswith("Z") and not raw.endswith("+00:00"):
            raise ValueError(
                f"{RESET_ENV}: use an explicit UTC timestamp ending in Z or +00:00"
            )
        budget = (
            money(environment[BUDGET_ENV], BUDGET_ENV)
            if BUDGET_ENV in environment
            else None
        )
        root, projects = root.expanduser().resolve(), projects.expanduser().resolve()
        if root.is_relative_to(projects) or projects.is_relative_to(root):
            raise ValueError(
                "root and projects: use disjoint state and transcript directories"
            )
        return cls(
            root,
            projects,
            reset,
            money(environment.get(ALERT_ENV, str(DEFAULT_ALERT)), ALERT_ENV),
            budget,
        )

    def period(self, now: dt.datetime) -> tuple[dt.datetime, dt.datetime]:
        if now < self.reset:
            raise ValueError(
                f"{RESET_ENV}: reset anchor {iso(self.reset)} is later than measurement end {iso(now)}"
            )
        start = self.reset + ((now - self.reset) // WEEK) * WEEK
        return start, start + WEEK

    def effective(self) -> Json:
        return {
            ALERT_ENV: str(self.alert),
            BUDGET_ENV: str(self.weekly_budget) if self.weekly_budget else None,
            RESET_ENV: iso(self.reset),
            "root": str(self.root),
            "projects": str(self.projects),
        }


@dataclass(frozen=True)
class Price:
    input: Decimal
    read: Decimal
    write5: Decimal
    write1: Decimal
    output: Decimal


PRICES: Final = {
    "claude-opus-5-5": Price(*(Decimal(v) for v in ("4", ".2", "5", "8", "20"))),
    "claude-sonnet-5-5": Price(*(Decimal(v) for v in ("2", ".1", "2.5", "4", "10"))),
    "claude-opus-4-6": Price(*(Decimal(v) for v in ("5", ".5", "6.25", "10", "25"))),
    "claude-sonnet-4-6": Price(*(Decimal(v) for v in ("3", ".3", "3.75", "6", "15"))),
}


def encoded(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def native(source: Path, row: Json) -> tuple[str, str, bool]:
    child = source.parent.name == "subagents"
    parent = (
        source.parent.parent.name if child else str(row.get("sessionId") or source.stem)
    )
    return (source.stem if child else parent), parent, child


def request(row: Json, source: Path) -> tuple[Json | None, list[str]]:
    if row.get("type") != "assistant":
        return None, []
    message = row.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("usage"), dict):
        return None, ["assistant usage absent"]
    usage = message["usage"]
    if not row.get("timestamp") or not message.get("id"):
        return None, ["assistant timestamp or message.id absent"]
    stamp = timestamp(str(row["timestamp"]))
    session, parent, child = native(source, row)
    gaps: list[str] = []
    tokens: list[int] = []
    for field in FIELDS:
        value = usage.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            gaps.append(f"invalid or absent usage.{field}")
            value = 0
        tokens.append(value)
    if not any(tokens):
        return None, gaps
    creation = usage.get("cache_creation")
    write5 = (
        creation.get("ephemeral_5m_input_tokens")
        if isinstance(creation, dict)
        else None
    )
    write1 = (
        creation.get("ephemeral_1h_input_tokens")
        if isinstance(creation, dict)
        else None
    )
    ttl_known = (
        isinstance(write5, int)
        and not isinstance(write5, bool)
        and write5 >= 0
        and isinstance(write1, int)
        and not isinstance(write1, bool)
        and write1 >= 0
        and write5 + write1 == tokens[2]
    ) or tokens[2] == 0
    if not ttl_known:
        gaps.append(
            "cache-write duration absent or inconsistent; estimate uses five-minute lower bound"
        )
        write5, write1 = tokens[2], 0
    if tokens[2] == 0:
        write5, write1 = 0, 0
    model = str(message.get("model") or "unknown")
    speed = usage.get("speed", "standard")
    tier = usage.get("service_tier", "standard")
    priced = (
        model in PRICES and speed in (None, "standard") and tier in (None, "standard")
    )
    if not priced:
        gaps.append(
            f"unsupported pricing: model={model}, speed={speed}, service_tier={tier}"
        )
    identity = encoded([parent, session, message["id"]])
    result = {
        "identity": identity,
        "stamp": iso(stamp),
        "session": session,
        "parent": parent,
        "child": child,
        "model": model,
        "workspace": str(row.get("cwd") or "unknown"),
        "tokens": tokens,
        "write5": write5,
        "write1": write1,
        "priced": priced,
        "ttl_known": ttl_known,
        "source": str(source),
        "uuid": str(row.get("uuid") or "unknown"),
        "gaps": gaps,
    }
    return result, gaps


def reconcile(old: Json, new: Json) -> Json:
    # Native streaming snapshots carry cumulative usage, rather than deltas.
    result = dict(new)
    result["stamp"] = min(old["stamp"], new["stamp"])
    result["tokens"] = [
        max(a, b) for a, b in zip(old["tokens"], new["tokens"], strict=True)
    ]
    if old["tokens"][2] > new["tokens"][2]:
        result["write5"], result["write1"], result["ttl_known"] = (
            old["write5"],
            old["write1"],
            old["ttl_known"],
        )
    elif (
        old["tokens"][2] == new["tokens"][2]
        and old["ttl_known"]
        and not new["ttl_known"]
    ):
        result["write5"], result["write1"], result["ttl_known"] = (
            old["write5"],
            old["write1"],
            True,
        )
    result["gaps"] = sorted(set(old["gaps"] + new["gaps"]))
    for field in FIELDS:
        gap = f"invalid or absent usage.{field}"
        if gap not in old["gaps"] or gap not in new["gaps"]:
            result["gaps"] = [item for item in result["gaps"] if item != gap]
    if result["ttl_known"]:
        result["gaps"] = [
            item
            for item in result["gaps"]
            if not item.startswith("cache-write duration absent or inconsistent")
        ]
    if new["model"] == "unknown" and old["model"] != "unknown":
        result["model"], result["priced"] = old["model"], old["priced"]
    if old["model"] != new["model"] and "unknown" not in (old["model"], new["model"]):
        result["priced"] = False
        result["gaps"].append(
            "conflicting models for one native request; pricing unavailable"
        )
    if result["priced"]:
        result["gaps"] = [
            item
            for item in result["gaps"]
            if not item.startswith("unsupported pricing: model=unknown,")
        ]
    return result


def cost(value: Json) -> dict[str, Decimal] | None:
    rate = PRICES.get(value["model"])
    if rate is None or not value["priced"]:
        return None
    inputs, reads, _, outputs = value["tokens"]
    return dict(
        zip(
            TOKEN_KEYS,
            (
                Decimal(inputs) * rate.input / MILLION,
                Decimal(reads) * rate.read / MILLION,
                (
                    Decimal(value["write5"]) * rate.write5
                    + Decimal(value["write1"]) * rate.write1
                )
                / MILLION,
                Decimal(outputs) * rate.output / MILLION,
            ),
            strict=True,
        )
    )


class Evidence:
    def __init__(
        self, config: Config, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.config = config
        self.clock = clock
        config.root.mkdir(parents=True, exist_ok=True)
        if (config.root / STATE_NAME).is_symlink():
            raise ValueError(f"Managed state is symlinked: {config.root / STATE_NAME}")
        self.db = sqlite3.connect(config.root / STATE_NAME, timeout=1)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA cache_size=-4096")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS directories(path TEXT PRIMARY KEY,cursor INTEGER,next_scan REAL);
        CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY,device INTEGER,inode INTEGER,offset INTEGER,
          tail BLOB,anchor TEXT,discard INTEGER,last_visit REAL);
        CREATE TABLE IF NOT EXISTS requests(identity TEXT PRIMARY KEY,stamp TEXT,session TEXT,parent TEXT,
          model TEXT,workspace TEXT,payload TEXT);
        CREATE INDEX IF NOT EXISTS requests_stamp ON requests(stamp);
        CREATE TABLE IF NOT EXISTS behavior(identity TEXT PRIMARY KEY,stamp TEXT,session TEXT,parent TEXT,
          kind TEXT,tool TEXT,signature TEXT,characters INTEGER,error INTEGER,payload TEXT);
        CREATE INDEX IF NOT EXISTS behavior_stamp ON behavior(stamp);
        CREATE TABLE IF NOT EXISTS signals(identity TEXT PRIMARY KEY,payload TEXT,stamp TEXT);
        """)
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO directories VALUES(?,0,0)",
                (str(config.projects),),
            )
            schema = self.setting("schema_version")
            if schema and schema != str(SCHEMA_VERSION):
                raise ValueError(
                    f"Unsupported state schema {schema}; choose a separate state root"
                )
            self.set_setting("schema_version", str(SCHEMA_VERSION))

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> Evidence:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def setting(self, key: str) -> str | None:
        row = self.db.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ).fetchone()
        return str(row[0]) if row else None

    def set_setting(self, key: str, value: str) -> None:
        self.db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, value))

    def visit(self) -> int:
        value = int(self.setting("visit_sequence") or "0") + 1
        self.set_setting("visit_sequence", str(value))
        return value

    def remember_gap(self, gap: str) -> None:
        remembered = json.loads(self.setting("ingestion_gaps") or "[]")
        self.set_setting(
            "ingestion_gaps", encoded(sorted(set(remembered + [gap]))[:MAX_GAPS])
        )

    def discover(self, deadline: float) -> list[str]:
        gaps: list[str] = []
        visited = 0
        registered_files = int(
            self.db.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        )
        registered_directories = int(
            self.db.execute("SELECT COUNT(*) FROM directories").fetchone()[0]
        )
        directories = self.db.execute(
            "SELECT * FROM directories ORDER BY next_scan,path LIMIT ?", (MAX_FILES,)
        ).fetchall()
        for directory in directories:
            if self.clock() >= deadline or visited >= MAX_ENTRIES:
                gaps.append(
                    "discovery bound reached; unvisited directories resume next invocation"
                )
                break
            cursor = int(directory["cursor"])
            position = 0
            complete = True
            try:
                with os.scandir(directory["path"]) as entries, self.db:
                    for entry in entries:
                        visited += 1
                        position += 1
                        if self.clock() >= deadline or visited >= MAX_ENTRIES:
                            complete = False
                            break
                        if position <= cursor or entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            if registered_directories >= MAX_REGISTERED_DIRECTORIES:
                                gaps.append(
                                    "directory registration bound reached; configure a narrower transcript root"
                                )
                            else:
                                changed = self.db.execute(
                                    "INSERT OR IGNORE INTO directories VALUES(?,0,0)",
                                    (entry.path,),
                                ).rowcount
                                registered_directories += changed
                        elif entry.is_file(
                            follow_symlinks=False
                        ) and entry.name.endswith(".jsonl"):
                            if registered_files >= MAX_REGISTERED_FILES:
                                gaps.append(
                                    "file registration bound reached; configure a narrower transcript root"
                                )
                            else:
                                st = entry.stat(follow_symlinks=False)
                                changed = self.db.execute(
                                    "INSERT OR IGNORE INTO files VALUES(?,?,?,?,?,?,0,0)",
                                    (entry.path, st.st_dev, st.st_ino, 0, b"", ""),
                                ).rowcount
                                registered_files += changed
                    self.db.execute(
                        "UPDATE directories SET cursor=?,next_scan=? WHERE path=?",
                        (
                            0 if complete else max(cursor, position - 1),
                            self.visit(),
                            directory["path"],
                        ),
                    )
                if not complete:
                    gaps.append(
                        f"incomplete directory discovery: {directory['path']}; directory cursor={position}"
                    )
                    if cursor >= MAX_ENTRIES - 1:
                        gaps.append(
                            f"directory exceeds discovery capacity: {directory['path']}; configure a narrower transcript root"
                        )
            except OSError as error:
                gaps.append(f"directory unavailable: {directory['path']}: {error}")
                with self.db:
                    self.db.execute(
                        "UPDATE directories SET next_scan=? WHERE path=?",
                        (self.visit(), directory["path"]),
                    )
        return gaps

    def behavior(
        self, row: Json, source: Path, stamp: str, session: str, parent: str
    ) -> None:
        message = row.get("message")
        content = message.get("content", []) if isinstance(message, dict) else []
        blocks = (
            content
            if isinstance(content, list)
            else [{"type": "text", "text": str(content)}]
        )
        if row.get("type") == "user" and any(
            isinstance(block, dict) and block.get("type") == "text" for block in blocks
        ):
            identity = encoded(
                [
                    str(source),
                    row.get("uuid")
                    or hashlib.sha256(encoded(row).encode()).hexdigest(),
                    "user_turn",
                ]
            )
            self.db.execute(
                "INSERT OR REPLACE INTO behavior VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    identity,
                    stamp,
                    session,
                    parent,
                    "user_turn",
                    "",
                    "",
                    0,
                    0,
                    encoded({"kind": "user_turn"}),
                ),
            )
        for index, block in enumerate(blocks):
            if not isinstance(block, dict) or block.get("type") not in (
                "tool_use",
                "tool_result",
            ):
                continue
            kind = str(block["type"])
            tool = str(block.get("name") or "unknown") if kind == "tool_use" else ""
            raw = (
                encoded(block.get("input", {}))
                if kind == "tool_use"
                else encoded(block.get("content", ""))
            )
            row_id = (
                row.get("uuid") or hashlib.sha256(encoded(row).encode()).hexdigest()
            )
            identity = encoded(
                [
                    str(source),
                    row_id,
                    block.get("id") or block.get("tool_use_id"),
                    kind,
                    index,
                ]
            )
            signature = (
                hashlib.sha256(encoded([tool, block.get("input")]).encode()).hexdigest()
                if kind == "tool_use"
                else ""
            )
            payload = {
                "source": str(source),
                "uuid": row.get("uuid"),
                "stamp": stamp,
                "session": session,
                "parent": parent,
                "kind": kind,
                "tool": tool,
                "tool_id": block.get("id") or block.get("tool_use_id"),
                "excerpt": raw[:EXCERPT_CHARS],
                "characters": len(raw),
                "truncated": len(raw) > EXCERPT_CHARS,
                "arguments": block.get("input")
                if kind == "tool_use" and len(raw) <= EXCERPT_CHARS
                else None,
                "explicit_error": bool(block.get("is_error")),
            }
            self.db.execute(
                "INSERT OR REPLACE INTO behavior VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    identity,
                    stamp,
                    session,
                    parent,
                    kind,
                    tool,
                    signature,
                    len(raw),
                    int(bool(block.get("is_error"))),
                    encoded(payload),
                ),
            )

    def ingest(
        self, row: Json, source: Path, lower: dt.datetime, end: dt.datetime
    ) -> list[str]:
        if not row.get("timestamp"):
            gaps = (
                ["transcript timestamp absent"]
                if row.get("type") in ("assistant", "user")
                else []
            )
            for gap in gaps:
                self.remember_gap(f"{source}: {gap}")
            return gaps
        parsed = timestamp(str(row["timestamp"]))
        if parsed < lower:
            return []
        session, parent, _ = native(source, row)
        self.behavior(row, source, iso(parsed), session, parent)
        value, gaps = request(row, source)
        if value is None:
            for gap in gaps:
                self.remember_gap(f"{source}: {gap}")
            return gaps
        if parsed > end:
            gaps.append(
                "future transcript timestamp retained; excluded from current measurement"
            )
        previous = self.db.execute(
            "SELECT payload FROM requests WHERE identity=?", (value["identity"],)
        ).fetchone()
        if previous:
            value = reconcile(json.loads(previous[0]), value)
        self.db.execute(
            "INSERT OR REPLACE INTO requests VALUES(?,?,?,?,?,?,?)",
            (
                value["identity"],
                value["stamp"],
                session,
                parent,
                value["model"],
                value["workspace"],
                encoded(value),
            ),
        )
        return gaps

    def collect(self, end: dt.datetime) -> Json:
        lower, _ = self.config.period(end)
        deadline = self.clock() + MAX_SECONDS
        gaps = self.discover(deadline)
        read_bytes = rows = files = 0
        if not self.config.projects.is_dir():
            gaps.append(f"transcript root absent: {self.config.projects}")
        targets = self.db.execute(
            "SELECT * FROM files ORDER BY last_visit,path LIMIT ?", (MAX_FILES,)
        ).fetchall()
        for target in targets:
            if self.clock() >= deadline or read_bytes >= MAX_BYTES:
                gaps.append(
                    "collection bound reached; remaining file offsets resume next invocation"
                )
                break
            path = Path(target["path"])
            try:
                if path.is_symlink() or not path.resolve().is_relative_to(
                    self.config.projects
                ):
                    gaps.append(
                        f"transcript outside configured root or symlinked: {path}"
                    )
                    continue
                with path.open("rb") as stream:
                    st = os.fstat(stream.fileno())
                    offset, tail, discard = (
                        int(target["offset"]),
                        bytes(target["tail"]),
                        bool(target["discard"]),
                    )
                    stream.seek(max(0, offset - ANCHOR_BYTES))
                    anchor = (
                        hashlib.sha256(
                            stream.read(min(offset, ANCHOR_BYTES))
                        ).hexdigest()
                        if offset
                        else ""
                    )
                    if (
                        (st.st_dev, st.st_ino) != (target["device"], target["inode"])
                        or st.st_size < offset
                        or (offset and target["anchor"] != anchor)
                    ):
                        offset, tail, discard = 0, b"", False
                        gaps.append(
                            f"transcript rotated, truncated or changed before cursor: {path}; replay reconciles request identities"
                        )
                    stream.seek(offset)
                    chunk = stream.read(min(MAX_CHUNK, MAX_BYTES - read_bytes))
                    read_bytes += len(chunk)
                    pieces = (tail + chunk).split(b"\n")
                    pending = pieces.pop()
                    consumed = 0
                    with self.db:
                        for line in pieces:
                            if self.clock() >= deadline:
                                gaps.append(
                                    f"collection time bound reached: {path}; unprocessed bytes replay next invocation"
                                )
                                break
                            consumed += len(line) + 1
                            if discard:
                                discard = False
                                continue
                            if not line.strip():
                                continue
                            if len(line) > MAX_LINE:
                                gap = f"oversized transcript row skipped: {path}"
                                gaps.append(gap)
                                self.remember_gap(gap)
                                continue
                            try:
                                row = json.loads(line)
                                if not isinstance(row, dict):
                                    raise ValueError("JSON row is not an object")
                                gaps.extend(
                                    f"{path}: {gap}"
                                    for gap in self.ingest(row, path, lower, end)
                                )
                                rows += 1
                            except (ValueError, TypeError, UnicodeError) as error:
                                gap = f"invalid transcript row: {path}: {error}"
                                gaps.append(gap)
                                self.remember_gap(gap)
                            if len(gaps) > MAX_GAPS:
                                gaps = sorted(set(gaps))[:MAX_GAPS]
                        if consumed < sum(len(piece) + 1 for piece in pieces):
                            # Rewind to the first unprocessed row, preserving its initial fragment.
                            offset += max(0, consumed - len(tail))
                            pending = tail if consumed == 0 else b""
                        else:
                            offset += len(chunk)
                        if len(pending) > MAX_LINE:
                            pending, discard = b"", True
                            gaps.append(
                                f"oversized pending row discarded until its next newline: {path}"
                            )
                        stream.seek(max(0, offset - ANCHOR_BYTES))
                        next_anchor = (
                            hashlib.sha256(
                                stream.read(min(offset, ANCHOR_BYTES))
                            ).hexdigest()
                            if offset
                            else ""
                        )
                        self.db.execute(
                            "UPDATE files SET device=?,inode=?,offset=?,tail=?,anchor=?,discard=?,last_visit=? WHERE path=?",
                            (
                                st.st_dev,
                                st.st_ino,
                                offset,
                                pending,
                                next_anchor,
                                int(discard),
                                self.visit(),
                                str(path),
                            ),
                        )
                        files += 1
                    if st.st_size > offset:
                        gaps.append(
                            f"file import incomplete: {path}; offset {offset} of {st.st_size}"
                        )
            except OSError as error:
                gaps.append(f"transcript unavailable: {path}: {error}")
                with self.db:
                    self.db.execute(
                        "UPDATE files SET last_visit=? WHERE path=?",
                        (self.visit(), str(path)),
                    )
        with self.db:
            pending_directories = int(
                self.db.execute(
                    "SELECT COUNT(*) FROM directories WHERE next_scan=0 OR cursor>0"
                ).fetchone()[0]
            )
            pending_files = int(
                self.db.execute(
                    "SELECT COUNT(*) FROM files WHERE last_visit=0 OR length(tail)>0 OR discard=1"
                ).fetchone()[0]
            )
            if pending_directories or pending_files:
                gaps.append(
                    f"import pending: {pending_directories} directories and {pending_files} files or partial rows"
                )
            if (
                len(targets) == MAX_FILES
                and registered_total(self.db, "files") > MAX_FILES
            ):
                gaps.append(
                    "file visit page bounded; changes in unvisited files remain unknown until a later invocation"
                )
            if registered_total(self.db, "directories") > MAX_FILES:
                gaps.append(
                    "directory visit page bounded; changes in unvisited directories remain unknown until a later invocation"
                )
            cutoff = iso(end - dt.timedelta(days=RETENTION_DAYS))
            self.db.execute("DELETE FROM requests WHERE stamp<?", (cutoff,))
            self.db.execute("DELETE FROM behavior WHERE stamp<?", (cutoff,))
            self.db.execute("DELETE FROM signals WHERE stamp<?", (cutoff,))
            self.db.execute(
                "DELETE FROM behavior WHERE identity IN (SELECT identity FROM behavior ORDER BY stamp DESC LIMIT -1 OFFSET ?)",
                (MAX_BEHAVIOR,),
            )
            removed_behavior = self.db.execute("SELECT changes()").fetchone()[0]
            if removed_behavior:
                self.set_setting(
                    "behavior_retention_cutoff",
                    str(
                        self.db.execute("SELECT MIN(stamp) FROM behavior").fetchone()[0]
                    ),
                )
            gaps.extend(json.loads(self.setting("ingestion_gaps") or "[]"))
            result = {
                "end_utc": iso(end),
                "import_start_utc": iso(lower),
                "bytes_read": read_bytes,
                "rows_read": rows,
                "files_visited": files,
                "gaps": sorted(set(gaps))[:MAX_GAPS],
                "history_complete": not gaps,
                "bounds": {
                    "bytes": MAX_BYTES,
                    "files": MAX_FILES,
                    "directory_entries": MAX_ENTRIES,
                    "seconds": MAX_SECONDS,
                    "row_bytes": MAX_LINE,
                },
            }
            self.set_setting("collection", encoded(result))
        return result

    def measure(self, start: dt.datetime, end: dt.datetime) -> Json:
        if start >= end:
            raise ValueError("measurement window: start must precede end")
        deadline = self.clock() + MAX_SECONDS
        self.db.set_progress_handler(lambda: int(self.clock() >= deadline), 1_000)
        try:
            return self._measure(start, end)
        finally:
            self.db.set_progress_handler(None, 0)

    def _measure(self, start: dt.datetime, end: dt.datetime) -> Json:
        groups: dict[str, dict[str, Json]] = {
            key: {} for key in ("sessions", "models", "workspaces", "roles")
        }
        result: Json = {
            "schema_version": SCHEMA_VERSION,
            "start_utc": iso(start),
            "end_exclusive_utc": iso(end),
            "requests": 0,
            **dict.fromkeys(TOKEN_KEYS, 0),
            "api_equivalent_usd": 0.0,
            "cost_components": dict.fromkeys(TOKEN_KEYS, 0.0),
            "unpriced_requests": 0,
            "pricing_assumption_requests": 0,
            "child_requests": 0,
            "gaps": [],
            "pricing": {
                "source": PRICE_SOURCE,
                "effective_date": PRICE_DATE,
                "basis": "standard first-party API list prices; unknown cache duration uses five-minute lower bound",
            },
            "verified_outputs": [],
            "attribution": "Transcript activity is measured; delivery, usefulness and exact skill/tool token costs are unknown.",
        }
        values = self.db.execute(
            "SELECT payload FROM requests WHERE stamp>=? AND stamp<? ORDER BY stamp,identity LIMIT ?",
            (iso(start), iso(end), MAX_QUERY_ROWS + 1),
        )
        gaps: set[str] = set()
        for index, row in enumerate(values):
            if index >= MAX_QUERY_ROWS:
                gaps.add("measurement row bound reached; totals are partial")
                break
            value = json.loads(row[0])
            components = cost(value)
            amount = sum(components.values(), Decimal(0)) if components else Decimal(0)
            result["requests"] += 1
            result["unpriced_requests"] += components is None
            result["pricing_assumption_requests"] += not value["ttl_known"]
            result["child_requests"] += bool(value["child"])
            context = sum(value["tokens"][:3])
            for key, token in zip(TOKEN_KEYS, value["tokens"], strict=True):
                result[key] += token
                result["cost_components"][key] += (
                    float(components[key]) if components else 0.0
                )
            result["api_equivalent_usd"] += float(amount)
            gaps.update(value["gaps"])
            for category, identity in (
                ("sessions", value["session"]),
                ("models", value["model"]),
                ("workspaces", value["workspace"]),
                ("roles", "native_child" if value["child"] else "native_parent"),
            ):
                if (
                    identity not in groups[category]
                    and len(groups[category]) >= MAX_GROUPS
                ):
                    identity = "other_groups_at_bound"
                    gaps.add(f"{category} group bound reached")
                group = groups[category].setdefault(
                    identity,
                    {
                        "requests": 0,
                        **dict.fromkeys(TOKEN_KEYS, 0),
                        "api_equivalent_usd": 0.0,
                        "cost_components": dict.fromkeys(TOKEN_KEYS, 0.0),
                        "first_utc": value["stamp"],
                        "last_utc": value["stamp"],
                        "model": value["model"],
                        "parent": value["parent"],
                        "child": value["child"],
                        "peak_context": 0,
                        "context_sum": 0,
                        "early_contexts": [],
                        "late_contexts": [],
                        "early_costs": [],
                        "late_costs": [],
                    },
                )
                group["requests"] += 1
                group["last_utc"] = value["stamp"]
                group["peak_context"] = max(group["peak_context"], context)
                group["context_sum"] += context
                group["model"] = (
                    value["model"] if group["model"] == value["model"] else "multiple"
                )
                for key, token in zip(TOKEN_KEYS, value["tokens"], strict=True):
                    group[key] += token
                    group["cost_components"][key] += (
                        float(components[key]) if components else 0.0
                    )
                group["api_equivalent_usd"] += float(amount)
                if len(group["early_contexts"]) < 10:
                    group["early_contexts"].append(context)
                    group["early_costs"].append(float(amount))
                group["late_contexts"] = (group["late_contexts"] + [context])[-10:]
                group["late_costs"] = (group["late_costs"] + [float(amount)])[-10:]
        for category_groups in groups.values():
            for group in category_groups.values():
                size = min(10, max(1, group["requests"] // 4))
                early = sum(group.pop("early_contexts")[:size]) / size
                late = sum(group.pop("late_contexts")[-size:]) / size
                early_cost = sum(group.pop("early_costs")[:size]) / size
                late_cost = sum(group.pop("late_costs")[-size:]) / size
                group.update(
                    {
                        "early_context_mean": early,
                        "late_context_mean": late,
                        "context_growth_ratio": late / early if early else None,
                        "early_cost_mean": early_cost,
                        "late_cost_mean": late_cost,
                        "cost_growth_ratio": late_cost / early_cost
                        if early_cost
                        else None,
                        "duration_seconds": (
                            timestamp(group["last_utc"]) - timestamp(group["first_utc"])
                        ).total_seconds(),
                        "mean_context": group.pop("context_sum") / group["requests"],
                        "sample_turns": size,
                        "marginal_cost_includes_unpriced_zero": bool(
                            result["unpriced_requests"]
                        ),
                        "share_measured_cost": group["api_equivalent_usd"]
                        / result["api_equivalent_usd"]
                        if result["api_equivalent_usd"]
                        else None,
                    }
                )
        collection = json.loads(self.setting("collection") or "{}")
        gaps.update(collection.get("gaps", []))
        behavior_cutoff = self.setting("behavior_retention_cutoff")
        if behavior_cutoff and iso(start) < behavior_cutoff:
            gaps.add("behavior evidence before retained-row cutoff is incomplete")
        if not collection:
            gaps.add("collection has not run")
        lower = collection.get("import_start_utc")
        if not lower or iso(start) < lower:
            gaps.add("measurement starts before configured import coverage")
        result.update(groups)
        result["gaps"] = sorted(gaps)[:MAX_GAPS]
        result["coverage"] = collection
        total_input = sum(result[key] for key in TOKEN_KEYS[:3])
        result["cache_read_share"] = (
            result["cache_read"] / total_input if total_input else None
        )
        result["context_input_tokens"] = total_input
        result["subscription_usage_conversion"] = None
        return result


def registered_total(db: sqlite3.Connection, table: str) -> int:
    if table not in ("files", "directories"):
        raise ValueError("registered_total: supported tables are files and directories")
    return int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def signals(
    config: Config, current: Json, weekly: Json, end: dt.datetime
) -> list[Json]:
    start, period_end = config.period(end)
    budget = config.weekly_budget
    expected = (
        budget
        * Decimal(str((end - start).total_seconds()))
        / Decimal(str(WEEK.total_seconds()))
        if budget
        else None
    )
    candidates = [
        (
            SignalKind.ROLLING_THRESHOLD,
            Decimal(str(current["api_equivalent_usd"])),
            config.alert,
            current,
        )
    ]
    if budget:
        candidates.append(
            (
                SignalKind.WEEKLY_BUDGET,
                Decimal(str(weekly["api_equivalent_usd"])),
                budget,
                weekly,
            )
        )
        if expected is not None and expected > 0:
            candidates.append(
                (
                    SignalKind.WEEKLY_PACE,
                    Decimal(str(weekly["api_equivalent_usd"])),
                    expected,
                    weekly,
                )
            )
    result = []
    for kind, amount, ceiling, measurement in candidates:
        if amount < ceiling:
            continue
        # Calendar bucket identifies one rolling occurrence; weekly signals identify one reset period.
        occurrence = (
            iso(end.replace(minute=end.minute // 15 * 15, second=0, microsecond=0))
            if kind == SignalKind.ROLLING_THRESHOLD
            else iso(start)
        )
        identity = hashlib.sha256(
            encoded([kind, occurrence, config.effective()]).encode()
        ).hexdigest()
        result.append(
            {
                "identity": identity,
                "kind": kind,
                "advisory": True,
                "api_equivalent_usd": str(amount),
                "ceiling_usd": str(ceiling),
                "start_utc": measurement["start_utc"],
                "end_exclusive_utc": measurement["end_exclusive_utc"],
                "reset_period_start_utc": iso(start),
                "reset_period_end_utc": iso(period_end),
                "expected_elapsed_spend_usd": str(expected)
                if expected is not None
                else None,
                "configuration": config.effective(),
                "gaps": measurement["gaps"],
                "subscription_usage_conversion": None,
            }
        )
    return result
