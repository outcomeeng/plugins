# Source and Templating

PROVIDES the source-tree convention and template directive surface
SO THAT plugin authors and the build pipeline
CAN locate sources predictably and express shared-content includes uniformly.

## Assertions

### Compliance

- ALWAYS: `src/` contains `src/plugins/<plugin>/{skills,commands,agents}/` mirroring runtime plugin structure and `src/_shared/<scope>/<topic>/` holding canonical shared content — a single source tree houses all authored plugin material ([test](tests/test_source_and_templating.compliance.l1.py))
- ALWAYS: shared content directories under `src/_shared/<scope>/<topic>/` contain a `fragment.md` body file and any reference subtrees that travel with it — fragments are the unit of inclusion ([test](tests/test_source_and_templating.compliance.l1.py))
- ALWAYS: the Jinja2 environment uses custom delimiters `{!% %!}` and `{{! !}}` for template parsing — collision-free with skill content that literally contains standard Jinja2 syntax ([test](tests/test_source_and_templating.compliance.l1.py))
- ALWAYS: `{!% include 'path/to/file.md' %!}` inlines the named file's body verbatim into the rendered output — short shared fragments expand inline ([test](tests/test_source_and_templating.compliance.l1.py))
- ALWAYS: `{!% require_skill 'plugin:skill' %!}` expands to identical agent-runtime-neutral invocation text in both targets — full sister-skill content stays in its own skill ([test](tests/test_source_and_templating.compliance.l1.py))
- NEVER: standard Jinja2 delimiters `{% %}` or `{{ }}` in source content trigger template parsing — content teaching templating syntax passes through unchanged ([test](tests/test_source_and_templating.compliance.l1.py))
