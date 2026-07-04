fn ignores_raw_string_declaration_text() {
    insta::assert_snapshot!(r#"
let expected = "not a declaration";
fn helper() {}
"#);

    let actual = build_actual();
}
