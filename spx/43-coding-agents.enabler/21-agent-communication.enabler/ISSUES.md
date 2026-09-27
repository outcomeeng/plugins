# Issues: Agent Communication

## An unsubmitted doorbell carries no reason

`_doorbell_submitted` in `src/plugins/coding-agents/skills/message-agents/scripts/agent_message.py` (line 1200) validates the doorbell transport through `_checked_success_transport`, catches the `MessageError` that check raises, and returns a bare `False`. The mail delivery result therefore reports `doorbell.submitted: false` with nothing beside it. The check rejects a transport for distinct reasons: an incomplete field set, a wrong schema version, an operation other than send, a status other than succeeded, a nonzero or mismatched exit code, a response, data, or input member that is not an object, or `trailing_enter_sent` other than `true`. The `MessageError` names which one, and the catch discards it. The skill standard's script rule requires verbose, specific error messages.

**Impact**: this node reports an unsubmitted doorbell beside a delivered message, never as a failed delivery. A sender that reads `submitted: false` cannot tell a transport that lacks trailing-Enter evidence, where the pointer is still editable in the recipient's pane, from a malformed or failed transport result without inspecting the transport by hand. Those two conditions call for different next steps.

**Settlement condition**: a mail delivery result whose doorbell is unsubmitted carries, beside the submitted flag, the specific transport field or condition that failed. The message-agents skill surface passes the typed skill auditor with no finding under `script-standards-validation-rule` at this site.

**Evidence**: `instructions:skill-auditor` on `src/plugins/coding-agents/skills/message-agents/` at head `a4fbdf287527ba6af2d3cd570e32021de1619daa`, finding `f-011`, severity `WARNING`, rule `script-standards-validation-rule`, at line 1200 of that file. That audit's overall verdict was `REJECTED` because of a separate must-fix finding. The function is unchanged between that head and `c216a8dd158dac991494bc437f0217b44e746b23`, where it still starts at line 1200 and the catch sits at line 1209.

## A rejected input's validation detail names a field chosen by set order

`src/plugins/coding-agents/skills/message-agents/scripts/agent_message.py` stops at the first failing field while iterating a `set`, and names that field in the `MessageError` detail. Python randomizes string hashing per process, so a `set` of field names has no stable iteration order. When one input fails on more than one field, the field the detail names depends on which run produced it. There are three such sites:

- `_validated_fields` (line 553) builds its result at line 566 with a comprehension over the `fields` frozenset, and `_text` raises for the first field that is not a non-empty string. Both `mutationTarget` (`MUTATION_TARGET_FIELDS`) and `observedState` (`OBSERVED_STATE_FIELDS`) are validated this way.
- `_mutation_contract` (line 578) compares the target with the live message identity at line 628, iterating the set literal `{PANE_FIELD, WORKTREE_FIELD, BRANCH_FIELD, REPOSITORY_FIELD}`, and raises on the first field that does not match.
- `_mutation_contract` compares the observed state with the mutation target at line 635, iterating the frozenset `OBSERVED_STATE_FIELDS`, and raises on the first field that does not match.

The same file's field-set mismatch details do not have this problem, because they sort the unexpected and missing names before joining them.

**Impact**: when the same invalid ownership proposal, mutation-state report, or mutation authorization is sent twice, the two rejections can name different fields. A sender that repairs the named field and resends can then be rejected on a field the first detail never mentioned. Test evidence that checks the named field also passes or fails depending on the process hash seed. The detail names one of several failing fields and does not say that others exist, so it looks complete when it is not.

**Settlement condition**: at all three sites, a rejected input produces the same validation detail in every process, whatever the hash seed. The message-agents skill surface passes the typed skill auditor with no finding at these sites.

**Evidence**: `instructions:skill-auditor` finding `f-014`, severity `WARNING`, against the message-agents skill surface at head `807500ceba67534713bf06d05a36598ebe552819`. The previous round left it open. At that same head, the script has the three iterations at the lines cited above. Loading the script and calling `_validated_fields` on an `observedState` whose five fields all hold a non-string produced these details under `PYTHONHASHSEED` 0 through 5: `observedState.branch`, `observedState.head`, `observedState.branch`, `observedState.repository`, `observedState.status`, `observedState.status`.
