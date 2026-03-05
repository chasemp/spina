"""Tests for post-processing markdown to fix OCR artifacts."""

from spina.postprocess import repair_drop_caps


class TestRepairDropCaps:
    def test_fixes_truncated_toc_entry_matching_heading(self) -> None:
        markdown = (
            "## Simple Unison\n\n"
            "Some content.\n\n"
            "| imple Unison | 20 |\n"
            "|---|---|\n"
        )
        result = repair_drop_caps(markdown)
        assert "| Simple Unison | 20 |" in result

    def test_fixes_multiple_truncated_entries(self) -> None:
        markdown = (
            "## The Pendulum\n\n"
            "## Appendix D\n\n"
            "| he Pendulum | 16 |\n"
            "|---|---|\n"
            "| ppendix D | 56 |\n"
            "|---|---|\n"
        )
        result = repair_drop_caps(markdown)
        assert "| The Pendulum | 16 |" in result
        assert "| Appendix D | 56 |" in result

    def test_case_insensitive_heading_match(self) -> None:
        markdown = (
            "## THE LATERAL OCTAVE\n\n"
            "Content.\n\n"
            "| he Lateral Octave | 26 |\n"
            "|---|---|\n"
        )
        result = repair_drop_caps(markdown)
        assert "| The Lateral Octave | 26 |" in result

    def test_does_not_modify_correct_entries(self) -> None:
        markdown = (
            "## Introduction\n\n"
            "| Introduction | 1 |\n"
            "|---|---|\n"
        )
        result = repair_drop_caps(markdown)
        assert "| Introduction | 1 |" in result

    def test_returns_unchanged_when_no_headings(self) -> None:
        markdown = "Just some text.\n\n| imple | 20 |\n|---|---|\n"
        result = repair_drop_caps(markdown)
        assert result == markdown

    def test_handles_heading_with_extra_formatting(self) -> None:
        markdown = (
            "## Chladni Patterns\n\n"
            "Content.\n\n"
            "| hladni Patterns | 46 |\n"
            "|---|---|\n"
        )
        result = repair_drop_caps(markdown)
        assert "| Chladni Patterns | 46 |" in result

    def test_does_not_modify_non_table_text(self) -> None:
        markdown = (
            "## The Fourth\n\n"
            "he Fourth is a common interval.\n\n"
        )
        result = repair_drop_caps(markdown)
        # Should not modify text outside of tables
        assert "he Fourth is a common interval." in result
