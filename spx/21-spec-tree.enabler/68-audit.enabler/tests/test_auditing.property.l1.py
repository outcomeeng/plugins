"""Property tests for audit_orchestrator helper functions.

Covers the spec assertion: 'The scope hash is deterministic: the same sorted
file list always produces the same scope hash.'

Includes a regression-style example test that exercises the length-prefixed
framing decided in PR #9 round-2 review — the framing must distinguish the
known-collision pair `[(a.ts, b), (b, c)]` from `[(a.ts, bb), (c, "")]`.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from outcomeeng_testing.harnesses.audit_orchestrator import (
    load_audit_orchestrator_module,
)

# Filename strategy bounded to harmless characters and modest length so the
# Hypothesis generator stays cheap while still exercising path/content framing.
FILENAME_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789_-./"

_file_strategy = st.tuples(
    st.text(alphabet=FILENAME_ALPHABET, min_size=1, max_size=40),
    st.text(min_size=0, max_size=200),
)


@given(st.lists(_file_strategy, min_size=1, max_size=20))
def test_scope_hash_is_deterministic_for_same_input(
    files: list[tuple[str, str]],
) -> None:
    """For the same sorted file list, compute_scope_hash returns the same hash
    on every call (within and across pytest invocations)."""
    module = load_audit_orchestrator_module()
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
    module = load_audit_orchestrator_module()
    pair_a = [("a.ts", ""), ("a.tsb", "x")]
    pair_b = [("a.ts", "a.ts"), ("b", "x")]
    hash_a = module.compute_scope_hash(pair_a)
    hash_b = module.compute_scope_hash(pair_b)
    assert hash_a != hash_b, (
        f"Framing collision: both file lists hashed to {hash_a!r}; "
        "length-prefixed framing must distinguish them"
    )
