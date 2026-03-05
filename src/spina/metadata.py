"""Metadata extraction from PDF info dictionaries."""

from pathlib import Path

from pypdf import PdfReader


def extract_pdf_metadata(pdf_path: Path) -> dict[str, str]:
    """Extract title and author from a PDF's info dictionary.

    Returns a dict with 'title' and/or 'author' keys if found.
    Returns empty dict on failure or if metadata is absent.
    """
    try:
        reader = PdfReader(str(pdf_path))
        info = reader.metadata
    except Exception:
        return {}

    if info is None:
        return {}

    result: dict[str, str] = {}

    title = info.get("/Title", "") or ""
    if isinstance(title, str) and title.strip():
        result["title"] = title.strip()

    author = info.get("/Author", "") or ""
    if isinstance(author, str) and author.strip():
        result["author"] = author.strip()

    return result
