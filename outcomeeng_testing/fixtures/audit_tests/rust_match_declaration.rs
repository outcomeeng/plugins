fn checks_match_bindings() {
    match outcome() {
        Some(value) => assert_value(value),
        Ok((input, expected)) => assert_case(input, expected),
        Harness { root, target, .. } => assert_paths(root, target),
        Ok((
            multiline_input,
            multiline_expected,
        )) => assert_case(multiline_input, multiline_expected),
        Harness {
            root: multiline_root,
            target: multiline_target,
            ..
        } => assert_paths(multiline_root, multiline_target),
        _ => {}
    }
}
