"""Level-1 compliance evidence for `spx/21-hygiene.enabler/21-clean.enabler/`.

Covers the two compliance assertions in `clean.md`:
- ALWAYS: invoke `git clean -fdX` — the exact flag combination is the
  contract.
- NEVER: pass any additional argument to `git clean` — extra flags would
  broaden the remove set beyond gitignored paths.
"""

from __future__ import annotations

from outcomeeng.hygiene.clean import CLEAN_ARGV


def test_argv_is_force_directories_gitignored_only() -> None:
    assert CLEAN_ARGV == ("git", "clean", "-fdX")


def test_argv_contains_no_additional_arguments() -> None:
    assert len(CLEAN_ARGV) == 3
    assert CLEAN_ARGV[0] == "git"
    assert CLEAN_ARGV[1] == "clean"
    assert CLEAN_ARGV[2] == "-fdX"
