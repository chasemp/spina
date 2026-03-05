"""Tests for domain models - frozen Pydantic models for immutability."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from spina.models import BookMetadata, Chapter, DownloadLink, IntermediateBook, TocEntry
from tests.conftest import (
    make_chapter,
    make_intermediate_book,
    make_metadata,
    make_toc_entry,
)


class TestTocEntry:
    def test_creates_with_required_fields(self) -> None:
        entry = make_toc_entry(title="Introduction", level=1, page=5)
        assert entry.title == "Introduction"
        assert entry.level == 1
        assert entry.page == 5

    def test_is_frozen(self) -> None:
        entry = make_toc_entry()
        with pytest.raises(ValidationError):
            entry.title = "New Title"  # type: ignore[misc]

    def test_rejects_negative_level(self) -> None:
        with pytest.raises(ValidationError):
            make_toc_entry(level=-1)

    def test_rejects_negative_page(self) -> None:
        with pytest.raises(ValidationError):
            make_toc_entry(page=-1)


class TestBookMetadata:
    def test_creates_with_required_fields(self) -> None:
        meta = make_metadata(title="My Book", author="Author", page_count=100)
        assert meta.title == "My Book"
        assert meta.author == "Author"
        assert meta.page_count == 100
        assert meta.toc == ()

    def test_is_frozen(self) -> None:
        meta = make_metadata()
        with pytest.raises(ValidationError):
            meta.title = "New Title"  # type: ignore[misc]

    def test_includes_toc_entries(self) -> None:
        entries = (
            make_toc_entry(title="Ch 1", page=1),
            make_toc_entry(title="Ch 2", page=10),
        )
        meta = make_metadata(toc=entries)
        assert len(meta.toc) == 2
        assert meta.toc[0].title == "Ch 1"

    def test_rejects_empty_title(self) -> None:
        with pytest.raises(ValidationError):
            make_metadata(title="")

    def test_rejects_zero_page_count(self) -> None:
        with pytest.raises(ValidationError):
            make_metadata(page_count=0)


class TestChapter:
    def test_creates_with_required_fields(self) -> None:
        chapter = make_chapter(title="Intro", content="Hello world.", order=0)
        assert chapter.title == "Intro"
        assert chapter.content == "Hello world."
        assert chapter.order == 0
        assert chapter.images == ()

    def test_is_frozen(self) -> None:
        chapter = make_chapter()
        with pytest.raises(ValidationError):
            chapter.title = "New"  # type: ignore[misc]

    def test_tracks_image_references(self) -> None:
        chapter = make_chapter(images=("img1.png", "img2.jpg"))
        assert len(chapter.images) == 2
        assert "img1.png" in chapter.images


class TestDownloadLink:
    def test_creates_with_label_and_filename(self) -> None:
        link = DownloadLink(label="EPUB", filename="my_book.epub")
        assert link.label == "EPUB"
        assert link.filename == "my_book.epub"

    def test_is_frozen(self) -> None:
        link = DownloadLink(label="EPUB", filename="my_book.epub")
        with pytest.raises(ValidationError):
            link.label = "PDF"  # type: ignore[misc]


class TestIntermediateBook:
    def test_creates_with_metadata_and_chapters(self) -> None:
        book = make_intermediate_book()
        assert book.metadata.title == "Test Book"
        assert len(book.chapters) == 1

    def test_is_frozen(self) -> None:
        book = make_intermediate_book()
        with pytest.raises(ValidationError):
            book.metadata = make_metadata(title="Other")  # type: ignore[misc]

    def test_optional_image_dir(self) -> None:
        book = make_intermediate_book(image_dir=Path("/tmp/images"))
        assert book.image_dir == Path("/tmp/images")

    def test_image_dir_defaults_to_none(self) -> None:
        book = make_intermediate_book()
        assert book.image_dir is None

    def test_requires_at_least_one_chapter(self) -> None:
        with pytest.raises(ValidationError):
            IntermediateBook(
                metadata=make_metadata(),
                chapters=(),
            )
