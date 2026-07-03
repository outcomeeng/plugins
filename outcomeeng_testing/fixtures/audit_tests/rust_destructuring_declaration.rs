fn maps_fixture_bindings() {
    let (project_dir, expected) = fixture();
    let Harness { root, .. } = harness();
    let alias @ Some(value) = maybe_value();
    let Foo { a: nested_alias @ Some(nested_value), .. } = value;
    static ref LOGGER: Logger = init();
}
