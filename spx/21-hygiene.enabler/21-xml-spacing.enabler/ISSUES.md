# Issues: XML Spacing

## ~~1. Idempotence assertion uses scenario evidence~~ (FIXED)

Fixed: the Property assertion in `xml-spacing.md` links to `tests/test_fix_xml_spacing.property.l1.py`.

The property test uses Hypothesis to generate markdown-like content and verifies that running `fix_file` twice produces the same output as running it once.
