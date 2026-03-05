"""Factory functions for test data. No mutable fixtures."""

from pathlib import Path

from spina.models import BookMetadata, Chapter, IntermediateBook, TocEntry


def make_toc_entry(
    *,
    title: str = "Chapter 1",
    level: int = 1,
    page: int = 1,
) -> TocEntry:
    return TocEntry(title=title, level=level, page=page)


def make_metadata(
    *,
    title: str = "Test Book",
    author: str = "Test Author",
    source_filename: str = "test.pdf",
    page_count: int = 10,
    toc: tuple[TocEntry, ...] = (),
) -> BookMetadata:
    return BookMetadata(
        title=title,
        author=author,
        source_filename=source_filename,
        page_count=page_count,
        toc=toc,
    )


def make_chapter(
    *,
    title: str = "Chapter 1",
    content: str = "Some content.",
    images: tuple[str, ...] = (),
    order: int = 0,
) -> Chapter:
    return Chapter(
        title=title,
        content=content,
        images=images,
        order=order,
    )


def make_intermediate_book(
    *,
    metadata: BookMetadata | None = None,
    chapters: tuple[Chapter, ...] | None = None,
    image_dir: Path | None = None,
) -> IntermediateBook:
    return IntermediateBook(
        metadata=metadata or make_metadata(),
        chapters=chapters or (make_chapter(),),
        image_dir=image_dir,
    )
