---
id: 01a1b95b-0000-7000-8000-000000000001
malleability: spec
---

# Catalog

PROVIDES a catalog of items
SO THAT readers
CAN find an item

## Assertions

### Test.Mapping: item-kinds

Items map to kinds. ([test](tests/test_catalog.mapping.l1.py))

| Case | Kind    |
| ---- | ------- |
| book | printed |
| song | audio   |

### Test.Compliance: listing

- sorted: ALWAYS: the listing is sorted ([test](tests/test_catalog.mapping.l1.py))
- paged: NEVER: the listing returns more than a page ([test](tests/test_catalog.mapping.l1.py))
