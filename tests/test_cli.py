"""Tests for CLI - Click commands for convert, batch, build-site."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from spina.cli import main


class TestCliConvert:
    def test_convert_requires_pdf_argument(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["convert"])
        assert result.exit_code != 0

    @patch("spina.cli._create_engine")
    @patch("spina.cli.convert_pdf")
    def test_convert_calls_pipeline(
        self,
        mock_convert: MagicMock,
        mock_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake")
        mock_convert.return_value = MagicMock()

        runner = CliRunner()
        result = runner.invoke(
            main, ["convert", str(pdf_path), "-o", str(tmp_path / "out")]
        )

        assert result.exit_code == 0
        mock_convert.assert_called_once()

    @patch("spina.cli._create_engine")
    @patch("spina.cli.convert_pdf")
    def test_convert_passes_enable_gpu_flag(
        self,
        mock_convert: MagicMock,
        mock_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake")
        mock_convert.return_value = MagicMock()

        runner = CliRunner()
        runner.invoke(
            main,
            ["convert", str(pdf_path), "-o", str(tmp_path / "out"), "--enable-gpu"],
        )

        call_kwargs = mock_convert.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
        assert config.gpu is True


class TestCliBatch:
    def test_batch_requires_directory_argument(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["batch"])
        assert result.exit_code != 0

    @patch("spina.cli._create_engine")
    @patch("spina.cli.batch_convert")
    def test_batch_calls_pipeline(
        self,
        mock_batch: MagicMock,
        mock_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        mock_batch.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            main, ["batch", str(pdf_dir), "-o", str(tmp_path / "out")]
        )

        assert result.exit_code == 0
        mock_batch.assert_called_once()


class TestCliBuildSite:
    @patch("spina.cli.build_site_from_intermediate")
    def test_build_site_calls_pipeline(
        self,
        mock_build: MagicMock,
        tmp_path: Path,
    ) -> None:
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(main, ["build-site", str(output_dir)])

        assert result.exit_code == 0
        mock_build.assert_called_once()


class TestCliCleanPdf:
    @patch("spina.cli._create_engine")
    @patch("spina.cli.convert_pdf")
    def test_convert_passes_clean_pdf_flag(
        self,
        mock_convert: MagicMock,
        mock_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake")
        mock_convert.return_value = MagicMock()

        runner = CliRunner()
        runner.invoke(
            main,
            ["convert", str(pdf_path), "-o", str(tmp_path / "out"), "--clean-pdf"],
        )

        call_kwargs = mock_convert.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
        assert config.generate_clean_pdf is True


class TestBuildSiteFromIntermediate:
    @patch("spina.cli.build_html")
    @patch("spina.cli.build_site")
    @patch("spina.cli.read_intermediate")
    def test_generates_html_output(
        self,
        mock_read: MagicMock,
        mock_build_site: MagicMock,
        mock_build_html: MagicMock,
        tmp_path: Path,
    ) -> None:
        from spina.cli import build_site_from_intermediate

        book_dir = tmp_path / "my-book"
        book_dir.mkdir()
        (book_dir / "metadata.yaml").write_text("title: Test")
        mock_read.return_value = MagicMock()

        build_site_from_intermediate(tmp_path, site_name="Test")

        mock_build_html.assert_called_once()

    @patch("spina.cli.build_html")
    @patch("spina.cli.build_site")
    @patch("spina.cli.read_intermediate")
    def test_passes_library_dir_to_build_site(
        self,
        mock_read: MagicMock,
        mock_build_site: MagicMock,
        mock_build_html: MagicMock,
        tmp_path: Path,
    ) -> None:
        from spina.cli import build_site_from_intermediate

        book_dir = tmp_path / "my-book"
        book_dir.mkdir()
        (book_dir / "metadata.yaml").write_text("title: Test")
        mock_read.return_value = MagicMock()

        build_site_from_intermediate(tmp_path, site_name="Test")

        call_kwargs = mock_build_site.call_args
        assert call_kwargs.kwargs.get("library_dir") == tmp_path


class TestDefaultOutputDir:
    @patch("spina.cli._create_engine")
    @patch("spina.cli.convert_pdf")
    def test_convert_defaults_to_library_dir(
        self,
        mock_convert: MagicMock,
        mock_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake")
        mock_convert.return_value = MagicMock()

        runner = CliRunner()
        result = runner.invoke(main, ["convert", str(pdf_path)])

        assert result.exit_code == 0
        call_kwargs = mock_convert.call_args
        output_dir = call_kwargs.kwargs.get("output_dir") or call_kwargs[1].get("output_dir")
        assert output_dir == Path("library")
