"""Tests for index page generation - landing page listing all books."""

from spina.site.index_generator import generate_index_page
from tests.conftest import make_metadata


class TestGenerateIndexPage:
    def test_generates_markdown(self) -> None:
        books = [make_metadata(title="Book One"), make_metadata(title="Book Two")]

        result = generate_index_page(books, site_name="My Library")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_includes_site_name_as_heading(self) -> None:
        books = [make_metadata(title="Book One")]

        result = generate_index_page(books, site_name="My Library")

        assert "# My Library" in result

    def test_lists_all_books(self) -> None:
        books = [
            make_metadata(title="Book A"),
            make_metadata(title="Book B"),
            make_metadata(title="Book C"),
        ]

        result = generate_index_page(books, site_name="Test")

        assert "Book A" in result
        assert "Book B" in result
        assert "Book C" in result

    def test_includes_author_info(self) -> None:
        books = [make_metadata(title="Test", author="Jane Doe")]

        result = generate_index_page(books, site_name="Test")

        assert "Jane Doe" in result

    def test_empty_books_shows_message(self) -> None:
        result = generate_index_page([], site_name="Empty Library")

        assert "No books" in result or "empty" in result.lower()
