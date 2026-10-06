---
id: 01a1125c-7a9c-7292-b240-ba0f1dc80210
malleability: spec
---

# Migrating

PROVIDES conversion of every citation in a spec tree to the tree-absolute link form the 4.0 methodology declares
SO THAT repositories whose trees carry the 3.x citation forms
CAN adopt the 4.0 methodology without hand-editing each citation

## Assertions

- ALWAYS: one node-directory pattern serves every check the conversion makes, and it admits every node kind of the 3.x and 4.0 grammars and every fractional index.
- ALWAYS: the conversion ships as one standalone Python file that uses only the standard library and runs on the floor of the supported Python window, per `spx/12-shipped-scripting.adr.md`.

### Scenarios

- Given two product roots that hold the same tree, when the conversion runs over each with that root as its parameter, then both trees convert to the same tree and the same report ([test](tests/test_migrating.scenario.l1.py))
- Given a root that holds no `spx/` directory, when the conversion runs, then it fails and changes no file ([test](tests/test_migrating.scenario.l1.py))

### Mappings

- A code span that holds the path of a decision record maps to a Markdown inline link whose text and href are the full path from `spx/` ([test](tests/test_migrating.mapping.l1.py))
- A link to a decision record, including a link to a decision of the citing node, maps to a link whose href is the full path from `spx/`, and whose text is that path when its text is the path it replaces ([test](tests/test_migrating.mapping.l1.py))
- A link whose href leads with a slash, climbs with `../`, or reaches into a descendant node maps to a link whose href is the full path from `spx/` ([test](tests/test_migrating.mapping.l1.py))
- A conversion maps each link's fragment and title, and its file's line count, to themselves ([test](tests/test_migrating.mapping.l1.py))
- A reference-style definition maps under the rules of an inline link ([test](tests/test_migrating.mapping.l1.py))
- The conversion lists each file it changes and no other ([test](tests/test_migrating.mapping.l1.py))
- A citation the conversion cannot convert maps to a report line with its file, line, form, and target, and the run continues; a bare path in prose maps to `text-decision`, a target that does not exist maps to `broken`, and neither is rewritten ([test](tests/test_migrating.mapping.l1.py))
- A file that carries only converted citation forms maps to itself, and the report lists the same citations ([test](tests/test_migrating.mapping.l1.py))

### Properties

- Converting a converted tree changes no file and reports the same citations ([test](tests/test_migrating.property.l1.py))

### Compliance

- NEVER: the conversion changes a fenced code block, a link that already carries its full path from `spx/`, a link to a non-decision file inside the citing node, an external or in-page link, or a path with a template placeholder — a brace pair or a bare `NN-` index ([test](tests/test_migrating.compliance.l1.py))
- NEVER: the conversion changes a file other than a Markdown file beneath the root's `spx/` ([test](tests/test_migrating.compliance.l1.py))
