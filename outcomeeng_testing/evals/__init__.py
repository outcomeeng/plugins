"""Marketplace-scoped test helpers for ``[eval]``-related slices.

This package complements ``outcomeeng_evals.testing`` (which ships generic
fakes and factories with the runner). Helpers here depend on the
marketplace's spec-tree layout — link integrity walking, slice-specific
fixture builders, etc. — and would not transfer to another project that
adopts ``outcomeeng_evals`` standalone.
"""
