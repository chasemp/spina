"""Post-processing - fixes OCR artifacts in converted markdown."""

import re

_HEADING_RE = re.compile(r"^#{1,4}\s+(.+)$", re.MULTILINE)
_TABLE_CELL_RE = re.compile(r"\|\s*([^|]+?)\s*\|")


def repair_drop_caps(markdown: str) -> str:
    """Repair drop-cap OCR artifacts in table cells by cross-referencing headings.

    Decorative drop caps in scanned books are often missed by OCR, resulting in
    table-of-contents entries like "ppendix D" instead of "Appendix D". This
    function finds all headings in the document and fixes truncated matches in
    table cells.
    """
    headings = _HEADING_RE.findall(markdown)
    if not headings:
        return markdown

    # Build lookup: truncated_lowercase -> original_title_case heading
    # For each heading, create the "drop-cap truncated" variant (first char removed)
    truncated_to_full: dict[str, str] = {}
    for heading in headings:
        heading = heading.strip().strip("*")  # Remove bold markers
        if len(heading) < 2:
            continue
        # The truncated version: remove first char, lowercase for matching
        truncated_key = heading[1:].lower()
        # Store the title-cased version for replacement
        truncated_to_full[truncated_key] = heading

    if not truncated_to_full:
        return markdown

    def _fix_table_row(line: str) -> str:
        if "|" not in line:
            return line
        # Only process table data rows (not separator rows like |---|---|)
        if re.match(r"^\s*\|[\s\-:|]+\|\s*$", line):
            return line

        def replace_cell(match: re.Match[str]) -> str:
            cell_text = match.group(1).strip()
            if not cell_text:
                return match.group(0)
            cell_lower = cell_text.lower()
            if cell_lower in truncated_to_full:
                full_heading = truncated_to_full[cell_lower]
                # Use title case from the heading
                return match.group(0).replace(cell_text, _to_title_case(full_heading))
            return match.group(0)

        return _TABLE_CELL_RE.sub(replace_cell, line)

    lines = markdown.split("\n")
    result = "\n".join(_fix_table_row(line) for line in lines)
    return result


def _to_title_case(heading: str) -> str:
    """Convert a heading to title case, handling ALL CAPS headings."""
    if heading.isupper():
        return heading.title()
    return heading
