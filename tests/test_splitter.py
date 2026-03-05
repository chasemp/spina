"""Tests for chapter splitting - pure function that splits markdown into chapters."""

from spina.models import Chapter
from spina.splitter import split_chapters


class TestSplitChapters:
    def test_short_document_returns_single_chapter(self) -> None:
        markdown = "# Title\n\nShort content here."
        chapters = split_chapters(markdown, page_count=5, page_threshold=30)
        assert len(chapters) == 1
        assert chapters[0].title == "Title"
        assert "Short content here." in chapters[0].content

    def test_long_document_splits_on_h1_headings(self) -> None:
        markdown = (
            "# Chapter 1\n\nContent one.\n\n"
            "# Chapter 2\n\nContent two.\n\n"
            "# Chapter 3\n\nContent three."
        )
        chapters = split_chapters(markdown, page_count=50, page_threshold=30)
        assert len(chapters) == 3
        assert chapters[0].title == "Chapter 1"
        assert chapters[1].title == "Chapter 2"
        assert chapters[2].title == "Chapter 3"

    def test_splits_on_h2_if_no_h1_headings(self) -> None:
        markdown = (
            "## Section A\n\nContent A.\n\n"
            "## Section B\n\nContent B."
        )
        chapters = split_chapters(markdown, page_count=50, page_threshold=30)
        assert len(chapters) == 2
        assert chapters[0].title == "Section A"
        assert chapters[1].title == "Section B"

    def test_no_headings_returns_single_chapter(self) -> None:
        markdown = "Just a plain document with no headings at all.\n\nMore text."
        chapters = split_chapters(markdown, page_count=50, page_threshold=30)
        assert len(chapters) == 1
        assert chapters[0].title == "Untitled"

    def test_chapters_have_sequential_order(self) -> None:
        markdown = "# A\n\nText.\n\n# B\n\nText.\n\n# C\n\nText."
        chapters = split_chapters(markdown, page_count=50, page_threshold=30)
        orders = [ch.order for ch in chapters]
        assert orders == [0, 1, 2]

    def test_chapter_content_excludes_heading_line(self) -> None:
        markdown = "# My Chapter\n\nThe actual content."
        chapters = split_chapters(markdown, page_count=5, page_threshold=30)
        assert "# My Chapter" not in chapters[0].content
        assert "The actual content." in chapters[0].content

    def test_extracts_image_references(self) -> None:
        markdown = (
            "# Chapter 1\n\n"
            "![figure](images/fig1.png)\n\n"
            "More text with ![another](images/fig2.jpg)\n"
        )
        chapters = split_chapters(markdown, page_count=5, page_threshold=30)
        assert "images/fig1.png" in chapters[0].images
        assert "images/fig2.jpg" in chapters[0].images

    def test_content_before_first_heading_becomes_first_chapter(self) -> None:
        markdown = (
            "Preamble text.\n\n"
            "# Chapter 1\n\nContent."
        )
        chapters = split_chapters(markdown, page_count=50, page_threshold=30)
        assert len(chapters) == 2
        assert chapters[0].title == "Preamble"
        assert "Preamble text." in chapters[0].content

    def test_returns_tuple_of_chapters(self) -> None:
        markdown = "# Title\n\nContent."
        chapters = split_chapters(markdown, page_count=5, page_threshold=30)
        assert isinstance(chapters, tuple)
        assert all(isinstance(ch, Chapter) for ch in chapters)


class TestSubSplitLargeChapters:
    """When an H1 chapter is large and contains H2 sub-headings, it should be sub-split."""

    def _make_large_chapter_markdown(self) -> str:
        """Build markdown with H1 sections where one contains many H2 sub-sections."""
        small_h1 = "# Introduction\n\nShort intro content.\n\n"
        # Build a large H1 section with H2 sub-sections
        large_sections = []
        for i in range(5):
            large_sections.append(
                f"## Sub Section {i}\n\n{'Content paragraph. ' * 50}"
            )
        large_h1 = "# Main Part\n\n" + "\n\n".join(large_sections) + "\n\n"
        small_h1_2 = "# Conclusion\n\nShort conclusion.\n\n"
        return small_h1 + large_h1 + small_h1_2

    def test_large_h1_chapter_with_h2_subheadings_gets_subsplit(self) -> None:
        markdown = self._make_large_chapter_markdown()
        chapters = split_chapters(
            markdown,
            page_count=50,
            page_threshold=30,
            max_chapter_chars=1000,
        )
        # Should have more than 3 chapters (the 3 H1s)
        # Introduction + 5 sub-sections from Main Part + Conclusion = 7
        titles = [ch.title for ch in chapters]
        assert "Introduction" in titles
        assert "Conclusion" in titles
        assert any("Sub Section" in t for t in titles)
        assert len(chapters) > 3

    def test_small_h1_chapters_not_subsplit_even_with_h2(self) -> None:
        markdown = (
            "# Chapter A\n\n## Small Sub\n\nTiny content.\n\n"
            "# Chapter B\n\nJust content."
        )
        chapters = split_chapters(
            markdown,
            page_count=50,
            page_threshold=30,
            max_chapter_chars=5000,
        )
        # Chapter A is small, so it should NOT be sub-split
        assert len(chapters) == 2
        assert chapters[0].title == "Chapter A"
        assert chapters[1].title == "Chapter B"

    def test_subsplit_preserves_sequential_order(self) -> None:
        markdown = self._make_large_chapter_markdown()
        chapters = split_chapters(
            markdown,
            page_count=50,
            page_threshold=30,
            max_chapter_chars=1000,
        )
        orders = [ch.order for ch in chapters]
        assert orders == list(range(len(chapters)))

    def test_subsplit_defaults_when_max_chapter_chars_not_provided(self) -> None:
        """Ensure split_chapters works without max_chapter_chars (backward compat)."""
        markdown = "# A\n\nContent.\n\n# B\n\nContent."
        chapters = split_chapters(
            markdown,
            page_count=50,
            page_threshold=30,
        )
        assert len(chapters) == 2
