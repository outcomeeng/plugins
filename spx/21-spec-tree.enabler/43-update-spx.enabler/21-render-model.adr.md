# Guide Render Model

The product's spx-level directory guide is generated, not hand-merged: its customization surface is declarative frontmatter data — the product name and the enabled-language list — and its body is rendered from the installed template. An update re-renders the new template with the guide's existing config, so new template content propagates, disabled-language blocks are omitted, and the product name and language selection are preserved while `template_version` is set to the installed version. The parse-config, version-compare, render, and scaffold functions are pure over content strings; filesystem reads and writes live only at the skill script's thin CLI edge. The canonical template has one home — the understanding skill's `templates/` — read by `/understanding` from its own template directory and by `/update-spx` through the understanding skill's `templates/` via the runtime's skill-directory path.

## Rationale

The guide cannot both stay current with the template and preserve arbitrary in-place edits from two inputs alone: "section absent from the product" is ambiguous between new-in-template and user-deleted without the template as it stood at the product's version. Modeling the customization as data removes the ambiguity — there is nothing to merge. The enabled-language selection and the product name are declared in frontmatter, and a re-render reflects the new template plus that declaration: new template sections arrive automatically, and a disabled language is an omission from the `languages` list rather than prose surgery. The accepted cost is that a re-render does not preserve unmodeled hand-prose edits to the guide body; this is acceptable because the guide is generated boilerplate, and the product's durable truth lives in its specs and decisions, not in the directory guide. The renderer uses stdlib-parseable block delimiters rather than a third-party templating engine, because plugin scripts run in consumer environments with no third-party packages, per `spx/13-plugin-and-runtime-conventions.adr.md`. One template home avoids the drift a per-skill copy would invite, and mirrors how `/authoring` reads the spec-artifact templates from `../understanding/templates/`.

## Verification

### Audit

- ALWAYS: the guide's customization surface is declarative frontmatter data — the product name and the enabled-language list — and the body is rendered from the template, never hand-merged ([audit])
- ALWAYS: an update re-renders the new template with the guide's existing config, so new template content propagates and the product name and enabled-language selection are preserved ([audit])
- ALWAYS: the parse-config, version-compare, render, and scaffold functions are pure — content strings in, content strings out — with no filesystem, environment, or subprocess access ([audit])
- ALWAYS: filesystem reads and writes live only in the skill script's thin CLI edge, which delegates to the pure core ([audit])
- ALWAYS: `template_version` comparison parses the dotted-numeric version with the standard library only ([audit])
- ALWAYS: the canonical template has one home — the understanding skill's `templates/` — and consuming skills read it through the understanding-templates path ([audit])
- NEVER: the core parse, render, compare, or scaffold functions read or write files, read environment variables, or spawn subprocesses ([audit])
- NEVER: the renderer depends on a third-party templating engine — language-conditional blocks use stdlib-parseable delimiters ([audit])
- NEVER: an update hand-merges or section-diffs the product's body against the template — re-render is the update mechanism ([audit])
