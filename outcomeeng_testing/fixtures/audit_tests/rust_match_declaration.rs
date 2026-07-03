fn checks_match_bindings() {
    match outcome() {
        Some(value) => assert_value(value),
        Ok((input, expected)) => assert_case(input, expected),
        Harness { root, target, .. } => assert_paths(root, target),
        _ => {}
    }
}
