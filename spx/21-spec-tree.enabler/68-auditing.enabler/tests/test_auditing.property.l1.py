"""Property tests for audit_orchestrator helper functions.

Covers the spec assertion: 'The scope hash is deterministic: the same sorted
file list always produces the same scope hash.'

Includes a regression-style example test that exercises the length-prefixed
framing decided in PR #9 round-2 review — the framing must distinguish the
known-collision pair `[(a.ts, b), (b, c)]` from `[(a.ts, bb), (c, "")]`.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType

from hypothesis import given
from hypothesis import strategies as st

# parents[4] = repo root (this file lives 4 levels deep: spx/21-spec-tree.enabler/
# 68-auditing.enabler/tests/<file>).
# Tree surgery that changes the enabler's depth must update this index.
SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[4]
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "auditing"
    / "scripts"
)
AUDIT_ORCHESTRATOR = SCRIPTS_DIR / "audit_orchestrator.py"

# Filename strategy bounded to harmless characters and modest length so the
# Hypothesis generator stays cheap while still exercising path/content framing.
FILENAME_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789_-./"

_file_strategy = st.tuples(
    st.text(alphabet=FILENAME_ALPHABET, min_size=1, max_size=40),
    st.text(min_size=0, max_size=200),
)


def _load_audit_orchestrator() -> ModuleType:
    """Load src/plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py.

    The module ships inside the spec-tree plugin's scripts/ directory rather
    than the outcomeeng Python package; importlib.util loads it by absolute
    path so the test does not depend on package layout.
    """
    spec = importlib.util.spec_from_file_location(
        "audit_orchestrator", AUDIT_ORCHESTRATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {AUDIT_ORCHESTRATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_orchestrator"] = module
    spec.loader.exec_module(module)
    return module


@given(st.lists(_file_strategy, min_size=1, max_size=20))
def test_scope_hash_is_deterministic_for_same_input(
    files: list[tuple[str, str]],
) -> None:
    """For the same sorted file list, compute_scope_hash returns the same hash
    on every call (within and across pytest invocations)."""
    module = _load_audit_orchestrator()
    sorted_files = sorted(files, key=lambda f: f[0])
    hash_a = module.compute_scope_hash(sorted_files)
    hash_b = module.compute_scope_hash(sorted_files)
    assert hash_a == hash_b, (
        f"Non-deterministic hash: same input produced {hash_a!r} then {hash_b!r}"
    )


def test_scope_hash_distinguishes_framing_collision_pair() -> None:
    """The framing-collision pair caught in PR #9 round-2 review must produce
    different scope hashes.

    Original framing `printf '%s\\0' "$f"; cat "$f"` produced the same byte
    stream for:
      [("a.ts", ""), ("a.tsb", "x")]  and
      [("a.ts", "a.ts"), ("b", "x")]
    because no separator existed between one file's content and the next
    file's path; both serialize to `a.ts\\0a.tsb\\0x`. The length-prefixed
    framing closes the gap by inserting `<byte_count>\\0` between path and
    content, so the differing content lengths (0 vs 4, 1 vs 1) split the
    streams.
    """
    module = _load_audit_orchestrator()
    pair_a = [("a.ts", ""), ("a.tsb", "x")]
    pair_b = [("a.ts", "a.ts"), ("b", "x")]
    hash_a = module.compute_scope_hash(pair_a)
    hash_b = module.compute_scope_hash(pair_b)
    assert hash_a != hash_b, (
        f"Framing collision: both file lists hashed to {hash_a!r}; "
        "length-prefixed framing must distinguish them"
    )
