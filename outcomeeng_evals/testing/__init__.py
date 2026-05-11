"""Test helpers shipped with the eval runner.

External consumers of ``outcomeeng_evals`` import these helpers to write
their own meta-tests without re-implementing the runner's contract surface.
The pattern follows pytest's own ``pytest.MonkeyPatch`` / ``pytest.tmp_path``
convention: a runner ships its own test infrastructure rather than
forcing consumers to roll their own.
"""
