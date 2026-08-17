"""Hypothesis strategies for manage-pr review-thread resolver tests."""

from __future__ import annotations

import string

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng_testing.harnesses.review_thread_resolver import RESOLVER

MAX_GENERATED_TEXT_LENGTH = 32
MAX_GENERATED_NUMBER = 2**31 - 1


def _forbidden_characters(allowed_characters: str) -> str:
    return "".join(
        character
        for character in string.printable + "\x00"
        if character not in allowed_characters
    )


def _discovery_argv(
    values: tuple[int, str, str, str],
) -> tuple[str, ...]:
    selector_mask, repository, pull_request, review_comment_id = values
    selector_values = (repository, pull_request, review_comment_id)
    return tuple(
        token
        for index, (selector, value) in enumerate(
            zip(
                RESOLVER.DISCOVERY_SELECTOR_CONTRACTS,
                selector_values,
                strict=True,
            )
        )
        if selector_mask & (1 << index)
        for token in (selector.option.value, value)
    )


def _mixed_mode_argv(
    values: tuple[str, int, str, str, str],
) -> tuple[str, ...]:
    thread_id, selector_mask, repository, pull_request, review_comment_id = values
    return (
        thread_id,
        *_discovery_argv(
            (selector_mask, repository, pull_request, review_comment_id)
        ),
    )


def malformed_resolver_argvs() -> SearchStrategy[tuple[str, ...]]:
    """Generate malformed argv from independent CLI grammar violations."""

    node_suffix = RESOLVER.NODE_ID_SUFFIX_CONTRACT
    repository_contract = RESOLVER.REPOSITORY_CONTRACT
    number_contract = RESOLVER.NUMBER_CONTRACT
    host_contract = RESOLVER.HOST_CONTRACT
    maximum_node_suffix_length = node_suffix.maximum_length
    if maximum_node_suffix_length is None:
        raise RuntimeError("review-thread node IDs require a finite maximum length")

    safe_name = st.text(
        alphabet=repository_contract.segment.allowed_characters,
        min_size=repository_contract.segment.minimum_length,
        max_size=MAX_GENERATED_TEXT_LENGTH,
    )
    generated_node_suffixes = st.text(
        alphabet=node_suffix.allowed_characters,
        min_size=node_suffix.minimum_length,
        max_size=min(
            maximum_node_suffix_length,
            MAX_GENERATED_TEXT_LENGTH,
        ),
    )
    valid_thread_ids = generated_node_suffixes.map(RESOLVER.format_thread_id)
    valid_repositories = st.tuples(safe_name, safe_name).map(
        lambda segments: repository_contract.separator.join(segments)
    )
    valid_numbers = st.integers(min_value=1, max_value=MAX_GENERATED_NUMBER).map(str)
    valid_comment_node_ids = generated_node_suffixes.map(
        RESOLVER.format_review_comment_node_id
    )
    valid_comment_ids = st.one_of(valid_numbers, valid_comment_node_ids)
    forbidden_text = st.tuples(
        st.text(
            alphabet=node_suffix.allowed_characters,
            max_size=MAX_GENERATED_TEXT_LENGTH,
        ),
        st.sampled_from(_forbidden_characters(node_suffix.allowed_characters)),
        st.text(
            alphabet=node_suffix.allowed_characters,
            max_size=MAX_GENERATED_TEXT_LENGTH,
        ),
    ).map(lambda parts: "".join(parts))
    forbidden_repository_text = st.tuples(
        safe_name,
        st.sampled_from(
            _forbidden_characters(
                repository_contract.segment.allowed_characters
                + repository_contract.separator
            )
        ),
        safe_name,
    ).map(lambda parts: "".join(parts))
    malformed_repositories = st.one_of(
        st.just(""),
        safe_name,
        st.tuples(safe_name, safe_name, safe_name).map(
            lambda segments: repository_contract.separator.join(segments)
        ),
        forbidden_repository_text,
    )
    malformed_numbers = st.one_of(
        st.integers(max_value=0).map(str),
        st.text(
            alphabet=_forbidden_characters(number_contract.remaining_characters),
            min_size=1,
            max_size=MAX_GENERATED_TEXT_LENGTH,
        ),
        st.integers(min_value=0, max_value=MAX_GENERATED_NUMBER).map(
            lambda value: f"0{value}"
        ),
    )
    malformed_host = st.one_of(
        st.just(""),
        st.tuples(
            st.text(
                alphabet=host_contract.allowed_characters,
                max_size=MAX_GENERATED_TEXT_LENGTH,
            ),
            st.sampled_from(_forbidden_characters(host_contract.allowed_characters)),
            st.text(
                alphabet=host_contract.allowed_characters,
                max_size=MAX_GENERATED_TEXT_LENGTH,
            ),
        ).map(lambda parts: "".join(parts)),
    )

    short_node_suffixes = st.text(
        alphabet=node_suffix.allowed_characters,
        max_size=node_suffix.minimum_length - 1,
    )
    overlong_node_suffix = node_suffix.allowed_characters[0] * (
        maximum_node_suffix_length + 1
    )
    malformed_thread_ids = st.one_of(
        st.just(""),
        short_node_suffixes.map(
            lambda suffix: f"{RESOLVER.THREAD_ID_CONTRACT.prefix}{suffix}"
        ),
        st.just(f"{RESOLVER.THREAD_ID_CONTRACT.prefix}{overlong_node_suffix}"),
        generated_node_suffixes.map(RESOLVER.format_review_comment_node_id),
        forbidden_text,
    )
    opaque_comment_ids = st.text(
        alphabet=node_suffix.allowed_characters,
        max_size=MAX_GENERATED_TEXT_LENGTH - 1,
    ).map(lambda suffix: f"A{suffix}")
    invalid_decimal_lead = next(
        character
        for character in number_contract.remaining_characters
        if character not in number_contract.first_characters
    )
    malformed_comment_ids = st.one_of(
        st.just(""),
        st.just(invalid_decimal_lead),
        valid_numbers.map(lambda value: f"{invalid_decimal_lead}{value}"),
        short_node_suffixes.map(
            lambda suffix: f"{RESOLVER.COMMENT_ID_CONTRACT.node_id.prefix}{suffix}"
        ),
        st.just(f"{RESOLVER.COMMENT_ID_CONTRACT.node_id.prefix}{overlong_node_suffix}"),
        generated_node_suffixes.map(RESOLVER.format_thread_id),
        opaque_comment_ids,
        forbidden_text,
    )

    full_discovery_selector_mask = (
        1 << len(RESOLVER.DISCOVERY_SELECTOR_CONTRACTS)
    ) - 1
    incomplete_discovery = st.tuples(
        st.integers(min_value=0, max_value=full_discovery_selector_mask - 1),
        valid_repositories,
        valid_numbers,
        valid_comment_ids,
    ).map(_discovery_argv)
    mixed_modes = st.tuples(
        valid_thread_ids,
        st.integers(min_value=1, max_value=full_discovery_selector_mask),
        valid_repositories,
        valid_numbers,
        valid_comment_ids,
    ).map(_mixed_mode_argv)

    return st.one_of(
        incomplete_discovery,
        malformed_thread_ids.map(lambda value: (value,)),
        st.tuples(
            malformed_repositories,
            valid_numbers,
            valid_comment_ids,
        ).map(
            lambda values: (
                RESOLVER.ResolverOption.REPOSITORY.value,
                values[0],
                RESOLVER.ResolverOption.PULL_REQUEST.value,
                values[1],
                RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
                values[2],
            )
        ),
        st.tuples(
            valid_repositories,
            malformed_numbers,
            valid_comment_ids,
        ).map(
            lambda values: (
                RESOLVER.ResolverOption.REPOSITORY.value,
                values[0],
                RESOLVER.ResolverOption.PULL_REQUEST.value,
                values[1],
                RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
                values[2],
            )
        ),
        st.tuples(
            valid_repositories,
            valid_numbers,
            malformed_comment_ids,
        ).map(
            lambda values: (
                RESOLVER.ResolverOption.REPOSITORY.value,
                values[0],
                RESOLVER.ResolverOption.PULL_REQUEST.value,
                values[1],
                RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
                values[2],
            )
        ),
        st.tuples(malformed_host, valid_thread_ids).map(
            lambda values: (
                RESOLVER.ResolverOption.HOST.value,
                values[0],
                values[1],
            )
        ),
        st.tuples(
            malformed_host,
            valid_repositories,
            valid_numbers,
            valid_comment_ids,
        ).map(
            lambda values: (
                RESOLVER.ResolverOption.HOST.value,
                values[0],
                RESOLVER.ResolverOption.REPOSITORY.value,
                values[1],
                RESOLVER.ResolverOption.PULL_REQUEST.value,
                values[2],
                RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
                values[3],
            )
        ),
        mixed_modes,
    )
