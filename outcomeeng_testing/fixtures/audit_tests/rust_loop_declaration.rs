fn checks_loop_bindings() {
    for case in cases() {
        assert_case(case);
    }

    for (input, expected) in table() {
        assert_eq!(actual(input), expected);
    }

    for Harness { root, target, .. } in harnesses() {
        assert_paths(root, target);
    }
}
