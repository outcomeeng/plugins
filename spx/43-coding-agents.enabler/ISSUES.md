# ISSUES — coding agents

Known imperfections in the coding-agents subtree that no single changeset settles. Each entry names the files, the rule they strain, the evidence, and the condition under which the entry closes.

## Compliance scanners ship inside the environment adapters

A shipped environment adapter carries the regex tables and the scanner functions that detect a sibling script constructing its tool's raw command or invoking its help, and each node's compliance test is their only caller. The Prowl adapter, `src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py`, carries `RAW_PROWL_COMMAND_PATTERNS` (line 410) and `raw_prowl_command_violations` (line 788). The herdr and agent-mail adapters that `spx/43-coding-agents.enabler/18-herdr-environment.enabler` and `spx/43-coding-agents.enabler/18-agent-mail.enabler` specify carry the same shape in the changeset that ships them, `work/change-88-slice-1`: `RAW_HERDR_COMMAND_PATTERNS`, `HERDR_HELP_PATTERNS`, `raw_herdr_command_violations`, `herdr_help_violations` in `operate-herdr/scripts/herdr_environment.py`, and `RAW_MAIL_COMMAND_PATTERNS`, `GIT_PROJECT_KEY_PATTERNS`, `raw_mail_command_violations`, `git_project_key_violations` in `operate-agent-mail/scripts/agent_mail.py`. The artifact installed into consumer repositories therefore carries enforcement logic outside the responsibilities its adapter decision names: command grammar, response validation, error-code projection, record mapping, and bounds.

**Evidence.** `spec-tree:implementation-auditor` run `2026-09-18_11-13-57-525-5814472b13d4` over `67e7f9469938d1273ae14232dc6e560fc8e51368..3f2e301b1c4dc235dca84f3d34726263a9c14691` on `work/change-88-slice-1`, findings `single-responsibility` (severity `debt`) on the herdr and agent-mail adapters; the Prowl adapter shows the same shape on `main`.

**Gap.** Where the scanners live is a placement decision the adapter decisions do not make: the product's test infrastructure under `outcomeeng_testing/harnesses/`, or a repository-side checker the gate runs. The patterns declare what a raw command looks like for each tool; the compliance tests read them by import.

**Settlement condition.** The adapter decisions, or the environments decision above them, name one home for raw-command detection outside the shipped adapters; each node's compliance test imports the scanners and patterns from that home; and no shipped adapter under `src/plugins/coding-agents/` defines a scanner over sibling scripts.
