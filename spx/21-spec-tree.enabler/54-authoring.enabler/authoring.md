# Authoring

PROVIDES template-driven authoring of spec tree artifacts and node-address delegation for multi-child decomposition
SO THAT all spec authors
CAN create correctly structured artifacts while preserving decomposition structure for the decomposition workflow

## Assertions

### Compliance

- ALWAYS: read the appropriate template before drafting — templates are the structural authority ([review])
- ALWAYS: invoke `/contextualizing` on the parent directory before creating any node — sibling enumeration prevents index collisions ([review])
- ALWAYS: when a request creates or restructures multiple sibling nodes, record the user's decomposition intent, constraints, and known issues in the target node's `PLAN.md` or `ISSUES.md`, then invoke `/decomposing` with only the target address (`spx/` for product-root children or a node address for nested children) ([review])
- NEVER: pass proposed child nodes, proposed indices, or pre-baked dependency order to `/decomposing` — decomposition owns the structure model ([review])
- NEVER: place implementation details in specs — "how" belongs in ADRs or code ([review])
