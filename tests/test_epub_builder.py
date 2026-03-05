"""Tests for EPUB builder - converts intermediate book to EPUB."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from spina.outputs.epub_builder import build_epub
from tests.conftest import make_chapter, make_intermediate_book, make_metadata


class TestBuildEpub:
    def test_creates_combined_markdown_for_pypandoc(self, tmp_path: Path) -> None:
        chapters = (
            make_chapter(title="Ch 1", content="Content one.", order=0),
            make_chapter(title="Ch 2", content="Content two.", order=1),
        )
        book = make_intermediate_book(
            metadata=make_metadata(title="Test Book"),
            chapters=chapters,
        )

        with patch("spina.outputs.epub_builder.pypandoc") as mock_pypandoc:
            build_epub(book, tmp_path / "output.epub")

            call_args = mock_pypandoc.convert_text.call_args
            source = call_args[0][0]
            assert "# Ch 1" in source
            assert "Content one." in source
            assert "# Ch 2" in source
            assert "Content two." in source

    def test_calls_pypandoc_with_epub3_format(self, tmp_path: Path) -> None:
        book = make_intermediate_book()

        with patch("spina.outputs.epub_builder.pypandoc") as mock_pypandoc:
            build_epub(book, tmp_path / "output.epub")

            call_args = mock_pypandoc.convert_text.call_args
            assert call_args[1]["to"] == "epub3"

    def test_sets_title_metadata(self, tmp_path: Path) -> None:
        book = make_intermediate_book(
            metadata=make_metadata(title="My Title", author="Author Name")
        )

        with patch("spina.outputs.epub_builder.pypandoc") as mock_pypandoc:
            build_epub(book, tmp_path / "output.epub")

            call_args = mock_pypandoc.convert_text.call_args
            extra_args = call_args[1].get("extra_args", [])
            assert any("My Title" in arg for arg in extra_args)

    def test_outputs_to_specified_path(self, tmp_path: Path) -> None:
        book = make_intermediate_book()
        output_path = tmp_path / "books" / "output.epub"

        with patch("spina.outputs.epub_builder.pypandoc") as mock_pypandoc:
            build_epub(book, output_path)

            call_args = mock_pypandoc.convert_text.call_args
            assert call_args[1]["outputfile"] == str(output_path)

    def test_passes_resource_path_for_image_dir(self, tmp_path: Path) -> None:
        img_dir = tmp_path / "images"
        img_dir.mkdir()
        (img_dir / "fig1.png").write_bytes(b"\x89PNG")

        book = make_intermediate_book(image_dir=img_dir)

        with patch("spina.outputs.epub_builder.pypandoc") as mock_pypandoc:
            build_epub(book, tmp_path / "output.epub")

            call_args = mock_pypandoc.convert_text.call_args
            extra_args = call_args[1].get("extra_args", [])
            resource_args = [a for a in extra_args if "--resource-path" in a]
            assert len(resource_args) == 1
            assert str(img_dir) in resource_args[0]

    def test_no_resource_path_when_no_image_dir(self, tmp_path: Path) -> None:
        book = make_intermediate_book()  # image_dir defaults to None

        with patch("spina.outputs.epub_builder.pypandoc") as mock_pypandoc:
            build_epub(book, tmp_path / "output.epub")

            call_args = mock_pypandoc.convert_text.call_args
            extra_args = call_args[1].get("extra_args", [])
            resource_args = [a for a in extra_args if "--resource-path" in a]
            assert len(resource_args) == 0

    def test_passes_webtex_for_math_rendering(self, tmp_path: Path) -> None:
        book = make_intermediate_book()

        with patch("spina.outputs.epub_builder.pypandoc") as mock_pypandoc:
            build_epub(book, tmp_path / "output.epub")

            call_args = mock_pypandoc.convert_text.call_args
            extra_args = call_args[1].get("extra_args", [])
            assert "--webtex" in extra_args

    def test_sanitizes_br_tags_for_xhtml(self, tmp_path: Path) -> None:
        chapters = (
            make_chapter(
                title="Ch 1",
                content="| Name<br>Here | Value |\n|---|---|\n| A | 1 |",
                order=0,
            ),
        )
        book = make_intermediate_book(chapters=chapters)

        with patch("spina.outputs.epub_builder.pypandoc") as mock_pypandoc:
            build_epub(book, tmp_path / "output.epub")

            call_args = mock_pypandoc.convert_text.call_args
            source = call_args[0][0]
            assert "<br>" not in source
            assert "<br/>" in source
