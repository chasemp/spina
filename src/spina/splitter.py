"""Chapter splitting - pure function that splits markdown into chapters."""

import re

from spina.models import Chapter

_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_H1_RE = re.compile(r"^# (.+)$", re.MULTILINE)
_H2_RE = re.compile(r"^## (.+)$", re.MULTILINE)


def _extract_images(content: str) -> tuple[str, ...]:
    return tuple(_IMAGE_RE.findall(content))


def _split_on_pattern(
    markdown: str,
    pattern: re.Pattern[str],
) -> list[tuple[str, str]]:
    """Split markdown on heading pattern, returning (title, content) pairs."""
    matches = list(pattern.finditer(markdown))
    if not matches:
        return []

    sections: list[tuple[str, str]] = []

    # Content before first heading
    preamble = markdown[: matches[0].start()].strip()
    if preamble:
        sections.append(("Preamble", preamble))

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        content = markdown[start:end].strip()
        sections.append((title, content))

    return sections


_DEFAULT_MAX_CHAPTER_CHARS = 10_000


def _subsplit_large_sections(
    sections: list[tuple[str, str]],
    max_chars: int,
) -> list[tuple[str, str]]:
    """Sub-split sections that are too large and contain H2 headings."""
    result: list[tuple[str, str]] = []
    for title, content in sections:
        if len(content) > max_chars:
            sub_sections = _split_on_pattern(content, _H2_RE)
            if sub_sections:
                result.extend(sub_sections)
                continue
        result.append((title, content))
    return result


def split_chapters(
    markdown: str,
    *,
    page_count: int,
    page_threshold: int,
    max_chapter_chars: int = _DEFAULT_MAX_CHAPTER_CHARS,
) -> tuple[Chapter, ...]:
    """Split markdown into chapters. Short docs stay as one chapter."""
    if page_count < page_threshold:
        # Short document: single chapter
        title = "Untitled"
        content = markdown
        h1_match = _H1_RE.search(markdown)
        if h1_match:
            title = h1_match.group(1).strip()
            content = markdown[h1_match.end() :].strip()
        return (
            Chapter(
                title=title,
                content=content,
                images=_extract_images(content),
                order=0,
            ),
        )

    # Try H1 first, then H2
    sections = _split_on_pattern(markdown, _H1_RE)
    if not sections:
        sections = _split_on_pattern(markdown, _H2_RE)

    if not sections:
        return (
            Chapter(
                title="Untitled",
                content=markdown.strip(),
                images=_extract_images(markdown),
                order=0,
            ),
        )

    # Sub-split large chapters that contain H2 sub-headings
    sections = _subsplit_large_sections(sections, max_chapter_chars)

    return tuple(
        Chapter(
            title=title,
            content=content,
            images=_extract_images(content),
            order=i,
        )
        for i, (title, content) in enumerate(sections)
    )
