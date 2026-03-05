"""Tests for site builder - generates MkDocs site from intermediate books."""

from pathlib import Path
from unittest.mock import patch, MagicMock

from spina.outputs.site_builder import (
    build_site,
    build_html,
    _detect_downloads,
    _copy_downloads,
    _create_markdown_zip,
)
from spina.models import DownloadLink
from tests.conftest import make_chapter, make_intermediate_book, make_metadata


class TestBuildSite:
    def test_creates_docs_directory(self, tmp_path: Path) -> None:
        book = make_intermediate_book()

        build_site([book], tmp_path, site_name="Test")

        assert (tmp_path / "docs").exists()

    def test_writes_mkdocs_yml(self, tmp_path: Path) -> None:
        book = make_intermediate_book()

        build_site([book], tmp_path, site_name="Test")

        assert (tmp_path / "mkdocs.yml").exists()

    def test_writes_chapter_files_to_docs(self, tmp_path: Path) -> None:
        chapters = (
            make_chapter(title="Ch 1", content="Content 1", order=0),
            make_chapter(title="Ch 2", content="Content 2", order=1),
        )
        book = make_intermediate_book(
            metadata=make_metadata(title="My Book"),
            chapters=chapters,
        )

        build_site([book], tmp_path, site_name="Test")

        docs_dir = tmp_path / "docs"
        md_files = list(docs_dir.rglob("*.md"))
        assert len(md_files) >= 3

    def test_writes_index_page(self, tmp_path: Path) -> None:
        book = make_intermediate_book()

        build_site([book], tmp_path, site_name="Test")

        index_file = tmp_path / "docs" / "index.md"
        assert index_file.exists()
        content = index_file.read_text()
        assert "Test" in content

    def test_handles_multiple_books(self, tmp_path: Path) -> None:
        book1 = make_intermediate_book(
            metadata=make_metadata(title="Book A", source_filename="a.pdf"),
        )
        book2 = make_intermediate_book(
            metadata=make_metadata(title="Book B", source_filename="b.pdf"),
        )

        build_site([book1, book2], tmp_path, site_name="Library")

        index_content = (tmp_path / "docs" / "index.md").read_text()
        assert "Book A" in index_content
        assert "Book B" in index_content

    def test_creates_overrides_directory(self, tmp_path: Path) -> None:
        book = make_intermediate_book()

        build_site([book], tmp_path, site_name="Test")

        overrides = tmp_path / "overrides"
        assert overrides.exists()

    def test_rewrites_image_paths_to_images_subdir(self, tmp_path: Path) -> None:
        chapters = (
            make_chapter(
                title="Ch 1",
                content="Some text\n\n![](_page_1_Picture_2.jpeg)\n\nMore text",
                order=0,
                images=("_page_1_Picture_2.jpeg",),
            ),
        )
        image_dir = tmp_path / "book_images"
        image_dir.mkdir()
        (image_dir / "_page_1_Picture_2.jpeg").write_bytes(b"fake image")

        book = make_intermediate_book(
            metadata=make_metadata(title="My Book"),
            chapters=chapters,
            image_dir=image_dir,
        )

        build_site([book], tmp_path, site_name="Test")

        chapter_file = tmp_path / "docs" / "my_book" / "000_ch_1.md"
        content = chapter_file.read_text()
        assert "![](images/_page_1_Picture_2.jpeg)" in content
        assert "![](_page_1_Picture_2.jpeg)" not in content


class TestMathExtensionConfig:
    def test_mkdocs_config_includes_arithmatex_extension(self, tmp_path: Path) -> None:
        import yaml

        book = make_intermediate_book()

        build_site([book], tmp_path, site_name="Test")

        config = yaml.safe_load((tmp_path / "mkdocs.yml").read_text())
        extensions = config.get("markdown_extensions", [])
        arithmatex_entries = [
            e for e in extensions
            if (isinstance(e, str) and e == "pymdownx.arithmatex")
            or (isinstance(e, dict) and "pymdownx.arithmatex" in e)
        ]
        assert len(arithmatex_entries) == 1

    def test_arithmatex_configured_with_generic_true(self, tmp_path: Path) -> None:
        import yaml

        book = make_intermediate_book()

        build_site([book], tmp_path, site_name="Test")

        config = yaml.safe_load((tmp_path / "mkdocs.yml").read_text())
        extensions = config.get("markdown_extensions", [])
        arithmatex = next(
            (e for e in extensions if isinstance(e, dict) and "pymdownx.arithmatex" in e),
            None,
        )
        assert arithmatex is not None
        assert arithmatex["pymdownx.arithmatex"]["generic"] is True

    def test_mkdocs_config_includes_mathjax_extra_javascript(self, tmp_path: Path) -> None:
        import yaml

        book = make_intermediate_book()

        build_site([book], tmp_path, site_name="Test")

        config = yaml.safe_load((tmp_path / "mkdocs.yml").read_text())
        extra_js = config.get("extra_javascript", [])
        assert any("mathjax" in str(entry).lower() for entry in extra_js)


class TestDetectDownloads:
    def test_detects_epub(self, tmp_path: Path) -> None:
        (tmp_path / "my_book.epub").write_bytes(b"fake epub")

        downloads = _detect_downloads("my_book", tmp_path)

        assert any(d.label == "EPUB" for d in downloads)
        assert any(d.filename == "my_book.epub" for d in downloads)

    def test_detects_clean_pdf(self, tmp_path: Path) -> None:
        (tmp_path / "my_book_clean.pdf").write_bytes(b"fake pdf")

        downloads = _detect_downloads("my_book", tmp_path)

        assert any(d.label == "Clean PDF" for d in downloads)
        assert any(d.filename == "my_book_clean.pdf" for d in downloads)

    def test_returns_empty_when_no_artifacts(self, tmp_path: Path) -> None:
        downloads = _detect_downloads("my_book", tmp_path)

        assert downloads == ()

    def test_detects_both_artifacts(self, tmp_path: Path) -> None:
        (tmp_path / "my_book.epub").write_bytes(b"fake epub")
        (tmp_path / "my_book_clean.pdf").write_bytes(b"fake pdf")

        downloads = _detect_downloads("my_book", tmp_path)

        assert len(downloads) == 2

    def test_detects_markdown_zip(self, tmp_path: Path) -> None:
        (tmp_path / "my_book_markdown.zip").write_bytes(b"fake zip")

        downloads = _detect_downloads("my_book", tmp_path)

        assert any(d.label == "Markdown" for d in downloads)
        assert any(d.filename == "my_book_markdown.zip" for d in downloads)


class TestMultiBookNavWithInfoPages:
    def test_nav_includes_about_as_first_item_when_enabled(
        self, tmp_path: Path
    ) -> None:
        import yaml
        from spina.outputs.site_builder import _generate_multi_book_config

        book = make_intermediate_book(
            metadata=make_metadata(title="My Book"),
        )

        config = _generate_multi_book_config(
            [book], site_name="Test", has_info_pages=True
        )

        parsed = yaml.safe_load(config)
        book_nav = parsed["nav"][1]["My Book"]
        assert book_nav[0] == {"About": "my_book/info.md"}

    def test_nav_excludes_about_by_default(self, tmp_path: Path) -> None:
        import yaml
        from spina.outputs.site_builder import _generate_multi_book_config

        book = make_intermediate_book(
            metadata=make_metadata(title="My Book"),
        )

        config = _generate_multi_book_config([book], site_name="Test")

        parsed = yaml.safe_load(config)
        book_nav = parsed["nav"][1]["My Book"]
        assert not any("About" in entry for entry in book_nav)


class TestCreateMarkdownZip:
    def test_creates_zip_from_chapters_directory(self, tmp_path: Path) -> None:
        chapters_dir = tmp_path / "my_book" / "chapters"
        chapters_dir.mkdir(parents=True)
        (chapters_dir / "000_intro.md").write_text("# Intro\n\nContent.")
        (chapters_dir / "001_main.md").write_text("# Main\n\nMore content.")

        result = _create_markdown_zip("my_book", tmp_path)

        assert result is not None
        assert result.exists()
        assert result.name == "my_book_markdown.zip"

    def test_zip_contains_chapter_files(self, tmp_path: Path) -> None:
        import zipfile

        chapters_dir = tmp_path / "my_book" / "chapters"
        chapters_dir.mkdir(parents=True)
        (chapters_dir / "000_intro.md").write_text("# Intro\n\nContent.")

        result = _create_markdown_zip("my_book", tmp_path)

        assert result is not None
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
            assert "000_intro.md" in names

    def test_returns_none_when_no_chapters_directory(self, tmp_path: Path) -> None:
        result = _create_markdown_zip("my_book", tmp_path)

        assert result is None

    def test_returns_none_when_chapters_directory_empty(self, tmp_path: Path) -> None:
        chapters_dir = tmp_path / "my_book" / "chapters"
        chapters_dir.mkdir(parents=True)

        result = _create_markdown_zip("my_book", tmp_path)

        assert result is None


class TestCopyDownloads:
    def test_copies_files_to_destination(self, tmp_path: Path) -> None:
        src = tmp_path / "library"
        src.mkdir()
        (src / "book.epub").write_bytes(b"epub data")

        dest = tmp_path / "docs" / "book"
        dest.mkdir(parents=True)

        downloads = (DownloadLink(label="EPUB", filename="book.epub"),)
        _copy_downloads(downloads, library_dir=src, dest_dir=dest)

        assert (dest / "book.epub").exists()
        assert (dest / "book.epub").read_bytes() == b"epub data"


class TestBuildSiteWithInfoPages:
    def test_writes_info_page_when_library_dir_given(self, tmp_path: Path) -> None:
        book = make_intermediate_book(
            metadata=make_metadata(title="My Book", source_filename="my_book.pdf"),
        )
        library_dir = tmp_path / "library"
        library_dir.mkdir()

        site_dir = tmp_path / "site"
        build_site([book], site_dir, site_name="Test", library_dir=library_dir)

        info_page = site_dir / "docs" / "my_book" / "info.md"
        assert info_page.exists()
        content = info_page.read_text()
        assert "# My Book" in content

    def test_copies_artifacts_when_library_dir_given(self, tmp_path: Path) -> None:
        book = make_intermediate_book(
            metadata=make_metadata(title="My Book", source_filename="my_book.pdf"),
        )
        library_dir = tmp_path / "library"
        library_dir.mkdir()
        (library_dir / "my_book.epub").write_bytes(b"epub data")

        site_dir = tmp_path / "site"
        build_site([book], site_dir, site_name="Test", library_dir=library_dir)

        assert (site_dir / "docs" / "my_book" / "my_book.epub").exists()

    def test_no_info_page_when_library_dir_is_none(self, tmp_path: Path) -> None:
        book = make_intermediate_book(
            metadata=make_metadata(title="My Book"),
        )

        build_site([book], tmp_path, site_name="Test")

        info_page = tmp_path / "docs" / "my_book" / "info.md"
        assert not info_page.exists()

    def test_info_page_includes_download_links(self, tmp_path: Path) -> None:
        book = make_intermediate_book(
            metadata=make_metadata(title="My Book", source_filename="my_book.pdf"),
        )
        library_dir = tmp_path / "library"
        library_dir.mkdir()
        (library_dir / "my_book.epub").write_bytes(b"epub data")

        site_dir = tmp_path / "site"
        build_site([book], site_dir, site_name="Test", library_dir=library_dir)

        info_page = site_dir / "docs" / "my_book" / "info.md"
        content = info_page.read_text()
        assert "[EPUB]" in content

    def test_creates_markdown_zip_and_includes_download_link(
        self, tmp_path: Path
    ) -> None:
        book = make_intermediate_book(
            metadata=make_metadata(title="My Book", source_filename="my_book.pdf"),
        )
        library_dir = tmp_path / "library"
        library_dir.mkdir()
        # Create the intermediate chapters directory
        chapters_dir = library_dir / "my_book" / "chapters"
        chapters_dir.mkdir(parents=True)
        (chapters_dir / "000_intro.md").write_text("# Intro\n\nContent.")

        site_dir = tmp_path / "site"
        build_site([book], site_dir, site_name="Test", library_dir=library_dir)

        # Zip should be created in library_dir
        assert (library_dir / "my_book_markdown.zip").exists()
        # Info page should have the download link
        info_page = site_dir / "docs" / "my_book" / "info.md"
        content = info_page.read_text()
        assert "[Markdown]" in content
        # Zip should be copied into docs
        assert (site_dir / "docs" / "my_book" / "my_book_markdown.zip").exists()


class TestBuildHtml:
    def test_produces_index_html(self, tmp_path: Path) -> None:
        book = make_intermediate_book()
        site_dir = tmp_path / "site"

        # First build the mkdocs source
        build_site([book], site_dir, site_name="Test")
        # Then build the HTML
        build_html(site_dir, output_dir=tmp_path / "html")

        assert (tmp_path / "html" / "index.html").exists()

    def test_html_contains_site_name(self, tmp_path: Path) -> None:
        book = make_intermediate_book()
        site_dir = tmp_path / "site"

        build_site([book], site_dir, site_name="My Library")
        build_html(site_dir, output_dir=tmp_path / "html")

        html = (tmp_path / "html" / "index.html").read_text()
        assert "My Library" in html
