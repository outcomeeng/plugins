"""Generated domains for the position-direction scripts."""

from __future__ import annotations

import string
from dataclasses import dataclass
from types import ModuleType

from hypothesis import strategies as st

DIGIT_FREE_ALPHABET = string.ascii_letters + " ,.:-\n"


def position_names() -> st.SearchStrategy[str]:
    """Names of watched positions."""
    return st.from_regex(r"[A-Z][a-z]{2,9}( [A-Z][a-z]{2,9}){0,2}", fullmatch=True)


def handles() -> st.SearchStrategy[str]:
    """Pane identifiers and agent names a backend reports."""
    return st.from_regex(r"[a-z][a-z0-9-]{2,15}", fullmatch=True)


def worktree_paths(root: str) -> st.SearchStrategy[str]:
    """Absolute paths under a root, without a trailing separator."""
    segment = st.from_regex(r"[a-z][a-z0-9_-]{1,9}", fullmatch=True)
    return st.lists(segment, min_size=1, max_size=3).map(
        lambda parts: f"{root}/" + "/".join(parts)
    )


def status_line(percent: int) -> str:
    """A Claude Code status line as the pane shows it, e.g. `(659k/1M tokens) 66%`."""
    return f"Opus 5 (1M context) ({percent * 10}k/1M tokens) {percent}%"


def every_percent() -> range:
    """Every context percentage a status line can show."""
    return range(0, 101)


def ticking(base: str, tick: int) -> str:
    """Pane text whose only change between ticks is a counter."""
    return f"{base} {tick}s elapsed"


def digit_free_texts() -> st.SearchStrategy[str]:
    """Pane text without a digit, so ticking counters never count as activity."""
    return st.text(alphabet=DIGIT_FREE_ALPHABET, min_size=8, max_size=80).filter(
        lambda text: text.strip() != ""
    )


def senders() -> st.SearchStrategy[str]:
    return st.from_regex(r"[A-Z][a-z]+[A-Z][a-z]+", fullmatch=True)


def subjects() -> st.SearchStrategy[str]:
    """Mail subjects and adapter messages: one line, no digits, no surrounding space."""
    return st.text(
        alphabet=DIGIT_FREE_ALPHABET.replace("\n", ""), min_size=1, max_size=40
    ).filter(lambda text: text == text.strip())


def states(environment: ModuleType) -> st.SearchStrategy[object]:
    """The session states the scripts read, from the source-owned enumeration."""
    return st.sampled_from(tuple(environment.State))


def invalid_intervals() -> st.SearchStrategy[str]:
    """Values the `--every` option must reject: non-positive numbers and non-numbers."""
    non_positive = st.one_of(
        st.integers(max_value=0).map(str),
        st.floats(max_value=0.0, allow_nan=False, allow_infinity=False).map(repr),
    )
    words = st.text(alphabet=string.ascii_letters, min_size=1, max_size=8)
    # Spellings Python's float() reads that are not finite numbers.
    non_finite = st.sampled_from(("inf", "-inf", "nan", "infinity"))
    return st.one_of(non_positive, words, non_finite)


@dataclass(frozen=True)
class RosterCase:
    """A watch file, the inventories its backends answered, and what each entry should show.

    The case is built from the plan, never read back from the roster: each
    watched position is live, absent, or on a backend whose inventory failed,
    and each group lists its members.
    """

    watch: dict
    inventories: dict
    live: dict[str, object]  # position -> its live session
    absent: list[str]  # positions with no session
    failed: dict[str, str]  # position or group label -> the inventory error text
    members: dict[str, list[object]]  # group label -> the members under its prefix


@st.composite
def roster_cases(draw: st.DrawFn, environment: ModuleType) -> RosterCase:
    backend_names = sorted(environment.BACKENDS)
    failed_backends = {
        name: draw(subjects()) for name in backend_names if draw(st.booleans())
    }
    used_paths: list[str] = []

    def fresh_path(root: str) -> str:
        """A path that is neither a prefix of nor prefixed by any path drawn so far."""
        path = draw(
            worktree_paths(root).filter(
                lambda candidate: (
                    not any(
                        (candidate + "/").startswith(other + "/")
                        or (other + "/").startswith(candidate + "/")
                        for other in used_paths
                    )
                )
            )
        )
        used_paths.append(path)
        return path

    def session(backend: str, cwd: str) -> object:
        return environment.Session(
            backend=backend,
            handle=draw(handles()),
            cwd=cwd,
            state=draw(states(environment)),
            changed_at=None,
            detail="",
        )

    entries: list[dict] = []
    live: dict[str, object] = {}
    absent: list[str] = []
    failed: dict[str, str] = {}
    inventory: dict[str, list[object]] = {name: [] for name in backend_names}
    names = draw(st.lists(position_names(), unique=True, min_size=0, max_size=4))
    for name in names:
        backend = draw(st.sampled_from(backend_names))
        cwd = fresh_path("/worktrees")
        entries.append(
            {
                "position": name,
                "mail_name": name.replace(" ", ""),
                "backend": backend,
                "cwd": cwd,
            }
        )
        if backend in failed_backends:
            failed[name] = failed_backends[backend]
        elif draw(st.booleans()):
            found = session(backend, cwd)
            inventory[backend].append(found)
            live[name] = found
        else:
            absent.append(name)

    groups: list[dict] = []
    members: dict[str, list[object]] = {}
    labels = draw(st.lists(position_names(), unique=True, min_size=0, max_size=2))
    for label in labels:
        backend = draw(st.sampled_from(backend_names))
        prefix = fresh_path("/pools")
        groups.append({"label": label, "backend": backend, "cwd_prefix": prefix})
        if backend in failed_backends:
            failed[label] = failed_backends[backend]
            continue
        count = draw(st.integers(min_value=0, max_value=3))
        found_members = [
            session(backend, f"{prefix}/{index}-{draw(handles())}")
            for index in range(count)
        ]
        inventory[backend].extend(found_members)
        members[label] = found_members

    inventories: dict = {}
    for name in backend_names:
        if name in failed_backends:
            inventories[name] = failed_backends[name]
        else:
            inventories[name] = inventory[name]
    watch = {"position": draw(position_names()), "sessions": entries, "groups": groups}
    return RosterCase(watch, inventories, live, absent, failed, members)


def loop_counts() -> st.SearchStrategy[int]:
    """How many monitor loops start together on one state file."""
    return st.integers(min_value=2, max_value=5)


def stall_minutes() -> st.SearchStrategy[int]:
    return st.integers(min_value=5, max_value=120)


def remind_minutes() -> st.SearchStrategy[int]:
    return st.integers(min_value=3, max_value=120)


def background_texts() -> st.SearchStrategy[str]:
    """Pane text of a turn that ended while shells still run, as Claude Code words it."""
    return st.integers(min_value=1, max_value=9).map(
        lambda n: f"{n} shells still running"
    )


@dataclass(frozen=True)
class Watched:
    position: str
    handle: str
    cwd: str


@st.composite
def watched(draw: st.DrawFn, root: str = "/worktrees") -> Watched:
    return Watched(draw(position_names()), draw(handles()), draw(worktree_paths(root)))


@st.composite
def distinct_pairs(draw: st.DrawFn) -> tuple[Watched, Watched]:
    first = draw(watched("/worktrees"))
    second = draw(
        watched("/pools").filter(lambda other: other.position != first.position)
    )
    return first, second


@dataclass(frozen=True)
class MailHistory:
    """Records an inbox held before the first poll and records that arrived after it."""

    channel: str
    agent: str
    existing: list[tuple[int, str, str]]  # (id, sender, subject)
    arrived: list[tuple[int, str, str]]


@st.composite
def mail_histories(draw: st.DrawFn) -> MailHistory:
    ids = draw(
        st.lists(
            st.integers(min_value=1, max_value=100_000),
            unique=True,
            min_size=0,
            max_size=10,
        )
    )
    split = draw(st.integers(min_value=0, max_value=len(ids)))
    ordered = sorted(ids)
    records = [(record_id, draw(senders()), draw(subjects())) for record_id in ordered]
    channel = draw(worktree_paths("/channels"))
    return MailHistory(
        channel, draw(position_names()), records[:split], records[split:]
    )


def thresholds() -> st.SearchStrategy[int]:
    """A positive threshold a watch entry sets to turn on a pane read."""
    return st.integers(min_value=1, max_value=100)
