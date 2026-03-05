"""EPUB builder - converts intermediate book to EPUB via pypandoc."""

import re
from pathlib import Path

import pypandoc

from spina.models import IntermediateBook


def build_epub(book: IntermediateBook, output_path: Path) -> None:
    """Build an EPUB3 file from an IntermediateBook."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    parts: list[str] = []
    for chapter in sorted(book.chapters, key=lambda c: c.order):
        parts.append(f"# {chapter.title}\n\n{chapter.content}")

    combined_markdown = "\n\n".join(parts)

    # Sanitize HTML for XHTML compatibility (EPUB requires valid XHTML)
    combined_markdown = re.sub(r'<br\s*(?!/)', '<br/', combined_markdown)

    extra_args = [
        f"--metadata=title:{book.metadata.title}",
        f"--metadata=author:{book.metadata.author}",
        "--webtex",
    ]

    if book.image_dir and book.image_dir.exists():
        extra_args.append(f"--resource-path={book.image_dir}")

    pypandoc.convert_text(
        combined_markdown,
        format="markdown",
        to="epub3",
        outputfile=str(output_path),
        extra_args=extra_args,
    )
