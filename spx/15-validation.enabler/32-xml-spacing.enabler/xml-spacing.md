# XML Spacing

PROVIDES automatic fixing of pseudo-XML tag spacing in markdown files before commit
SO THAT all skill authors
CAN avoid formatting breakage caused by list items followed by closing tags

## Assertions

### Scenarios

- Given a markdown file where a closing XML tag follows a list item, when fixed, then a blank line is inserted before the tag ([test](tests/test_fix_xml_spacing.scenario.l1.py))
- Given a closing XML tag that is indented, when fixed, then the indentation is removed ([test](tests/test_fix_xml_spacing.scenario.l1.py))
- Given content inside a code fence, when fixed, then the content is preserved unchanged ([test](tests/test_fix_xml_spacing.scenario.l1.py))
- Given a file with nested code fences, when fixed, then fence boundaries are tracked correctly ([test](tests/test_fix_xml_spacing.scenario.l1.py))
- Given a file with Windows line endings, when fixed, then line endings are normalized to Unix ([test](tests/test_fix_xml_spacing.scenario.l1.py))
- Given a file that needs no changes, when fixed, then the content is returned unchanged ([test](tests/test_fix_xml_spacing.scenario.l1.py))

### Properties

- Fixing is idempotent: running twice produces the same output as running once ([test](tests/test_fix_xml_spacing.property.l1.py))

### Compliance

- NEVER: modify content inside code fences — the hook respects fence boundaries ([review])
