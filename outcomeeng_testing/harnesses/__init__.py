"""Harnesses for the marketplace's test infrastructure.

Importing any harness turns the interpreter's bytecode writing off for the
process, so no in-process load or import of a shipped script, eager or lazy,
leaves a bytecode cache beside it under ``dist/``.
"""

import sys

sys.dont_write_bytecode = True
