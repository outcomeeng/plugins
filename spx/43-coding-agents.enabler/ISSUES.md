# ISSUES — coding agents

Known imperfections in the coding-agents subtree that no single changeset settles. Each entry names the files, the rule they strain, the evidence, and the condition under which the entry closes.

## Compliance scanners ship inside the environment adapters

A shipped environment adapter carries the regex tables and the scanner functions that detect a sibling script constructing its tool's raw command or invoking its help, and each node's compliance test is their only caller. The Prowl adapter, `src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py`, carries `RAW_PROWL_COMMAND_PATTERNS` (line 410) and `raw_prowl_command_violations` (line 788). The herdr and agent-mail adapters that `spx/43-coding-agents.enabler/18-herdr-environment.enabler` and `spx/43-coding-agents.enabler/18-agent-mail.enabler` specify carry the same shape in the changeset that ships them, `work/change-88-slice-1`: `RAW_HERDR_COMMAND_PATTERNS`, `HERDR_HELP_PATTERNS`, `raw_herdr_command_violations`, `herdr_help_violations` in `operate-herdr/scripts/herdr_environment.py`, and `RAW_MAIL_COMMAND_PATTERNS`, `GIT_PROJECT_KEY_PATTERNS`, `raw_mail_command_violations`, `git_project_key_violations` in `operate-agent-mail/scripts/agent_mail.py`. The artifact installed into consumer repositories therefore carries enforcement logic outside the responsibilities its adapter decision names: command grammar, response validation, error-code projection, record mapping, and bounds.

**Evidence.** `spec-tree:implementation-auditor` run `2026-09-18_11-13-57-525-5814472b13d4` over `67e7f9469938d1273ae14232dc6e560fc8e51368..3f2e301b1c4dc235dca84f3d34726263a9c14691` on `work/change-88-slice-1`, findings `single-responsibility` (severity `debt`) on the herdr and agent-mail adapters; the Prowl adapter shows the same shape on `main`.

**Gap.** Where the scanners live is a placement decision the adapter decisions do not make: the product's test infrastructure under `outcomeeng_testing/harnesses/`, or a repository-side checker the gate runs. The patterns declare what a raw command looks like for each tool; the compliance tests read them by import.

**Settlement condition.** The adapter decisions, or the environments decision above them, name one home for raw-command detection outside the shipped adapters; each node's compliance test imports the scanners and patterns from that home; and no shipped adapter under `src/plugins/coding-agents/` defines a scanner over sibling scripts.

## The evidence-repair same-class scan stops at the test file

The apply flow's evidence repair scans for the rejected class inside the linked tests — a restated literal, a copied table — and stops there. The mirror shape is invisible to that scan: a value the tests import from production that no production path consumes. `agent_message.py` carried `FORBIDDEN_TARGET_FIELDS`, `FORBIDDEN_EXECUTABLE_FIELDS`, and `CLEAN_STATUS` as constants only the node's tests and harness read, so a test that iterated them was coupled to an inert declaration, and emptying the constant left the test green.

**Evidence.** `spec-tree:test-evidence-auditor` on `spx/43-coding-agents.enabler/21-agent-communication.enabler` at `1b2479a84f70e528315aa7fb16c40448d31817bf` rejected restated literals in the tests; the repair at `4113d674c47ccd118de35b522d4c626a96c17a52` closed those, and the second pass at that head rejected the relocated-constant shape under the same rule, `source-ownership`.

**Gap.** `src/plugins/spec-tree/skills/apply/SKILL.md` `<stabilized_diff_rule>` names the same-class sweep over the touched node's governed files but does not name the consumer check: for every source-owned value a test imports, a production path consumes it.

**Settlement condition.** The apply flow's same-class sweep, or the test-evidence standard it applies, states that a source-owned value a test imports has a production consumer, and a compliance test's violating cases come from the linked test or a real production contract, never from a constant only tests read.
