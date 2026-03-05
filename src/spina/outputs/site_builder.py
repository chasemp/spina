"""Site builder - generates MkDocs site from intermediate books."""

import re
import subprocess
from pathlib import Path

import shutil
import zipfile

from spina.intermediate import _slugify
from spina.models import DownloadLink, IntermediateBook
from spina.site.book_info_generator import generate_book_info_page
from spina.site.index_generator import generate_index_page
from spina.site.mkdocs_config import generate_mkdocs_config


def build_site(
    books: list[IntermediateBook],
    output_dir: Path,
    *,
    site_name: str,
    library_dir: Path | None = None,
) -> None:
    """Build a MkDocs site directory from a list of intermediate books."""
    docs_dir = output_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Create overrides directory for theme customization
    overrides_dir = output_dir / "overrides"
    overrides_dir.mkdir(exist_ok=True)

    # Generate index page
    all_metadata = [book.metadata for book in books]
    index_content = generate_index_page(all_metadata, site_name=site_name)
    (docs_dir / "index.md").write_text(index_content)

    has_info_pages = library_dir is not None

    # Write chapter files for each book
    for book in books:
        book_slug = _slugify(book.metadata.title)
        book_dir = docs_dir / book_slug
        book_dir.mkdir(exist_ok=True)

        has_images = book.image_dir and book.image_dir.exists()
        for chapter in sorted(book.chapters, key=lambda c: c.order):
            filename = f"{chapter.order:03d}_{_slugify(chapter.title)}.md"
            chapter_content = chapter.content
            if has_images:
                chapter_content = _rewrite_image_paths(chapter_content)
            content = f"# {chapter.title}\n\n{chapter_content}\n"
            (book_dir / filename).write_text(content)

        # Copy images if available
        if book.image_dir and book.image_dir.exists():
            img_dest = book_dir / "images"
            img_dest.mkdir(exist_ok=True)
            for img in book.image_dir.iterdir():
                (img_dest / img.name).write_bytes(img.read_bytes())

        # Generate info page and copy download artifacts
        if library_dir is not None:
            artifact_slug = _slugify(Path(book.metadata.source_filename).stem)
            _create_markdown_zip(artifact_slug, library_dir)
            downloads = _detect_downloads(artifact_slug, library_dir)
            info_content = generate_book_info_page(
                book.metadata,
                chapter_count=len(book.chapters),
                downloads=downloads,
            )
            (book_dir / "info.md").write_text(info_content)
            _copy_downloads(downloads, library_dir=library_dir, dest_dir=book_dir)

    # Generate mkdocs.yml (use first book for nav, or generate multi-book nav)
    if books:
        mkdocs_config = _generate_multi_book_config(
            books, site_name=site_name, has_info_pages=has_info_pages
        )
    else:
        mkdocs_config = generate_mkdocs_config(
            books[0], site_name=site_name, has_info_pages=has_info_pages
        )

    (output_dir / "mkdocs.yml").write_text(mkdocs_config)


def _rewrite_image_paths(content: str) -> str:
    """Rewrite bare image filenames to include images/ prefix."""
    return re.sub(
        r'!\[([^\]]*)\]\((?!images/)(?!https?://)([^)]+)\)',
        r'![\1](images/\2)',
        content,
    )


def _create_markdown_zip(artifact_slug: str, library_dir: Path) -> Path | None:
    """Create a zip archive of the markdown chapters for a book.

    Returns the path to the created zip, or None if no chapters exist.
    """
    chapters_dir = library_dir / artifact_slug / "chapters"
    if not chapters_dir.exists():
        return None

    md_files = sorted(chapters_dir.glob("*.md"))
    if not md_files:
        return None

    zip_path = library_dir / f"{artifact_slug}_markdown.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for md_file in md_files:
            zf.write(md_file, md_file.name)

    return zip_path


def _detect_downloads(artifact_slug: str, library_dir: Path) -> tuple[DownloadLink, ...]:
    """Detect available download artifacts (EPUB, clean PDF) in library directory."""
    downloads: list[DownloadLink] = []

    epub_path = library_dir / f"{artifact_slug}.epub"
    if epub_path.exists():
        downloads.append(DownloadLink(label="EPUB", filename=epub_path.name))

    clean_pdf_path = library_dir / f"{artifact_slug}_clean.pdf"
    if clean_pdf_path.exists():
        downloads.append(DownloadLink(label="Clean PDF", filename=clean_pdf_path.name))

    markdown_zip_path = library_dir / f"{artifact_slug}_markdown.zip"
    if markdown_zip_path.exists():
        downloads.append(DownloadLink(label="Markdown", filename=markdown_zip_path.name))

    return tuple(downloads)


def _copy_downloads(
    downloads: tuple[DownloadLink, ...],
    *,
    library_dir: Path,
    dest_dir: Path,
) -> None:
    """Copy download artifact files into the MkDocs docs directory."""
    for link in downloads:
        src = library_dir / link.filename
        if src.exists():
            shutil.copy2(src, dest_dir / link.filename)


def build_html(site_dir: Path, *, output_dir: Path) -> None:
    """Run mkdocs build to produce static HTML from MkDocs source."""
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["mkdocs", "build", "-d", str(output_dir.resolve())],
        cwd=str(site_dir),
        check=True,
        capture_output=True,
    )


def _generate_multi_book_config(
    books: list[IntermediateBook],
    *,
    site_name: str,
    has_info_pages: bool = False,
) -> str:
    """Generate mkdocs.yml for multiple books."""
    import yaml

    nav: list[dict[str, object]] = [{"Home": "index.md"}]

    for book in books:
        book_slug = _slugify(book.metadata.title)
        book_nav: list[dict[str, str]] = []
        if has_info_pages:
            book_nav.append({"About": f"{book_slug}/info.md"})
        for chapter in sorted(book.chapters, key=lambda c: c.order):
            filename = f"{book_slug}/{chapter.order:03d}_{_slugify(chapter.title)}.md"
            book_nav.append({chapter.title: filename})
        nav.append({book.metadata.title: book_nav})

    config = {
        "site_name": site_name,
        "theme": {
            "name": "material",
            "custom_dir": "overrides",
            "features": [
                "navigation.instant",
                "navigation.footer",
                "search.suggest",
                "search.highlight",
            ],
        },
        "nav": nav,
        "markdown_extensions": [
            {"pymdownx.arithmatex": {"generic": True}},
        ],
        "extra_javascript": [
            {"https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js": {"async": True}},
        ],
    }

    return yaml.dump(config, default_flow_style=False, sort_keys=False)
