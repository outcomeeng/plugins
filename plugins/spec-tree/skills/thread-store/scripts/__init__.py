"""Thread-store scripts: facade, abstract backend, filesystem backend, CRUD CLIs.

This package mediates persistence of branch-scoped records produced by
spec-tree skills (review results, audit verdicts, and similar). See
``spx/21-spec-tree.enabler/32-evidence.enabler/21-verification.enabler/21-thread-store.enabler/21-backend-abstraction.adr.md``
for the architectural contract.

The scripts run against ``python3`` stdlib only — no third-party imports,
no ``uv`` at runtime, no ``outcomeeng_*`` modules.
"""
