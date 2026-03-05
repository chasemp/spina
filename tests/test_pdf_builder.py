"""Tests for clean PDF builder - generates searchable PDF from intermediate book."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from tests.conftest import make_chapter, make_intermediate_book, make_metadata


class TestBuildCleanPdf:
    @patch("spina.outputs.pdf_builder.pypandoc")
    def test_calls_pypandoc_with_pdf_format(
        self, mock_pypandoc: MagicMock, tmp_path: Path
    ) -> None:
        from spina.outputs.pdf_builder import build_clean_pdf

        book = make_intermediate_book()
        output_path = tmp_path / "clean.pdf"

        build_clean_pdf(book, output_path)

        mock_pypandoc.convert_text.assert_called_once()
        call_kwargs = mock_pypandoc.convert_text.call_args
        assert call_kwargs.kwargs.get("to") == "pdf" or call_kwargs[0][2] == "pdf"

    @patch("spina.outputs.pdf_builder.pypandoc")
    def test_combines_chapters_in_order(
        self, mock_pypandoc: MagicMock, tmp_path: Path
    ) -> None:
        from spina.outputs.pdf_builder import build_clean_pdf

        chapters = (
            make_chapter(title="Ch 1", content="First content", order=0),
            make_chapter(title="Ch 2", content="Second content", order=1),
        )
        book = make_intermediate_book(chapters=chapters)
        output_path = tmp_path / "clean.pdf"

        build_clean_pdf(book, output_path)

        call_args = mock_pypandoc.convert_text.call_args
        markdown_input = call_args[0][0] if call_args[0] else call_args.kwargs.get("source")
        assert "First content" in markdown_input
        assert "Second content" in markdown_input
        assert markdown_input.index("First") < markdown_input.index("Second")

    @patch("spina.outputs.pdf_builder.pypandoc")
    def test_sets_title_metadata(
        self, mock_pypandoc: MagicMock, tmp_path: Path
    ) -> None:
        from spina.outputs.pdf_builder import build_clean_pdf

        book = make_intermediate_book(
            metadata=make_metadata(title="My Book", author="Jane Doe"),
        )
        output_path = tmp_path / "clean.pdf"

        build_clean_pdf(book, output_path)

        call_kwargs = mock_pypandoc.convert_text.call_args
        extra_args = call_kwargs.kwargs.get("extra_args") or call_kwargs[1].get("extra_args", [])
        title_args = [a for a in extra_args if "title" in a.lower()]
        assert len(title_args) > 0

    @patch("spina.outputs.pdf_builder.pypandoc")
    def test_creates_parent_directory(
        self, mock_pypandoc: MagicMock, tmp_path: Path
    ) -> None:
        from spina.outputs.pdf_builder import build_clean_pdf

        book = make_intermediate_book()
        output_path = tmp_path / "nested" / "dir" / "clean.pdf"

        build_clean_pdf(book, output_path)

        assert output_path.parent.exists()

    @patch("spina.outputs.pdf_builder.pypandoc")
    def test_outputs_to_specified_path(
        self, mock_pypandoc: MagicMock, tmp_path: Path
    ) -> None:
        from spina.outputs.pdf_builder import build_clean_pdf

        book = make_intermediate_book()
        output_path = tmp_path / "output.pdf"

        build_clean_pdf(book, output_path)

        call_kwargs = mock_pypandoc.convert_text.call_args
        outputfile = call_kwargs.kwargs.get("outputfile")
        assert outputfile == str(output_path)

    @patch("spina.outputs.pdf_builder.pypandoc")
    def test_passes_webtex_for_math_rendering(
        self, mock_pypandoc: MagicMock, tmp_path: Path
    ) -> None:
        from spina.outputs.pdf_builder import build_clean_pdf

        book = make_intermediate_book()
        output_path = tmp_path / "clean.pdf"

        build_clean_pdf(book, output_path)

        call_kwargs = mock_pypandoc.convert_text.call_args
        extra_args = call_kwargs.kwargs.get("extra_args") or call_kwargs[1].get("extra_args", [])
        assert "--webtex" in extra_args

    @patch("spina.outputs.pdf_builder.pypandoc")
    def test_returns_false_when_pdflatex_missing(
        self, mock_pypandoc: MagicMock, tmp_path: Path
    ) -> None:
        from spina.outputs.pdf_builder import build_clean_pdf

        mock_pypandoc.convert_text.side_effect = RuntimeError(
            'Pandoc died with exitcode "47": pdflatex not found.'
        )
        book = make_intermediate_book()
        output_path = tmp_path / "clean.pdf"

        result = build_clean_pdf(book, output_path)

        assert result is False

    @patch("spina.outputs.pdf_builder.pypandoc")
    def test_returns_true_on_success(
        self, mock_pypandoc: MagicMock, tmp_path: Path
    ) -> None:
        from spina.outputs.pdf_builder import build_clean_pdf

        book = make_intermediate_book()
        output_path = tmp_path / "clean.pdf"

        result = build_clean_pdf(book, output_path)

        assert result is True
