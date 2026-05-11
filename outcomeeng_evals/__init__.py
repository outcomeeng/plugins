"""Generic eval harness for grading LLM-driven skill behavior.

This package is the same role pytest plays for ``[test]`` evidence — a
runner that replays curated cases through a model, grades structured
verdicts, and emits machine-checkable suite results. The package encodes
nothing marketplace-specific; the ``outcomeeng_`` prefix is namespace only.

Governance: ``spx/16-evidence-execution-lanes.adr.md`` declares the
``[eval]`` lane; ``spx/13-infrastructure.enabler/25-eval-harness.enabler/
eval-harness.md`` is the spec node.
"""
