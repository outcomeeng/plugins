# Issues: Python tests

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The Python test-writing path does not load the product's test overlay

`docs/cross-language-test-standards-drift-audit.md` records one Python-specific follow-up: the Python test-writing path, `python-test-standards` and `test-python`, does not load the repo-local `spx/local/python-tests.md` overlay, while the TypeScript and Rust test-standard surfaces teach their overlay paths. Only `audit-python-tests` and the architecture skills name it, so a product-local rule in the overlay can judge Python tests without guiding the author who writes them.

**Settlement condition.** A decision places overlay loading in `python-test-standards`, `test-python` or both, the Python test overlay read path lets product-local rules in `spx/local/python-tests.md` shape the writing guidance, `audit-python-tests` overlay handling stays intact, and the changeset passes `just check-skills`, `just docs-check` and `python:audit-python-tests`.
