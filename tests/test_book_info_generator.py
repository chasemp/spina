"""Tests for book info page generation."""

from spina.models import DownloadLink
from spina.site.book_info_generator import generate_book_info_page
from tests.conftest import make_metadata


class TestGenerateBookInfoPage:
    def test_includes_title_as_heading(self) -> None:
        metadata = make_metadata(title="Harmonograph")

        result = generate_book_info_page(metadata, chapter_count=5)

        assert result.startswith("# Harmonograph\n")

    def test_includes_author(self) -> None:
        metadata = make_metadata(author="Anthony Ashton")

        result = generate_book_info_page(metadata, chapter_count=3)

        assert "**Author:** Anthony Ashton" in result

    def test_includes_page_count(self) -> None:
        metadata = make_metadata(page_count=32)

        result = generate_book_info_page(metadata, chapter_count=3)

        assert "**Pages:** 32" in result

    def test_includes_chapter_count(self) -> None:
        metadata = make_metadata()

        result = generate_book_info_page(metadata, chapter_count=6)

        assert "**Chapters:** 6" in result

    def test_includes_source_filename(self) -> None:
        metadata = make_metadata(source_filename="harmonograph.pdf")

        result = generate_book_info_page(metadata, chapter_count=3)

        assert "**Source:** harmonograph.pdf" in result

    def test_renders_download_links(self) -> None:
        metadata = make_metadata()
        downloads = (
            DownloadLink(label="EPUB", filename="book.epub"),
            DownloadLink(label="Clean PDF", filename="book_clean.pdf"),
        )

        result = generate_book_info_page(
            metadata, chapter_count=3, downloads=downloads
        )

        assert "## Downloads" in result
        assert "- [EPUB](book.epub)" in result
        assert "- [Clean PDF](book_clean.pdf)" in result

    def test_omits_downloads_section_when_empty(self) -> None:
        metadata = make_metadata()

        result = generate_book_info_page(metadata, chapter_count=3)

        assert "## Downloads" not in result
