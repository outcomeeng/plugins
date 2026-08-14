# ISSUES — target emission

## The compliance evidence decides its verdicts inside the harness

`tests/test_target_emission.compliance.l1.py` states most of its assertions as `assert <harness_call>()`, where the harness function in `outcomeeng_testing/harnesses/target_emission.py` owns the comparison end to end. Several go further than returning a bare bool: they accumulate failures internally and `raise AssertionError` themselves, then finish with `return True`, so the linked test cannot fail on its own predicate and a reader cannot see which condition broke.

| Harness predicate                                                                                | Backs                        |
| ------------------------------------------------------------------------------------------------ | ---------------------------- |
| `claude_output_preserves_skill_dir_token`                                                        | `target-emission.md` line 15 |
| `codex_output_rewrites_skill_dir_token`                                                          | lines 16 and 21              |
| `skill_dir_escape_preserves_authoring_guidance`                                                  | line 17                      |
| `codex_skill_frontmatter_strips_claude_fields`                                                   | line 18                      |
| `target_scoped_includes_emit_only_to_matching_tree`, `repeated_include_emits_shared_source_once` | line 19                      |
| `outputs_exclude_execution_time_injection`                                                       | line 20                      |

**Resolution shape**: convert each harness predicate to an observation function returning the values its comparison consumes, and move the comparison into the linked test, one assertion at a time. The shape to copy is `observe_build_comment_outputs` in `outcomeeng_testing/harnesses/source_and_templating.py`, which returns each target's rendered body and the comment it carried rather than a verdict. Re-run the test-evidence audit per assertion rather than per file, because the conversions are independent.

`spx/18-plugin-build.enabler/21-source-and-templating.enabler/ISSUES.md` records the same defect class against that node's compliance evidence; the two resolve the same way.
