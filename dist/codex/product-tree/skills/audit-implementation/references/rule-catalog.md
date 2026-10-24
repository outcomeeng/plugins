<objective>

The rule catalog of the implementation audit: every rule identifier a finding this audit raises itself may carry, its severity, and the clause it states. A finding's `rule` field holds one identifier from this catalog or from the catalog of the composed concern skill that returned it, and no finding names an identifier outside those catalogs.

</objective>

<contents>
- `key_form`
- `native_rules`
- `composed_rules`

</contents>

<key_form>

The unit of a finding is the scope unit it references, whose `unitId` is the stable scope key `implementation:<kind>:<concern>:<subject-path>`. The finding key is `<stable-scope-key>:<rule-id>`, for example `implementation:typescript:code:src/parse.ts:governing-decision-violated`. A rule identifier is colon-free, so the last `:` separates the subject path from the rule. A finding's `location` names the path and line, or the subject location, where the rule is violated.

Severity in the table below labels the defect on touched text and takes the payload values `blocking` or `debt`. A finding whose location lies outside touched text is returned as `filed` with its recorded severity.

</key_form>

<native_rules>

| Identifier                    | Severity | Rule                                                                                                                              | Stated in                                       |
| ----------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `governing-decision-violated` | blocking | The implementation complies with every rule of the governing decisions discovered for its resolved paths.                         | `audit_workflow` `<execution_sequence>` stage 3 |
| `governing-spec-unmet`        | blocking | The implementation fulfills every assertion of the governing spec nodes discovered for its resolved paths.                        | `audit_workflow` `<execution_sequence>` stage 3 |
| `concern-result-invalid`      | blocking | A concern skill's result names the paths it audited, or returns `NOT_APPLICABLE`, as the invoked skill's verdict contract states. | `audit_workflow` `<coverage_model>`             |

</native_rules>

<composed_rules>

A finding returned by a composed concern skill (`audit-<lang>-code`, `audit-<lang>-test`, `audit-<lang>-architecture`) keeps the rule identifier from that skill's own rule catalog, and its key is `<stable-scope-key>:<that identifier>`. This catalog adds no identifier for it.

</composed_rules>
