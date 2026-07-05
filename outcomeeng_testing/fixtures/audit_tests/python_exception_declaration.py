def checks_exception_binding() -> None:
    try:
        raise ValueError("case")
    except ValueError as error:
        assert str(error)
