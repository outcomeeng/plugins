def generated_cases() -> tuple[str, ...]:
    return ("first", "rest")


def nested_cases() -> tuple[str, tuple[str, str]]:
    return ("head", ("middle", "tail"))


def test_starred_assignment_declarations() -> None:
    first, *rest = generated_cases()
    head, (*middle, tail) = nested_cases()
    assert first
    assert rest
    assert head
    assert middle
    assert tail
