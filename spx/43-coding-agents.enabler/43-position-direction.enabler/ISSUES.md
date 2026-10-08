# ISSUES — position direction

Known imperfections in the position-direction node that its changeset does not settle. Each entry names the files, the rule it strains, the evidence, and the condition under which the entry closes.

## The restart workflow names no source for a position's start prompt

`src/plugins/coding-agents/skills/direct-positions/workflows/restart.md` tells the Director to start a position's session "with the position's start prompt" and names no place where that prompt is recorded and no start operation of the backend. A Director session either improvises the prompt and the launch route, which the skill forbids, or asks the operator what the prompt is.

**Evidence.** `instructions:skill-auditor` finding `f-013`, severity `WARNING`, rule `ambiguous_instruction`, on the skill committed for the position-direction changeset.

**Settlement condition.** The Plugins Maintainer or the Methodology Director states where a position's start prompt lives (the position's own state note, the watch entry, or a plugin reference), and `restart.md` names that source and the start operation of `coding-agents:operate-prowl` and `coding-agents:operate-herdr`.

**Why separate.** The draft bundle records no source for the start prompt, and the changeset cannot choose one for the Director position.
