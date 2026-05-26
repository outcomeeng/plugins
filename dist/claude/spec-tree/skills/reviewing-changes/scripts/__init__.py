"""Reviewing-changes scripts package marker — no exports.

The CLI scripts (`validate_review_result.py`, `compute_diff.py`,
`render_review.py`) and the policy module (`review_result.py`) live as
bare modules under this directory. Tests and the wrapper agent load
them directly by file path; nothing imports through this package.
"""
