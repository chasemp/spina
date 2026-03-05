"""Index page generation - creates a landing page listing all books."""

from spina.models import BookMetadata


def generate_index_page(
    books: list[BookMetadata],
    *,
    site_name: str,
) -> str:
    """Generate markdown for the index page listing all converted books."""
    lines = [f"# {site_name}", ""]

    if not books:
        lines.append("No books have been converted yet.")
        return "\n".join(lines)

    for book in books:
        lines.append(f"## {book.title}")
        lines.append("")
        if book.author:
            lines.append(f"**Author:** {book.author}")
            lines.append("")
        lines.append(f"**Pages:** {book.page_count}")
        lines.append(f"**Source:** {book.source_filename}")
        lines.append("")

    return "\n".join(lines)
