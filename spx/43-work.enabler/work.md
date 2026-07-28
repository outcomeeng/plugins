# Work

PROVIDES skills that author or repair work deliverables alongside code — Excalidraw diagrams and PowerPoint decks
SO THAT developers shipping documents and slide decks together with their codebase
CAN generate diagrams and sanitize OPC-XML structure without leaving the editor

The work plugin contains `/draw-excalidraw` for creating Excalidraw-format diagrams and `/sanitize-powerpoint` for repairing PowerPoint `.pptx` decks at the OPC XML level. The `sanitize-powerpoint` skill ships two stdlib Python helpers under `plugins/work/skills/sanitize-powerpoint/scripts/`: `pptx_audit.py` reports findings across six dimensions read-only, and `pptx_repack.py` performs content-surgical repackaging with verification.

## Assertions

### Scenarios

- Given a synthetic `.pptx` containing an orphaned slide layout, when `pptx_audit.py` runs against it, then the audit reports the orphan under the structure dimension ([test](tests/test_pptx_audit.scenario.l1.py))
- Given a workdir that is a verbatim extraction of the original deck, when `pptx_repack.py` rebuilds the archive, then the rebuilt deck reports zero changed parts ([test](tests/test_pptx_repack.scenario.l1.py))
- Given a workdir whose changed part contains malformed XML, when `pptx_repack.py` runs verification, then the script exits with code 3 ([test](tests/test_pptx_repack.scenario.l1.py))

### Conformance

- The deck rebuilt by `pptx_repack.py` keeps `[Content_Types].xml` as the first ZIP member, per the OPC packaging convention ([test](tests/test_pptx_repack.conformance.l1.py))

### Compliance

- ALWAYS: `/draw-excalidraw` output is valid Excalidraw JSON — diagrams are consumed by the Excalidraw renderer ([audit])
- ALWAYS: `/sanitize-powerpoint` presents audit findings to the user and gets per-fix approval before any edit — no auto-fix path exists ([audit])
- NEVER: `/sanitize-powerpoint` modifies a `.pptx` while PowerPoint holds the deck open — PowerPoint overwrites external edits from memory on its next save ([audit])
- NEVER: `/sanitize-powerpoint` edits only `docProps/app.xml` to remove a finding — PowerPoint regenerates that file from deck content on every save ([audit])
