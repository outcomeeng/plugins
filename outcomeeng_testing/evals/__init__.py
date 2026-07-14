"""Test infrastructure for the eval harness node.

This package is the test-infrastructure home for every ``[eval]``-related
slice, kept outside the shipped ``outcomeeng_evals`` runtime package and
outside any ``tests/`` directory per the test-infrastructure placement
decision. It holds the generic runner test helpers — factories, fakes, and
the CLI harness that exercise the ``outcomeeng_evals`` contract surface —
alongside marketplace-scoped helpers (link-integrity walking, Just-recipe
assertions, producer-prompt materialization) that depend on the
marketplace's spec-tree layout.
"""
