fn ignores_raw_string_declaration_text() {
    insta::assert_snapshot!(r#"
let expected = "not a declaration";
fn local_function() {}
"#);

    let actual = build_actual();
}
