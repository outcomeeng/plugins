# Source and Templating

PROVIDES the source-tree convention and template directive surface
SO THAT plugin authors and the build pipeline
CAN locate sources predictably and express shared-content includes uniformly.

## Assertions

### Scenarios

- Given an `{!% include %!}` directive whose target fragment file is absent, when the source renders, then `IncludeResolutionError` is raised so an unresolved include fails the build loudly instead of emitting empty or partial output ([test](tests/test_expand_include.scenario.l1.py))
- Given a directive whose block body is neither a recognized `name 'argument'` directive nor a Jinja control statement (for example `{!% include %!}` with the argument omitted), when directives are parsed, then `DirectiveSyntaxError` is raised so a malformed directive fails the build rather than shipping verbatim ([test](tests/test_parse_directives.scenario.l1.py))
- Given a Jinja control block in the custom block delimiter (for example `{!% if target == 'codex' %!}`), when directives are parsed, then it yields no directive — the block passes through to the render pass for Jinja to evaluate ([test](tests/test_parse_directives.scenario.l1.py))

### Compliance

- ALWAYS: `src/` contains `src/plugins/<plugin>/{skills,commands,agents}/` mirroring Claude Code plugin structure and `src/_shared/<scope>/<topic>/` holding canonical shared content — a single source tree houses all authored plugin material ([test](tests/test_source_and_templating.compliance.l1.py))
- ALWAYS: shared content directories under `src/_shared/<scope>/<topic>/` contain a `fragment.md` body file and any reference subtrees that travel with it — fragments are the unit of inclusion ([test](tests/test_source_and_templating.compliance.l1.py))
- ALWAYS: the Jinja2 environment uses custom delimiters `{!% %!}` and `{{! !}}` for template parsing — collision-free with skill content that literally contains standard Jinja2 syntax ([test](tests/test_source_and_templating.compliance.l1.py))
- ALWAYS: `{!% require_skill 'plugin:skill' %!}` expands to identical coding-agent-neutral invocation text in both targets — full sister-skill content stays in its own skill ([test](tests/test_source_and_templating.compliance.l1.py))
- NEVER: standard Jinja2 delimiters `{% %}` or `{{ }}` in source content trigger template parsing — content teaching templating syntax passes through unchanged ([test](tests/test_parse_directives.scenario.l1.py))
- ALWAYS: a per-runtime conditional block carrying no variable token still renders per target — the render pass evaluates a surviving `{!% if %!}` control block rather than shipping it verbatim ([test](tests/test_source_and_templating.compliance.l1.py))
- ALWAYS: the skill-directory rewrite escape directive survives the render pass intact even when the body triggers Jinja — the escape shares Jinja's comment syntax but reaches per-target path rewriting unstripped ([test](tests/test_source_and_templating.compliance.l1.py))

### Properties

- Directive round-trip: `parse_directives(format_directive(d)) == (d,)` for every Directive — parse and format are inverses ([test](tests/test_parse_directives.property.l1.py))
- Include resolution returns the referenced fragment file's body verbatim for any content, including delimiter sequences, significant whitespace, and non-ASCII — `expand_include` reads the file unchanged ([test](tests/test_expand_include.property.l1.py))
- Rendering inlines an included fragment's body verbatim into the surrounding output for any directive-free, variable-delimiter-free body — `render_text` replaces the include directive with the file's content unchanged ([test](tests/test_render_text.property.l1.py))
