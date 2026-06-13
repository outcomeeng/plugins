# Authoring

PROVIDES template-driven authoring of spec tree artifacts and node-address delegation for multi-child decomposition
SO THAT all spec authors
CAN create correctly structured artifacts while preserving decomposition structure for the decomposition workflow

## Assertions

### Compliance

- ALWAYS: read the appropriate template before drafting — templates are the structural authority ([review])
- ALWAYS: preserve the three-part hypothesis when authoring outcome nodes — outcome specs declare output, outcome, and impact ([review])
- ALWAYS: invoke `/contextualizing` on the parent directory before creating any node — sibling enumeration prevents index collisions ([review])
- ALWAYS: create single nodes or decision records only when the parent, artifact type, and collision-free index are clear from loaded context ([review])
- ALWAYS: flag content misplacement when scenario, mapping, conformance, or property assertions appear in ADRs/PDRs or implementation details appear in specs ([review])
- ALWAYS: when a request creates or restructures multiple sibling nodes, record the user's decomposition intent, constraints, and known issues in the target node's `PLAN.md` or `ISSUES.md`, then invoke `/decomposing` with only the target address (`spx/` for product-root children or a node address for nested children) ([review])
- ALWAYS: reference nodes, ADRs, and PDRs by full path from `spx/` — bare names and bare decision filenames are ambiguous because numeric prefixes are sibling-local ([review])
- NEVER: pass proposed child nodes, proposed indices, or pre-baked dependency order to `/decomposing` — decomposition owns the structure model ([review])
- NEVER: place implementation details in specs — "how" belongs in ADRs or code ([review])
- NEVER: select an assertion's verification type or assertion type, write or edit a test file, or implement a work item — type selection and test authoring route to `/applying` (which invokes `/testing`); authoring writes assertion text and the evidence-tag requirement only ([review])
