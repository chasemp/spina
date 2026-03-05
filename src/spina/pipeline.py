"""Pipeline - orchestrates PDF → intermediate → outputs."""

from pathlib import Path

from spina.config import SpinaConfig
from spina.engines.base import ConversionEngine
from spina.intermediate import _slugify, read_intermediate, write_intermediate
from spina.metadata import extract_pdf_metadata
from spina.models import BookMetadata, Chapter, IntermediateBook
from spina.postprocess import repair_drop_caps
from spina.outputs.epub_builder import build_epub
from spina.outputs.pdf_builder import build_clean_pdf
from spina.outputs.site_builder import build_html, build_site
from spina.splitter import split_chapters


def _collect_all_books(output_dir: Path) -> list[IntermediateBook]:
    """Scan output_dir for all existing intermediate books."""
    book_dirs = [
        d for d in output_dir.iterdir()
        if d.is_dir() and (d / "metadata.yaml").exists()
    ]
    return [read_intermediate(d) for d in sorted(book_dirs)]


def convert_pdf(
    pdf_path: Path,
    *,
    engine: ConversionEngine,
    config: SpinaConfig,
    output_dir: Path | None = None,
) -> IntermediateBook:
    """Convert a single PDF to an IntermediateBook, optionally writing outputs."""
    result = engine.convert(pdf_path)

    # Extract metadata: PDF info dict → engine metadata → filename
    pdf_info = extract_pdf_metadata(pdf_path)
    title = (
        pdf_info.get("title")
        or result.metadata.get("title")
        or pdf_path.stem
    )
    author = (
        pdf_info.get("author")
        or result.metadata.get("author")
        or "Unknown"
    )

    # Post-process OCR output to fix drop-cap artifacts
    markdown = repair_drop_caps(result.markdown)

    chapters = split_chapters(
        markdown,
        page_count=result.page_count,
        page_threshold=config.page_threshold,
    )

    metadata = BookMetadata(
        title=title,
        author=author,
        source_filename=pdf_path.name,
        page_count=result.page_count,
    )

    if output_dir is not None:
        book_dir = output_dir / _slugify(pdf_path.stem)
        image_dir = book_dir / "images" if result.images else None

        book = IntermediateBook(
            metadata=metadata,
            chapters=chapters,
            image_dir=image_dir,
        )
        write_intermediate(book, book_dir, images=result.images)

        if config.generate_epub:
            epub_path = output_dir / f"{_slugify(pdf_path.stem)}.epub"
            build_epub(book, epub_path)

        if config.generate_clean_pdf:
            clean_pdf_path = output_dir / f"{_slugify(pdf_path.stem)}_clean.pdf"
            build_clean_pdf(book, clean_pdf_path)

        # Build HTML site including all books in output_dir
        all_books = _collect_all_books(output_dir)
        site_src = output_dir / "site"
        build_site(
            all_books, site_src, site_name=config.site_name, library_dir=output_dir
        )
        build_html(site_src, output_dir=output_dir / "html")

        return book

    return IntermediateBook(
        metadata=metadata,
        chapters=chapters,
    )


def batch_convert(
    pdf_dir: Path,
    *,
    engine: ConversionEngine,
    config: SpinaConfig,
    output_dir: Path,
) -> list[IntermediateBook]:
    """Convert all PDFs in a directory and build a site."""
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    books: list[IntermediateBook] = []
    for pdf_path in pdf_files:
        book = convert_pdf(
            pdf_path, engine=engine, config=config, output_dir=output_dir
        )
        books.append(book)

    # Build site and HTML
    site_dir = output_dir / "site"
    build_site(books, site_dir, site_name=config.site_name, library_dir=output_dir)
    build_html(site_dir, output_dir=output_dir / "html")

    return books
