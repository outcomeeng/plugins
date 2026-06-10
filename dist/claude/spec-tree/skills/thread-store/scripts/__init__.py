"""Thread-store scripts: facade, abstract backend, filesystem backend, CRUD CLIs.

This package mediates persistence of branch-scoped records produced by
spec-tree skills (review results, audit verdicts, and similar) behind an
abstract backend the facade resolves, so callers depend on the storage
contract rather than the storage mechanism.

The scripts run against ``python3`` stdlib only — no third-party imports,
no ``uv`` at runtime, no ``outcomeeng_*`` modules.
"""
