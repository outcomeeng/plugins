"""Reviewing-changes scripts package marker — no exports.

The CLI scripts (`compute_diff.py`, `journal_emit.py`) and the policy
module (`review_result.py`) live as bare modules under this directory.
Tests and the wrapper agent load them directly by file path; nothing
imports through this package.
"""
