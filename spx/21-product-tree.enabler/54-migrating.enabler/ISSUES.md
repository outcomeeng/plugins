# Issues: Migrating

## The link-conversion script is plugin-local debt toward an SPX CLI command

**Evidence:** The conversion ships as one standalone script of about 400 lines. [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) lets a generic shipped script beyond fifty lines stand only as debt: its logic moves into the agent-neutral SPX CLI once it proves its value, and a script that never proves its value is removed. The conversion is generic. It reads a product root and carries no agent-specific logic.

**Impact:** A consumer repository cannot version the script independently, and a repair reaches it only through a marketplace release.

**Settlement condition:** The script proves its value in use, its logic moves into an SPX CLI command that carries its own tests, and the skill keeps its instruction and no script; or the script never proves its value and is removed.

## The fixture mapping test fails in a worktree whose fixture trees hold compiled test files

**Evidence:** `test_every_fixture_file_maps_to_its_expected_counterpart` in `tests/test_migrating.mapping.l1.py` compares the bytes of every file under the converted input tree with every file under the expected tree. It reads both through `tree_files` in `outcomeeng_testing/harnesses/link_conversion.py` (line 136), which keys every file `rglob("*")` finds, files git ignores included. A pytest run in a worktree compiles the fixture trees' `test-files/test_*.py` into `__pycache__/*.pyc` files under `outcomeeng_testing/fixtures/link_conversion/input` and `outcomeeng_testing/fixtures/link_conversion/expected`, which `.gitignore` line 56 ignores. On 2026-11-16 the worktree `contributor-4` held six such files, among them `outcomeeng_testing/fixtures/link_conversion/expected/spx/40-legacy.enabler/test-files/__pycache__/test_legacy.mapping.l1.cpython-314-pytest-9.0.2.pyc`, and the test failed in that worktree's `just check-full`. In an export of `bd4b1d7fd250a7db569144ad2509309187b35b96` with those six files copied in, the test failed on the bytes of `spx/32-alpha.capability/21-alpha-child.domain/tests/__pycache__/test_child.scenario.l1.cpython-314-pytest-9.0.2.pyc`. The same export without them passed all four tests of the file. A fresh CI checkout holds no compiled fixture file, so CI passes. On 2026-11-22 the same six files, still in `contributor-4`, failed the test again in `just check-full` at `283a822e3247f55ddd4e020477274100fc1ca775`, and the full gate passed once they were moved out. The read-only command `find outcomeeng_testing/fixtures/link_conversion -name '*.pyc'` lists the compiled fixture files a worktree holds; the test reads no compiled fixture file when it lists none.

**Impact:** `just check-full` fails this one test in every worktree where pytest has run, so the local full gate never passes clean.

**Settlement condition:** The test passes in a worktree whose fixture trees hold ignored `__pycache__` files.

## `l1` tests cross an `l2` boundary

**Evidence:** A run of every `l1` test file of the Product Tree at commit `744cf8cf23`, traced through the Python audit events of each test's setup, call and teardown, records that these `l1` files cross a boundary [`l1-boundaries`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) places at `l2`:

- `tests/test_migrating.compliance.l1.py`: write a file, start a process, make a temporary directory
- `tests/test_migrating.mapping.l1.py`: write a file, start a process, make a temporary directory
- `tests/test_migrating.property.l1.py`: write a file, start a process, make a temporary directory
- `tests/test_migrating.scenario.l1.py`: write a file, start a process, make a temporary directory

**Impact:** Each run of these files starts processes or writes into temporary trees on the host every Position shares, so local and CI gates spend that load on every run.

**Settlement condition:** Each listed file covers the same linked Assertions in process, with no lower line or branch coverage of this Node's code, or the evidence that needs the boundary stands in an `l2` file written for it.
