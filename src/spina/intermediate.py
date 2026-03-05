"""Intermediate format I/O - write/read books as markdown + YAML + images."""

from pathlib import Path

import yaml

from spina.models import BookMetadata, Chapter, IntermediateBook, TocEntry


def write_intermediate(
    book: IntermediateBook,
    output_dir: Path,
    *,
    images: dict[str, bytes] | None = None,
) -> None:
    """Write an IntermediateBook to disk as YAML metadata + chapter markdown files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write metadata
    meta_dict = {
        "title": book.metadata.title,
        "author": book.metadata.author,
        "source_filename": book.metadata.source_filename,
        "page_count": book.metadata.page_count,
        "toc": [
            {"title": e.title, "level": e.level, "page": e.page}
            for e in book.metadata.toc
        ],
    }
    meta_path = output_dir / "metadata.yaml"
    meta_path.write_text(yaml.dump(meta_dict, default_flow_style=False))

    # Write chapters
    chapters_dir = output_dir / "chapters"
    chapters_dir.mkdir(exist_ok=True)
    for chapter in book.chapters:
        frontmatter = yaml.dump(
            {"title": chapter.title, "order": chapter.order, "images": list(chapter.images)},
            default_flow_style=False,
        )
        content = f"---\n{frontmatter}---\n\n{chapter.content}\n"
        filename = f"{chapter.order:03d}_{_slugify(chapter.title)}.md"
        (chapters_dir / filename).write_text(content)

    # Write images
    if images:
        img_dir = output_dir / "images"
        img_dir.mkdir(exist_ok=True)
        for name, data in images.items():
            (img_dir / name).write_bytes(data)


def read_intermediate(input_dir: Path) -> IntermediateBook:
    """Read an IntermediateBook from disk."""
    # Read metadata
    meta_path = input_dir / "metadata.yaml"
    meta_dict = yaml.safe_load(meta_path.read_text())
    toc = tuple(
        TocEntry(title=e["title"], level=e["level"], page=e["page"])
        for e in meta_dict.get("toc", [])
    )
    metadata = BookMetadata(
        title=meta_dict["title"],
        author=meta_dict["author"],
        source_filename=meta_dict["source_filename"],
        page_count=meta_dict["page_count"],
        toc=toc,
    )

    # Read chapters
    chapters_dir = input_dir / "chapters"
    chapter_files = sorted(chapters_dir.glob("*.md"))
    chapters: list[Chapter] = []
    for ch_file in chapter_files:
        text = ch_file.read_text()
        front, body = _parse_frontmatter(text)
        chapters.append(
            Chapter(
                title=front.get("title", "Untitled"),
                content=body.strip(),
                images=tuple(front.get("images", [])),
                order=front.get("order", 0),
            )
        )

    # Check for images directory
    img_dir = input_dir / "images"
    image_dir = img_dir if img_dir.exists() else None

    return IntermediateBook(
        metadata=metadata,
        chapters=tuple(chapters),
        image_dir=image_dir,
    )


def _parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Parse YAML frontmatter from markdown text."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    front = yaml.safe_load(parts[1]) or {}
    return front, parts[2]


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text.lower()).strip("_")
