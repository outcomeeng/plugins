# Validation

PROVIDES the pre-commit validation pipeline that runs automated checks on plugin and skill artifacts
SO THAT all plugin and skill authors
CAN trust that committed artifacts conform to Claude Code and Agent Skills standards

The pipeline is orchestrated by `lefthook` and runs two categories of checks:

- **Skill frontmatter validation** — [32-skill-frontmatter.enabler/skill-frontmatter.md](32-skill-frontmatter.enabler/skill-frontmatter.md) verifies SKILL.md frontmatter fields against the union of Agent Skills open standard and Claude Code binary-extracted fields.
- **Plugin manifest validation** — [32-plugin-manifest.enabler/plugin-manifest.md](32-plugin-manifest.enabler/plugin-manifest.md) runs `claude plugin validate` against marketplace and plugin manifest files.

XML spacing is handled by a separate sibling enabler — [32-xml-spacing.enabler/xml-spacing.md](32-xml-spacing.enabler/xml-spacing.md) — which applies formatting fixes to markdown files before other formatters run.
