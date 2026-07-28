"""Level 1 scenario tests for outcomeeng.hygiene.xml_spacing."""

from __future__ import annotations

from outcomeeng.hygiene import xml_spacing
from outcomeeng_testing.harnesses.hygiene import markdown_file


# =============================================================================
# Test get_newline()
# =============================================================================


class TestGetNewline:
    """Test newline style extraction."""

    def test_unix_newline(self) -> None:
        result = xml_spacing.get_newline("some text\n")
        assert result == "\n"

    def test_windows_newline(self) -> None:
        result = xml_spacing.get_newline("some text\r\n")
        assert result == "\r\n"

    def test_no_newline_defaults_to_unix(self) -> None:
        result = xml_spacing.get_newline("some text")
        assert result == "\n"


# =============================================================================
# Test needs_blank_line_before_tag()
# =============================================================================


class TestNeedsBlankLineBeforeTag:
    """Test blank line detection for closing tags after lists."""

    def test_empty_output_returns_false(self) -> None:
        result = xml_spacing.needs_blank_line_before_tag([])
        assert result is False

    def test_non_list_item_returns_false(self) -> None:
        result = xml_spacing.needs_blank_line_before_tag(["regular text\n"])
        assert result is False

    def test_bullet_list_item_returns_true(self) -> None:
        result = xml_spacing.needs_blank_line_before_tag(["- list item\n"])
        assert result is True

    def test_asterisk_list_item_returns_true(self) -> None:
        result = xml_spacing.needs_blank_line_before_tag(["* list item\n"])
        assert result is True

    def test_plus_list_item_returns_true(self) -> None:
        result = xml_spacing.needs_blank_line_before_tag(["+ list item\n"])
        assert result is True

    def test_ordered_list_item_returns_true(self) -> None:
        result = xml_spacing.needs_blank_line_before_tag(["1. list item\n"])
        assert result is True

    def test_ordered_list_paren_returns_true(self) -> None:
        result = xml_spacing.needs_blank_line_before_tag(["1) list item\n"])
        assert result is True

    def test_task_checkbox_returns_true(self) -> None:
        result = xml_spacing.needs_blank_line_before_tag(["- [x] task item\n"])
        assert result is True

    def test_blank_line_already_present_returns_false(self) -> None:
        # A blank last line is not a list item, so no additional blank line is needed.
        result = xml_spacing.needs_blank_line_before_tag(["- list item\n", "\n"])
        assert result is False


# =============================================================================
# Test process_fence_marker()
# =============================================================================


class TestProcessFenceMarker:
    """Test code fence state machine."""

    def test_non_fence_line_preserves_state_outside_fence(self) -> None:
        in_fence, fence, _ = xml_spacing.process_fence_marker(
            "regular text\n", in_fence=False, fence=None
        )
        assert in_fence is False
        assert fence is None

    def test_non_fence_line_preserves_state_inside_fence(self) -> None:
        in_fence, fence, _ = xml_spacing.process_fence_marker(
            "code inside fence\n", in_fence=True, fence="```"
        )
        assert in_fence is True
        assert fence == "```"

    def test_opening_backtick_fence(self) -> None:
        in_fence, fence, pattern = xml_spacing.process_fence_marker(
            "```python\n", in_fence=False, fence=None
        )
        assert in_fence is True
        assert fence == "```"
        assert pattern is not None

    def test_opening_tilde_fence(self) -> None:
        in_fence, fence, pattern = xml_spacing.process_fence_marker(
            "~~~\n", in_fence=False, fence=None
        )
        assert in_fence is True
        assert fence == "~~~"
        assert pattern is not None

    def test_closing_matching_fence(self) -> None:
        in_fence, fence, pattern = xml_spacing.process_fence_marker(
            "```\n", in_fence=True, fence="```"
        )
        assert in_fence is False
        assert fence is None
        assert pattern is None

    def test_non_matching_fence_inside_fence(self) -> None:
        # ~~~ inside a ``` fence doesn't close it
        in_fence, fence, pattern = xml_spacing.process_fence_marker(
            "~~~\n", in_fence=True, fence="```"
        )
        assert in_fence is True
        assert fence == "```"
        assert pattern is None

    def test_longer_fence_opens(self) -> None:
        in_fence, fence, pattern = xml_spacing.process_fence_marker(
            "````\n", in_fence=False, fence=None
        )
        assert in_fence is True
        assert fence == "````"

    def test_indented_fence(self) -> None:
        in_fence, fence, pattern = xml_spacing.process_fence_marker(
            "   ```\n", in_fence=False, fence=None
        )
        assert in_fence is True
        assert fence == "```"


# =============================================================================
# Test process_closing_tag()
# =============================================================================


class TestProcessClosingTag:
    """Test closing XML tag processing."""

    def test_non_closing_tag_returns_false(self) -> None:
        should_skip, modified = xml_spacing.process_closing_tag(
            "regular text\n", ["previous\n"]
        )
        assert should_skip is False
        assert modified is None

    def test_opening_tag_returns_false(self) -> None:
        should_skip, modified = xml_spacing.process_closing_tag(
            "<section>\n", ["previous\n"]
        )
        assert should_skip is False
        assert modified is None

    def test_empty_output_returns_false(self) -> None:
        should_skip, modified = xml_spacing.process_closing_tag("</section>\n", [])
        assert should_skip is False
        assert modified is None

    def test_closing_tag_after_text_unindents(self) -> None:
        should_skip, modified = xml_spacing.process_closing_tag(
            "  </section>\n", ["some text\n"]
        )
        assert should_skip is True
        assert modified == "</section>\n"

    def test_closing_tag_after_list_adds_blank_line(self) -> None:
        output_lines: list[str] = ["- list item\n"]
        should_skip, modified = xml_spacing.process_closing_tag(
            "</section>\n", output_lines
        )
        assert should_skip is True
        assert modified == "</section>\n"
        # Blank line should have been added to output_lines
        assert len(output_lines) == 2
        assert output_lines[-1] == "\n"

    def test_closing_tag_preserves_windows_newline(self) -> None:
        should_skip, modified = xml_spacing.process_closing_tag(
            "  </section>\r\n", ["some text\r\n"]
        )
        assert should_skip is True
        assert modified == "</section>\r\n"

    def test_closing_tag_with_hyphen(self) -> None:
        should_skip, modified = xml_spacing.process_closing_tag(
            "</my-section>\n", ["text\n"]
        )
        assert should_skip is True
        assert modified == "</my-section>\n"

    def test_closing_tag_with_numbers(self) -> None:
        should_skip, modified = xml_spacing.process_closing_tag(
            "</section1>\n", ["text\n"]
        )
        assert should_skip is True
        assert modified == "</section1>\n"


# =============================================================================
# Test fix_file() - End-to-End
# =============================================================================


class TestFixFile:
    """End-to-end tests for file fixing."""

    def test_no_changes_needed(self) -> None:
        with markdown_file("# Header\n\nSome text\n") as path:
            changed = xml_spacing.fix_file(path)
            assert changed is False

    def test_adds_blank_line_before_closing_tag_after_list(self) -> None:
        content = "- item 1\n- item 2\n</section>\n"
        expected = "- item 1\n- item 2\n\n</section>\n"

        with markdown_file(content) as path:
            changed = xml_spacing.fix_file(path)
            assert changed is True
            assert path.read_text() == expected

    def test_unindents_closing_tag(self) -> None:
        content = "text\n  </section>\n"
        expected = "text\n</section>\n"

        with markdown_file(content) as path:
            changed = xml_spacing.fix_file(path)
            assert changed is True
            assert path.read_text() == expected

    def test_preserves_content_inside_code_fence(self) -> None:
        content = "```\n- item\n</section>\n```\n"
        # Inside fence, no changes should be made

        with markdown_file(content) as path:
            changed = xml_spacing.fix_file(path)
            assert changed is False
            assert path.read_text() == content

    def test_handles_nested_fences_correctly(self) -> None:
        # ~~~ inside ``` fence shouldn't close the fence
        content = "```\n~~~\n- item\n</tag>\n~~~\n```\n"

        with markdown_file(content) as path:
            changed = xml_spacing.fix_file(path)
            assert changed is False
            assert path.read_text() == content

    def test_handles_multiple_closing_tags(self) -> None:
        content = "- item\n</section>\n- item2\n</section2>\n"
        expected = "- item\n\n</section>\n- item2\n\n</section2>\n"

        with markdown_file(content) as path:
            changed = xml_spacing.fix_file(path)
            assert changed is True
            assert path.read_text() == expected

    def test_normalizes_windows_line_endings_to_unix(self) -> None:
        # read_text() normalizes \r\n to \n, which is appropriate for git hooks
        content = "- item\r\n</section>\r\n"
        # After normalization and fix, we get Unix line endings
        expected = "- item\n\n</section>\n"

        with markdown_file(content) as path:
            changed = xml_spacing.fix_file(path)
            assert changed is True
            assert path.read_text() == expected

    def test_idempotent(self) -> None:
        """Running fix_file twice produces the same output as running once."""
        content = "- item 1\n- item 2\n</section>\ntext\n  </closing>\n"

        with markdown_file(content) as path:
            xml_spacing.fix_file(path)
            after_first = path.read_text()

            xml_spacing.fix_file(path)
            after_second = path.read_text()

            assert after_first == after_second
