"""Book info page generation - creates a metadata/download page per book."""

from spina.models import BookMetadata, DownloadLink


def generate_book_info_page(
    metadata: BookMetadata,
    *,
    chapter_count: int,
    downloads: tuple[DownloadLink, ...] = (),
) -> str:
    """Generate markdown for a book's info page with metadata and download links."""
    lines = [
        f"# {metadata.title}",
        "",
        f"**Author:** {metadata.author}",
        f"**Pages:** {metadata.page_count}",
        f"**Chapters:** {chapter_count}",
        f"**Source:** {metadata.source_filename}",
        "",
    ]

    if downloads:
        lines.append("## Downloads")
        lines.append("")
        for link in downloads:
            lines.append(f"- [{link.label}]({link.filename})")
        lines.append("")

    return "\n".join(lines)
