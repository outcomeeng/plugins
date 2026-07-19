"""Compliance tests for the evidence-link-integrity walker."""

from __future__ import annotations

from outcomeeng.validation.link_integrity import (
    REASON_EVAL_TARGET_NOT_EVAL_TOML,
    REASON_EVAL_TARGET_OUTSIDE_EVALS_DIR,
    REASON_TARGET_MISSING,
    REASON_TARGET_NOT_FILE,
    REASON_TEST_TARGET_NOT_COLLECTABLE,
    REASON_TEST_TARGET_OUTSIDE_TESTS_DIR,
    BrokenEvalLink,
    BrokenTestLink,
    EvalLink,
    TestLink,
)
from outcomeeng_testing.harnesses.link_integrity import (
    LinkIntegrityCase,
    LinkIntegrityObservation,
    run_link_integrity_contract,
)


def test_evidence_link_integrity_contract() -> None:
    def predicate(observation: LinkIntegrityObservation) -> None:
        match observation.case:
            case LinkIntegrityCase.EVAL_RESOLVABLE:
                assert len(observation.eval_links) == 1
                assert isinstance(observation.eval_links[0], EvalLink)
                assert observation.source_path is not None
                assert observation.target_path is not None
                assert (
                    observation.eval_links[0].source.resolve()
                    == observation.source_path.resolve()
                )
                assert (
                    observation.eval_links[0].target.resolve()
                    == observation.target_path.resolve()
                )
            case LinkIntegrityCase.EVAL_NON_LINK:
                assert observation.eval_links == ()
            case LinkIntegrityCase.EVAL_INLINE:
                assert observation.eval_links == ()
            case LinkIntegrityCase.EVAL_FENCED:
                assert observation.eval_links == ()
            case LinkIntegrityCase.EVAL_ALL:
                assert len(observation.eval_links) == 2
            case LinkIntegrityCase.EVAL_VALID:
                assert observation.broken_eval_links == ()
            case LinkIntegrityCase.EVAL_DEEP:
                assert observation.broken_eval_links == ()
            case LinkIntegrityCase.EVAL_MISSING:
                assert len(observation.broken_eval_links) == 1
                assert isinstance(observation.broken_eval_links[0], BrokenEvalLink)
                assert observation.target_path is not None
                assert (
                    observation.broken_eval_links[0].target.resolve()
                    == observation.target_path.resolve()
                )
                assert observation.broken_eval_links[0].reason == REASON_TARGET_MISSING
            case LinkIntegrityCase.EVAL_NOT_FILE:
                assert len(observation.broken_eval_links) == 1
                assert isinstance(observation.broken_eval_links[0], BrokenEvalLink)
                assert observation.target_path is not None
                assert (
                    observation.broken_eval_links[0].target.resolve()
                    == observation.target_path.resolve()
                )
                assert observation.broken_eval_links[0].reason == REASON_TARGET_NOT_FILE
            case LinkIntegrityCase.EVAL_NON_TOML:
                assert len(observation.broken_eval_links) == 1
                assert isinstance(observation.broken_eval_links[0], BrokenEvalLink)
                assert observation.target_path is not None
                assert (
                    observation.broken_eval_links[0].target.resolve()
                    == observation.target_path.resolve()
                )
                assert (
                    observation.broken_eval_links[0].reason
                    == REASON_EVAL_TARGET_NOT_EVAL_TOML
                )
            case LinkIntegrityCase.EVAL_LOOSE:
                assert len(observation.broken_eval_links) == 1
                assert isinstance(observation.broken_eval_links[0], BrokenEvalLink)
                assert observation.target_path is not None
                assert (
                    observation.broken_eval_links[0].target.resolve()
                    == observation.target_path.resolve()
                )
                assert (
                    observation.broken_eval_links[0].reason
                    == REASON_EVAL_TARGET_OUTSIDE_EVALS_DIR
                )
            case LinkIntegrityCase.TEST_RESOLVABLE:
                assert len(observation.test_links) == 1
                assert isinstance(observation.test_links[0], TestLink)
                assert observation.source_path is not None
                assert observation.target_path is not None
                assert (
                    observation.test_links[0].source.resolve()
                    == observation.source_path.resolve()
                )
                assert (
                    observation.test_links[0].target.resolve()
                    == observation.target_path.resolve()
                )
            case LinkIntegrityCase.TEST_INLINE:
                assert observation.test_links == ()
            case LinkIntegrityCase.TEST_FENCED:
                assert observation.test_links == ()
            case LinkIntegrityCase.TEST_VALID:
                assert observation.broken_test_links == ()
            case LinkIntegrityCase.TEST_DEEP:
                assert observation.broken_test_links == ()
            case LinkIntegrityCase.TEST_MISSING:
                assert len(observation.broken_test_links) == 1
                assert isinstance(observation.broken_test_links[0], BrokenTestLink)
                assert observation.target_path is not None
                assert (
                    observation.broken_test_links[0].target.resolve()
                    == observation.target_path.resolve()
                )
                assert observation.broken_test_links[0].reason == REASON_TARGET_MISSING
            case LinkIntegrityCase.TEST_NOT_FILE:
                assert len(observation.broken_test_links) == 1
                assert isinstance(observation.broken_test_links[0], BrokenTestLink)
                assert observation.target_path is not None
                assert (
                    observation.broken_test_links[0].target.resolve()
                    == observation.target_path.resolve()
                )
                assert observation.broken_test_links[0].reason == REASON_TARGET_NOT_FILE
            case LinkIntegrityCase.TEST_NON_DEFAULT_NAME:
                assert len(observation.broken_test_links) == 1
                assert isinstance(observation.broken_test_links[0], BrokenTestLink)
                assert observation.target_path is not None
                assert (
                    observation.broken_test_links[0].target.resolve()
                    == observation.target_path.resolve()
                )
                assert (
                    observation.broken_test_links[0].reason
                    == REASON_TEST_TARGET_NOT_COLLECTABLE
                )
            case LinkIntegrityCase.TEST_NON_PYTHON:
                assert len(observation.broken_test_links) == 1
                assert isinstance(observation.broken_test_links[0], BrokenTestLink)
                assert observation.target_path is not None
                assert (
                    observation.broken_test_links[0].target.resolve()
                    == observation.target_path.resolve()
                )
                assert (
                    observation.broken_test_links[0].reason
                    == REASON_TEST_TARGET_NOT_COLLECTABLE
                )
            case LinkIntegrityCase.TEST_LOOSE:
                assert len(observation.broken_test_links) == 1
                assert isinstance(observation.broken_test_links[0], BrokenTestLink)
                assert observation.target_path is not None
                assert (
                    observation.broken_test_links[0].target.resolve()
                    == observation.target_path.resolve()
                )
                assert (
                    observation.broken_test_links[0].reason
                    == REASON_TEST_TARGET_OUTSIDE_TESTS_DIR
                )

    run_link_integrity_contract(predicate)
