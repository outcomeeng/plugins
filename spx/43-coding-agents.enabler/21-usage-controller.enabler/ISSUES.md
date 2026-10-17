# ISSUES — usage controller

Known imperfections in the usage-controller node that no single changeset settles. Each entry names the file, the cited reference, the rule it strains, the evidence, the reason it is accepted, and the condition under which the entry closes.

## usage-controller.md:25 — prowl-adapter-access-path

Status: `accepted`. Resolved by outcomeeng/changes#476.

Line 25 of [`spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md`](spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md) states that the control-positions skill acts on panes only through the operation surface of [`spx/43-coding-agents.enabler/18-prowl-environment.enabler/prowl-environment.md`](spx/43-coding-agents.enabler/18-prowl-environment.enabler/prowl-environment.md) by a `__file__`-relative import. [`spx/43-coding-agents.enabler/18-prowl-environment.enabler/15-prowl-adapter.adr.md`](spx/43-coding-agents.enabler/18-prowl-environment.enabler/15-prowl-adapter.adr.md), line 38, states: "ALWAYS: `/operate-prowl` owns all bundled-script access; composing skills invoke the capability through the runtime skill surface rather than manufacturing a cross-skill filesystem path ([audit])". The same tension is filed for the sibling nodes in [`spx/43-coding-agents.enabler/ISSUES.md`](spx/43-coding-agents.enabler/ISSUES.md) under the adapter decisions' bundled-script ownership lines, and the root decision [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md) permits the same-plugin `__file__`-relative import.

**Finding.** DEBT [consistency] at `usage-controller.md:25`, raised in https://github.com/outcomeeng/plugins/pull/665#issuecomment-6232653590. Required: either phrase the access path as invoking `/operate-prowl` as a capability, consistent with the ADR text as committed, or make this assertion depend explicitly on outcomeeng/changes#476 resolving the ADR wording, so the eventual audit gate on the Prowl adapter decision does not reject the implementation on its face.

**Why accepted.** The Plugins Maintainer ruling (https://github.com/outcomeeng/changes/issues/416#issuecomment-6234943244) accepts the finding and keeps the record unchanged. The assertion states the root decision's permitted access path, and outcomeeng/changes#476 restates the adapter decisions' import statements to cite the root rule, which removes the contradiction at its source. The node spec text stays as the Change record states it.

**Settlement condition.** outcomeeng/changes#476 restates the Prowl adapter decision's bundled-script ownership line so that it agrees with the `__file__`-relative import this assertion states.

## usage-controller.md:14,21 — pass-overlap-exclusion

Status: `accepted`.

Lines 14 and 21 of [`spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md`](spx/43-coding-agents.enabler/21-usage-controller.enabler/usage-controller.md) bound a pass at five minutes, schedule the next launchd firing thirty minutes later, and allow one pass on request. Neither assertion declares exclusion between a running pass and the next scheduled or on-request pass. The sibling [`spx/43-coding-agents.enabler/18-consumption-control.enabler/consumption-control.md`](spx/43-coding-agents.enabler/18-consumption-control.enabler/consumption-control.md), line 20, declares the established pattern for a launchd-scheduled worker: "excludes overlapping work", backed by `tests/test_lock.compliance.l1.py`.

**Impact**: two overlapping passes could issue conflicting compact, pause, resume, or stop actions against the same position from stale reads of its share and spend.

**Finding.** DEBT [consistency] at `usage-controller.md:14,21`, raised in https://github.com/outcomeeng/plugins/pull/665#issuecomment-6232653590. Required: add an explicit overlap-exclusion guarantee to the scheduled-pass or launchd-job assertion, matching the sibling consumption-control pattern.

**Why accepted.** The Plugins Maintainer ruling (https://github.com/outcomeeng/changes/issues/416#issuecomment-6234943244) accepts the finding and keeps the record unchanged. The node spec text stays as the Change record states it.

**Settlement condition.** The scheduled-pass or launchd-job assertion of the node declares that a running pass excludes the next scheduled and on-request pass, matching the consumption-control pattern.
