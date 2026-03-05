"""MkDocs configuration generation - produces mkdocs.yml content."""

import yaml

from spina.models import IntermediateBook
from spina.intermediate import _slugify


def generate_mkdocs_config(
    book: IntermediateBook,
    *,
    site_name: str,
    has_info_pages: bool = False,
) -> str:
    """Generate mkdocs.yml content for a book site."""
    nav: list[dict[str, str]] = [{"Home": "index.md"}]
    book_slug = _slugify(book.metadata.title)

    if has_info_pages:
        nav.append({"About": f"{book_slug}/info.md"})

    for chapter in sorted(book.chapters, key=lambda c: c.order):
        chapter_file = f"{book_slug}/{chapter.order:03d}_{_slugify(chapter.title)}.md"
        nav.append({chapter.title: chapter_file})

    config = {
        "site_name": site_name,
        "theme": {
            "name": "material",
            "custom_dir": "overrides",
            "features": [
                "navigation.instant",
                "navigation.footer",
                "search.suggest",
                "search.highlight",
            ],
        },
        "nav": nav,
        "markdown_extensions": [
            {"pymdownx.arithmatex": {"generic": True}},
        ],
        "extra_javascript": [
            {"https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js": {"async": True}},
        ],
    }

    return yaml.dump(config, default_flow_style=False, sort_keys=False)
