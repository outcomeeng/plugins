"""Generic eval harness for grading LLM-driven skill behavior.

This package plays the same role pytest plays for automated test
evidence — a runner that replays curated cases through a model, grades
structured verdicts, and emits machine-checkable suite results. The
package encodes nothing marketplace-specific; the ``outcomeeng_`` prefix
is namespace only.
"""
