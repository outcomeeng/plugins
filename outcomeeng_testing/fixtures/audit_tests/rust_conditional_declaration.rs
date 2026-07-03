fn checks_conditionals() {
    if let Some(value) = maybe_value() {
        consume(value);
    }

    while let Ok((input, expected)) = next_case() {
        assert_case(input, expected);
    }

    if let Harness {
        branch,
        nested: nested_branch,
        ..
    } = harness() {
        consume(branch);
        consume(nested_branch);
    }

    if let Harness {
        block_branch,
        nested: nested_block_branch,
        ..
    } = {
        harness()
    } {
        consume(block_branch);
        consume(nested_block_branch);
    }

    let (
        project_dir,
        target,
    ) = fixture();

    let Harness {
        root,
        nested: nested_target,
        ..
    } = harness();
}
