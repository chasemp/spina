"""Tests for pipeline - orchestrates PDF → intermediate → outputs."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from spina.config import SpinaConfig
from spina.engines.base import ConversionResult
from spina.models import IntermediateBook
from spina.pipeline import convert_pdf, batch_convert


def _make_fake_engine(
    markdown: str = "# Test\n\nContent.",
    page_count: int = 5,
) -> MagicMock:
    engine = MagicMock()
    engine.convert.return_value = ConversionResult(
        markdown=markdown,
        images={},
        metadata={"title": "Test Doc"},
        page_count=page_count,
    )
    return engine


class TestConvertPdf:
    def test_produces_intermediate_book(self, tmp_path: Path) -> None:
        engine = _make_fake_engine()
        config = SpinaConfig()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        book = convert_pdf(pdf_path, engine=engine, config=config)

        assert isinstance(book, IntermediateBook)
        assert book.metadata.source_filename == "test.pdf"

    def test_writes_intermediate_to_output_dir(self, tmp_path: Path) -> None:
        engine = _make_fake_engine()
        config = SpinaConfig()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")
        output_dir = tmp_path / "output"

        convert_pdf(pdf_path, engine=engine, config=config, output_dir=output_dir)

        assert (output_dir / "test" / "metadata.yaml").exists()

    def test_uses_pdf_title_from_metadata(self, tmp_path: Path) -> None:
        engine = _make_fake_engine()
        engine.convert.return_value = ConversionResult(
            markdown="# Custom Title\n\nContent.",
            images={},
            metadata={"title": "Custom Title"},
            page_count=5,
        )
        config = SpinaConfig()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        book = convert_pdf(pdf_path, engine=engine, config=config)

        assert book.metadata.title == "Custom Title"

    def test_generates_epub_when_configured(self, tmp_path: Path) -> None:
        engine = _make_fake_engine()
        config = SpinaConfig(generate_epub=True)
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")
        output_dir = tmp_path / "output"

        with MagicMock() as mock_pypandoc:
            import spina.outputs.epub_builder as epub_mod
            original = epub_mod.pypandoc
            epub_mod.pypandoc = mock_pypandoc
            try:
                convert_pdf(
                    pdf_path, engine=engine, config=config, output_dir=output_dir
                )
                mock_pypandoc.convert_text.assert_called_once()
            finally:
                epub_mod.pypandoc = original

    def test_skips_epub_when_disabled(self, tmp_path: Path) -> None:
        engine = _make_fake_engine()
        config = SpinaConfig(generate_epub=False)
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")
        output_dir = tmp_path / "output"

        convert_pdf(pdf_path, engine=engine, config=config, output_dir=output_dir)

        epub_files = list(output_dir.rglob("*.epub"))
        assert len(epub_files) == 0


    def test_generates_clean_pdf_when_configured(self, tmp_path: Path) -> None:
        engine = _make_fake_engine()
        config = SpinaConfig(generate_epub=False, generate_clean_pdf=True)
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")
        output_dir = tmp_path / "output"

        with MagicMock() as mock_pypandoc:
            import spina.outputs.pdf_builder as pdf_mod
            original = pdf_mod.pypandoc
            pdf_mod.pypandoc = mock_pypandoc
            try:
                convert_pdf(
                    pdf_path, engine=engine, config=config, output_dir=output_dir
                )
                mock_pypandoc.convert_text.assert_called_once()
                call_kwargs = mock_pypandoc.convert_text.call_args
                assert call_kwargs.kwargs.get("to") == "pdf" or call_kwargs[0][2] == "pdf"
            finally:
                pdf_mod.pypandoc = original

    def test_skips_clean_pdf_when_disabled(self, tmp_path: Path) -> None:
        engine = _make_fake_engine()
        config = SpinaConfig(generate_clean_pdf=False)
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")
        output_dir = tmp_path / "output"

        convert_pdf(pdf_path, engine=engine, config=config, output_dir=output_dir)

        pdf_files = [f for f in output_dir.rglob("*.pdf") if f.name != "test.pdf"]
        assert len(pdf_files) == 0


class TestMetadataExtraction:
    @patch("spina.pipeline.extract_pdf_metadata")
    def test_prefers_pdf_info_dict_title_over_engine(
        self, mock_extract: MagicMock, tmp_path: Path
    ) -> None:
        mock_extract.return_value = {"title": "PDF Info Title", "author": "PDF Author"}
        engine = _make_fake_engine()
        engine.convert.return_value = ConversionResult(
            markdown="# Test\n\nContent.",
            images={},
            metadata={},  # engine has no title
            page_count=5,
        )
        config = SpinaConfig()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        book = convert_pdf(pdf_path, engine=engine, config=config)

        assert book.metadata.title == "PDF Info Title"
        assert book.metadata.author == "PDF Author"

    @patch("spina.pipeline.extract_pdf_metadata")
    def test_falls_back_to_engine_metadata(
        self, mock_extract: MagicMock, tmp_path: Path
    ) -> None:
        mock_extract.return_value = {}  # PDF info dict has nothing
        engine = _make_fake_engine()
        engine.convert.return_value = ConversionResult(
            markdown="# Test\n\nContent.",
            images={},
            metadata={"title": "Engine Title", "author": "Engine Author"},
            page_count=5,
        )
        config = SpinaConfig()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        book = convert_pdf(pdf_path, engine=engine, config=config)

        assert book.metadata.title == "Engine Title"
        assert book.metadata.author == "Engine Author"

    @patch("spina.pipeline.extract_pdf_metadata")
    def test_falls_back_to_filename_when_no_metadata(
        self, mock_extract: MagicMock, tmp_path: Path
    ) -> None:
        mock_extract.return_value = {}
        engine = _make_fake_engine()
        engine.convert.return_value = ConversionResult(
            markdown="No headings here.\n\nJust content.",
            images={},
            metadata={},
            page_count=5,
        )
        config = SpinaConfig()
        pdf_path = tmp_path / "my_book_title.pdf"
        pdf_path.write_bytes(b"fake pdf")

        book = convert_pdf(pdf_path, engine=engine, config=config)

        assert book.metadata.title == "my_book_title"

    @patch("spina.pipeline.extract_pdf_metadata")
    def test_cleans_up_filename_for_title(
        self, mock_extract: MagicMock, tmp_path: Path
    ) -> None:
        mock_extract.return_value = {}
        engine = _make_fake_engine()
        engine.convert.return_value = ConversionResult(
            markdown="Content only.",
            images={},
            metadata={},
            page_count=5,
        )
        config = SpinaConfig()
        pdf_path = tmp_path / "Bach, C. Ph. E.-Essay on Keyboard Instruments 1974.pdf"
        pdf_path.write_bytes(b"fake pdf")

        book = convert_pdf(pdf_path, engine=engine, config=config)

        assert book.metadata.title == "Bach, C. Ph. E.-Essay on Keyboard Instruments 1974"


class TestPostProcessing:
    def test_drop_cap_repair_runs_before_splitting(self, tmp_path: Path) -> None:
        # Markdown with a heading and a TOC entry missing first letter
        markdown = (
            "## Simple Unison\n\n"
            "Content.\n\n"
            "| imple Unison | 20 |\n"
            "|---|---|\n"
        )
        engine = _make_fake_engine(markdown=markdown, page_count=50)
        config = SpinaConfig(generate_epub=False)
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")
        output_dir = tmp_path / "output"

        book = convert_pdf(
            pdf_path, engine=engine, config=config, output_dir=output_dir
        )

        # The repaired TOC entry should appear in one of the chapters
        all_content = " ".join(ch.content for ch in book.chapters)
        assert "| Simple Unison |" in all_content
        assert "| imple Unison |" not in all_content


class TestSiteIncludesAllBooks:
    def test_convert_pdf_includes_existing_intermediates_in_site(
        self, tmp_path: Path
    ) -> None:
        """When convert_pdf builds a site, it should include all books in output_dir."""
        from spina.intermediate import write_intermediate
        from spina.models import BookMetadata, Chapter, IntermediateBook

        # Pre-existing book in output_dir
        existing_book = IntermediateBook(
            metadata=BookMetadata(
                title="Existing Book",
                author="Author A",
                source_filename="existing.pdf",
                page_count=10,
            ),
            chapters=(Chapter(title="Ch1", content="text", order=0),),
        )
        write_intermediate(existing_book, tmp_path / "output" / "existing")

        # Now convert a new PDF
        engine = _make_fake_engine()
        config = SpinaConfig(generate_epub=False)
        pdf_path = tmp_path / "new_book.pdf"
        pdf_path.write_bytes(b"fake pdf")
        output_dir = tmp_path / "output"

        convert_pdf(pdf_path, engine=engine, config=config, output_dir=output_dir)

        # Site index should mention both books
        index_content = (output_dir / "site" / "docs" / "index.md").read_text()
        assert "Existing Book" in index_content
        assert "Test Doc" in index_content  # title from _make_fake_engine metadata


class TestInfoPageIntegration:
    def test_convert_pdf_passes_library_dir_to_build_site(
        self, tmp_path: Path
    ) -> None:
        engine = _make_fake_engine()
        config = SpinaConfig(generate_epub=False)
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")
        output_dir = tmp_path / "output"

        with patch("spina.pipeline.build_site") as mock_build_site:
            with patch("spina.pipeline.build_html"):
                convert_pdf(
                    pdf_path, engine=engine, config=config, output_dir=output_dir
                )

            mock_build_site.assert_called_once()
            call_kwargs = mock_build_site.call_args
            assert call_kwargs.kwargs.get("library_dir") == output_dir

    def test_batch_convert_passes_library_dir_to_build_site(
        self, tmp_path: Path
    ) -> None:
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "a.pdf").write_bytes(b"fake")

        engine = _make_fake_engine()
        config = SpinaConfig(generate_epub=False)
        output_dir = tmp_path / "output"

        with patch("spina.pipeline.build_site") as mock_build_site:
            with patch("spina.pipeline.build_html"):
                batch_convert(
                    pdf_dir, engine=engine, config=config, output_dir=output_dir
                )

            # batch_convert calls build_site once for the batch (and convert_pdf
            # calls it once per book). The batch call is the last one.
            last_call = mock_build_site.call_args_list[-1]
            assert last_call.kwargs.get("library_dir") == output_dir


class TestBatchConvert:
    def test_converts_all_pdfs_in_directory(self, tmp_path: Path) -> None:
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "a.pdf").write_bytes(b"fake")
        (pdf_dir / "b.pdf").write_bytes(b"fake")
        (pdf_dir / "not_pdf.txt").write_text("ignore")

        engine = _make_fake_engine()
        config = SpinaConfig(generate_epub=False)
        output_dir = tmp_path / "output"

        books = batch_convert(
            pdf_dir, engine=engine, config=config, output_dir=output_dir
        )

        assert len(books) == 2
        assert engine.convert.call_count == 2

    def test_builds_site_after_conversion(self, tmp_path: Path) -> None:
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "a.pdf").write_bytes(b"fake")

        engine = _make_fake_engine()
        config = SpinaConfig(generate_epub=False)
        output_dir = tmp_path / "output"

        batch_convert(pdf_dir, engine=engine, config=config, output_dir=output_dir)

        assert (output_dir / "site" / "mkdocs.yml").exists()
        assert (output_dir / "site" / "docs" / "index.md").exists()

    def test_produces_html_output(self, tmp_path: Path) -> None:
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "a.pdf").write_bytes(b"fake")

        engine = _make_fake_engine()
        config = SpinaConfig(generate_epub=False)
        output_dir = tmp_path / "output"

        batch_convert(pdf_dir, engine=engine, config=config, output_dir=output_dir)

        assert (output_dir / "html" / "index.html").exists()

    def test_single_convert_produces_html_output(self, tmp_path: Path) -> None:
        engine = _make_fake_engine()
        config = SpinaConfig(generate_epub=False)
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")
        output_dir = tmp_path / "output"

        convert_pdf(pdf_path, engine=engine, config=config, output_dir=output_dir)

        assert (output_dir / "html" / "index.html").exists()
