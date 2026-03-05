"""Clean PDF builder - generates searchable PDF from intermediate book via pypandoc."""

import logging
from pathlib import Path

import pypandoc

from spina.models import IntermediateBook

logger = logging.getLogger(__name__)


def build_clean_pdf(book: IntermediateBook, output_path: Path) -> bool:
    """Build a clean, searchable PDF from an IntermediateBook.

    Returns True on success, False if PDF engine is unavailable.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    parts: list[str] = []
    for chapter in sorted(book.chapters, key=lambda c: c.order):
        parts.append(f"# {chapter.title}\n\n{chapter.content}")

    combined_markdown = "\n\n".join(parts)

    extra_args = [
        f"--metadata=title:{book.metadata.title}",
        f"--metadata=author:{book.metadata.author}",
        "--webtex",
    ]

    if book.image_dir and book.image_dir.exists():
        extra_args.append(f"--resource-path={book.image_dir}")

    try:
        pypandoc.convert_text(
            combined_markdown,
            format="markdown",
            to="pdf",
            outputfile=str(output_path),
            extra_args=extra_args,
        )
        return True
    except RuntimeError as e:
        if "pdflatex not found" in str(e) or "pdf-engine" in str(e):
            logger.warning(
                "Clean PDF generation skipped: no PDF engine found. "
                "Install pdflatex (texlive) or another pandoc PDF engine."
            )
            return False
        raise
