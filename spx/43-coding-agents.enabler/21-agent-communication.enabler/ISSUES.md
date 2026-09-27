# Issues: Agent Communication

## An unsubmitted doorbell carries no reason

`_doorbell_submitted` in `src/plugins/coding-agents/skills/message-agents/scripts/agent_message.py` (line 1200) validates the doorbell transport through `_checked_success_transport`, catches the `MessageError` that check raises, and returns a bare `False`. The mail delivery result therefore reports `doorbell.submitted: false` with nothing beside it. The check rejects a transport for distinct reasons: an incomplete field set, a wrong schema version, an operation other than send, a status other than succeeded, a nonzero or mismatched exit code, a response, data, or input member that is not an object, or `trailing_enter_sent` other than `true`. The `MessageError` names which one, and the catch discards it. The skill standard's script rule requires verbose, specific error messages.

**Impact**: this node reports an unsubmitted doorbell beside a delivered message, never as a failed delivery. A sender that reads `submitted: false` cannot tell a transport that lacks trailing-Enter evidence, where the pointer is still editable in the recipient's pane, from a malformed or failed transport result without inspecting the transport by hand. Those two conditions call for different next steps.

**Settlement condition**: a mail delivery result whose doorbell is unsubmitted carries, beside the submitted flag, the specific transport field or condition that failed. The message-agents skill surface passes the typed skill auditor with no finding under `script-standards-validation-rule` at this site.

**Evidence**: `instructions:skill-auditor` on `src/plugins/coding-agents/skills/message-agents/` at head `a4fbdf287527ba6af2d3cd570e32021de1619daa`, finding `f-011`, severity `WARNING`, rule `script-standards-validation-rule`, at line 1200 of that file. That audit's overall verdict was `REJECTED` because of a separate must-fix finding. The function is unchanged between that head and `c216a8dd158dac991494bc437f0217b44e746b23`, where it still starts at line 1200 and the catch sits at line 1209.
