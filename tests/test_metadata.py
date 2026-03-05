"""Tests for metadata extraction from PDF info dictionaries."""

from pathlib import Path

from spina.metadata import extract_pdf_metadata


class TestExtractPdfMetadata:
    def test_extracts_title_from_pdf_info(self, tmp_path: Path) -> None:
        pdf_path = _create_pdf_with_metadata(tmp_path, title="My Great Book")

        metadata = extract_pdf_metadata(pdf_path)

        assert metadata["title"] == "My Great Book"

    def test_extracts_author_from_pdf_info(self, tmp_path: Path) -> None:
        pdf_path = _create_pdf_with_metadata(tmp_path, author="Jane Doe")

        metadata = extract_pdf_metadata(pdf_path)

        assert metadata["author"] == "Jane Doe"

    def test_returns_empty_dict_for_pdf_without_metadata(self, tmp_path: Path) -> None:
        pdf_path = _create_pdf_with_metadata(tmp_path)

        metadata = extract_pdf_metadata(pdf_path)

        assert metadata.get("title", "") == ""
        assert metadata.get("author", "") == ""

    def test_handles_corrupt_or_invalid_pdf(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "bad.pdf"
        pdf_path.write_bytes(b"not a real pdf")

        metadata = extract_pdf_metadata(pdf_path)

        assert isinstance(metadata, dict)

    def test_strips_whitespace_from_values(self, tmp_path: Path) -> None:
        pdf_path = _create_pdf_with_metadata(tmp_path, title="  Padded Title  ")

        metadata = extract_pdf_metadata(pdf_path)

        assert metadata["title"] == "Padded Title"


def _create_pdf_with_metadata(
    tmp_path: Path,
    *,
    title: str = "",
    author: str = "",
) -> Path:
    """Create a minimal PDF with given metadata using pypdf."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)

    if title or author:
        info = {}
        if title:
            info["/Title"] = title
        if author:
            info["/Author"] = author
        writer.add_metadata(info)

    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, "wb") as f:
        writer.write(f)
    return pdf_path
