"""Scenario evidence: read-candidate reads a repository candidate through the request boundary.

Given a Git repository holding a candidate that needs more than one piece, a
client requests ``read-candidate`` without ``offset``, then at the ``next``
offset each piece reports until it is ``null``, and then at the candidate's
``length`` and past it. The runner prints each response as one sorted JSON line
that, with the line terminator it writes after it, takes at most 16,000 UTF-8
bytes of output, a request without ``offset`` returns the piece at
0, each requested ``offset`` returns the piece that starts there, the pieces
concatenate to the candidate file, and an ``offset`` at or past the ``length``
is blocked as ``invalid-request``.

The candidate is the captured Change record the harness repeats until it exceeds
the character limit; the generated piece arithmetic is the property evidence in
``test_audit_change_read_candidate.property.l1.py``.

Given a Git repository holding an empty candidate, a client requests
``read-candidate`` at ``offset`` 0 and receives the one empty piece whose
``next`` is ``null``, and at ``offset`` 1 is blocked as ``invalid-request``. The
case is the interaction the spec declares; the candidate's digest comes from
hashing zero bytes.
"""

from __future__ import annotations

import hashlib
import json

from outcomeeng_testing.harnesses.audit_change_read_candidate import (
    CANDIDATE_PATH,
    candidate_requests,
    wired_candidate_text,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Field = runner.RequestField
Result = runner.ResultField
Status = runner.ResultStatus
Reason = runner.BlockReason
ExitCode = runner.ExitCode


def test_a_client_reads_the_repository_candidate_in_pieces_and_is_refused_at_and_past_its_end() -> (
    None
):
    text = wired_candidate_text()
    base = {
        Field.OPERATION: runner.Operation.READ_CANDIDATE,
        Field.PATH: CANDIDATE_PATH,
    }

    with candidate_requests(text) as send:
        calls = [send(base)]
        while isinstance(calls[-1].result[Result.NEXT], int):
            calls.append(send({**base, Field.OFFSET: calls[-1].result[Result.NEXT]}))
        at_end = send({**base, Field.OFFSET: len(text)})
        past_end = send({**base, Field.OFFSET: len(text) + 1})

    assert Field.OFFSET not in calls[0].request
    assert len(calls) > 1
    consumed = 0
    for call in calls:
        content = str(call.result[Result.CONTENT])
        assert call.exit_code == ExitCode.OK
        assert call.line == json.dumps(call.result, sort_keys=True)
        assert call.output == call.line + runner.LINE_TERMINATOR
        assert call.output_bytes <= runner.PIECE_BYTE_LIMIT
        assert call.result[Result.OFFSET] == consumed
        assert call.result[Result.LENGTH] == len(text)
        assert content == text[consumed : consumed + len(content)]
        consumed += len(content)
    assert consumed == len(text)
    assert calls[-1].result[Result.NEXT] is None
    for refused in (at_end, past_end):
        assert refused.exit_code == ExitCode.INVALID_REQUEST
        assert refused.result[Result.STATUS] == Status.BLOCKED
        assert refused.result[Result.REASON] == Reason.INVALID_REQUEST


def test_a_client_reads_an_empty_candidate_at_offset_zero_and_is_refused_at_offset_one() -> (
    None
):
    base = {
        Field.OPERATION: runner.Operation.READ_CANDIDATE,
        Field.PATH: CANDIDATE_PATH,
    }

    with candidate_requests("") as send:
        first = send({**base, Field.OFFSET: 0})
        refused = send({**base, Field.OFFSET: 1})

    assert first.exit_code == ExitCode.OK
    assert first.result[Result.STATUS] == Status.OK
    assert first.result[Result.CONTENT] == ""
    assert first.result[Result.OFFSET] == 0
    assert first.result[Result.LENGTH] == 0
    assert first.result[Result.SHA256] == hashlib.sha256(b"").hexdigest()
    assert first.result[Result.NEXT] is None
    assert refused.exit_code == ExitCode.INVALID_REQUEST
    assert refused.result[Result.STATUS] == Status.BLOCKED
    assert refused.result[Result.REASON] == Reason.INVALID_REQUEST
