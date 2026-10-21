---
name: report-changes
description: >-
  ALWAYS invoke this skill when listing, reporting, or checking the open
  Changes in the Change store, such as which Changes are waiting, blocked, or
  claimed. NEVER list Changes with ad hoc gh commands without this skill.
argument-hint: "[product=<Product>] [maturity=<Maturity>] [lifecycle=<Lifecycle>] [holder=<login>] [blocked=<yes|no>]"
allowed-tools: Read, Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/report_changes.py":*)
---

<objective>
A table of the open Changes of the declared Change store that pass the request's filters, one row each in Priority order, or a blocked result naming the failed read or the bound and no row.
</objective>

<constraints>

- NEVER write: the report runs reading `gh` commands only and posts no comment and writes no field, assignee, or blocker; this skill holds no file-write tool, and the script writes no file.
- NEVER substitute a shorter list for a failure: a read that fails, returns unreadable output, or fills a bound yields the blocked result and no row.
- ALWAYS take the Change store and the Priority order from `spx/local/coordination.md` and pass them to the script as request values; the script reads no overlay and no repository content.

</constraints>

<available_scripts>

| Script                      | Purpose                                                                                   | Usage                                                                                                                                                                                                        |
| --------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `scripts/report_changes.py` | Reads the store and prints the matching rows, or the blocked result, as one JSON document | `python3 "${CLAUDE_SKILL_DIR}/scripts/report_changes.py" --store <owner/repo> --priority-order <first,...,last> [--product <v>] [--maturity <v>] [--lifecycle <v>] [--holder <login>] [--blocked <yes\|no>]` |

The script needs `gh` authenticated for the store and Python 3.13 or later, and installs nothing. It exits 0 with `{"status": "ok", "rows": [...]}` and 3 with `{"status": "blocked", "read": ..., "detail": ..., "bound": ...}`; an invalid request value is a blocked result naming the value and the accepted forms.

</available_scripts>

<script_test_record>

`scripts/report_changes.py` was tested by replaying a recorded Change store through an injected command runner, so no test touched a live store or the network.

- **Sample input:** a store of open and closed Changes across several pages, with Product, Maturity, Lifecycle, Priority, and Parent values, assignees, blockers, Handoff and Claim comments, field-change events, and linked branches and pull requests with check results; the request named the store and a Priority order, once without filters and once with each filter.
- **Expected output:** exit 0 and `{"status": "ok", "rows": [...]}` holding exactly the open Changes that pass the filters, over every page, in Priority order with no Priority last, then by ascending issue number. Each row's root, blockers, changeset, waiting state, and next action equal the same values read directly from the recorded store, including `unresolved` for a Parent cycle or an absent Change, and `none` and `none recorded` for a Change with no Handoff.
- **Error cases:** each of the store, blocker, comment, field-change event, and check reads made to exit nonzero, return unreadable output, or fail to start gave exit 3, a blocked result naming the read and its detail, and no row. A store that never ends its pages, a Change returning a full set of field values, and a Change returning a full blocker list each gave exit 3 with the bound named and no row.
- **Cleanup:** every `gh` command the script issued was a read; no GraphQL write, no REST method other than GET, no file written, and no entry left in the working directory.

</script_test_record>

<workflow>

1. **Read the request values.** Read `spx/local/coordination.md`. Take the `Repository` value of its Change store as the store, and the `Priority` line's order from first to last as the Priority order, joined by commas. An absent file, store, or Priority order is a blocked result naming what is missing, with nothing run.
2. **Read the filters from `$ARGUMENTS`.** Each token is `key=value` with `key` one of `product`, `maturity`, `lifecycle`, `holder`, or `blocked`; every filter is optional, and an empty `$ARGUMENTS` reports every open Change. A token of any other form is a blocked result naming the accepted keys, with nothing run. `blocked=yes` keeps Changes with an open blocker and `blocked=no` keeps those without one.
3. **Run the script once**, as its own command with each value written literally: `--store`, `--priority-order`, and one flag for each filter given. The script reads every page of the store, so the rows equal the matching open Changes whatever the number of pages.
4. **Render the result.** For `"status": "blocked"`, report `read`, `detail`, and `bound` verbatim and no row. For `"status": "ok"`, render one table row per entry of `rows`, in the order given, with these columns and a null value as `none`:

   | Column      | Source                                                                                    |
   | ----------- | ----------------------------------------------------------------------------------------- |
   | Change      | `number` linked to `url`, with `title`                                                    |
   | Product     | `product`                                                                                 |
   | Maturity    | `maturity`                                                                                |
   | Lifecycle   | `lifecycle`                                                                               |
   | Priority    | `priority`                                                                                |
   | Holder      | `holder`                                                                                  |
   | Parent/Root | `parent` and `root`                                                                       |
   | Blockers    | each of `blockers` as `number (state)`                                                    |
   | Waiting     | `waiting`                                                                                 |
   | Changeset   | `changeset`: the branch or pull request with its head commit, and the pull request checks |
   | Next action | `next_action`                                                                             |

   An empty `rows` is a report that no open Change passes the filters, naming them.

</workflow>

<success_criteria>

- Each row carries the Change's number, URL, title, Product, Maturity, Lifecycle, Priority, holder, and Parent exactly as the store holds them, and the rows stand in the declared Priority order, a Change with no Priority with the last value, then by ascending issue number.
- Root, blockers, changeset, waiting state, and next action appear as the script derived them, with `unresolved`, `none`, and `none recorded` where it reports them.
- A failed read or a filled bound produced the blocked result and no row.
- No comment, field, assignee, blocker, or file was written.

</success_criteria>
