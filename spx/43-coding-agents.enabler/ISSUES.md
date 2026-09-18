# ISSUES — coding agents

Known imperfections in the coding-agents subtree that no single changeset settles. Each entry names the files, the rule they strain, the evidence, and the condition under which the entry closes.

## Compliance scanners ship inside the environment adapters

Each shipped adapter carries the regex tables and the two scanner functions that detect a sibling script constructing its tool's raw command or invoking its help: `src/plugins/coding-agents/skills/operate-herdr/scripts/herdr_environment.py` (`RAW_HERDR_COMMAND_PATTERNS`, `HERDR_HELP_PATTERNS`, `raw_herdr_command_violations`, `herdr_help_violations`), `src/plugins/coding-agents/skills/operate-agent-mail/scripts/agent_mail.py` (`RAW_MAIL_COMMAND_PATTERNS`, `GIT_PROJECT_KEY_PATTERNS`, `raw_mail_command_violations`, `git_project_key_violations`), and `src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py` (`RAW_PROWL_COMMAND_PATTERNS` at line 410, `raw_prowl_command_violations` at line 788). Their only callers are each node's compliance test, so the artifact installed into consumer repositories carries enforcement logic outside the responsibilities its adapter decision names: command grammar, response validation, error-code projection, record mapping, and bounds.

**Evidence.** `spec-tree:implementation-auditor` run `2026-09-18_11-13-57-525-5814472b13d4` over `67e7f9469938d1273ae14232dc6e560fc8e51368..3f2e301b1c4dc235dca84f3d34726263a9c14691`, findings `single-responsibility` (severity `debt`) on the herdr and agent-mail adapters; the Prowl adapter carries the same shape and lies outside that changeset.

**Gap.** Where the scanners live is a placement decision the three adapter decisions do not make: the product's test infrastructure under `outcomeeng_testing/harnesses/`, or a repository-side checker the gate runs. The patterns declare what a raw command looks like for each tool; the compliance tests read them by import today.

**Settlement condition.** The three adapter decisions, or the environments decision above them, name one home for raw-command detection outside the shipped adapters; the scanners and patterns move there in one changeset covering all three adapters; each node's compliance test imports them from the new home; and the three nodes pass their test-evidence audits on that changeset. The entry closes when no shipped adapter under `src/plugins/coding-agents/` defines a scanner over sibling scripts.
