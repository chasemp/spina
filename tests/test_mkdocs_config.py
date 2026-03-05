"""Tests for MkDocs configuration generation."""

import yaml

from spina.site.mkdocs_config import generate_mkdocs_config
from tests.conftest import make_chapter, make_intermediate_book, make_metadata


class TestGenerateMkdocsConfig:
    def test_generates_valid_yaml(self) -> None:
        book = make_intermediate_book(
            metadata=make_metadata(title="Test Book"),
        )

        config = generate_mkdocs_config(book, site_name="My Library")

        parsed = yaml.safe_load(config)
        assert isinstance(parsed, dict)

    def test_sets_site_name(self) -> None:
        book = make_intermediate_book()

        config = generate_mkdocs_config(book, site_name="My Library")

        parsed = yaml.safe_load(config)
        assert parsed["site_name"] == "My Library"

    def test_uses_material_theme(self) -> None:
        book = make_intermediate_book()

        config = generate_mkdocs_config(book, site_name="Test")

        parsed = yaml.safe_load(config)
        assert parsed["theme"]["name"] == "material"

    def test_includes_nav_with_chapters(self) -> None:
        chapters = (
            make_chapter(title="Intro", content="text", order=0),
            make_chapter(title="Main", content="text", order=1),
        )
        book = make_intermediate_book(chapters=chapters)

        config = generate_mkdocs_config(book, site_name="Test")

        parsed = yaml.safe_load(config)
        assert "nav" in parsed
        nav = parsed["nav"]
        assert len(nav) >= 2

    def test_returns_string(self) -> None:
        book = make_intermediate_book()
        config = generate_mkdocs_config(book, site_name="Test")
        assert isinstance(config, str)

    def test_enables_footer_navigation(self) -> None:
        book = make_intermediate_book()

        config = generate_mkdocs_config(book, site_name="Test")

        parsed = yaml.safe_load(config)
        features = parsed["theme"]["features"]
        assert "navigation.footer" in features

    def test_nav_includes_about_when_has_info_pages(self) -> None:
        book = make_intermediate_book(
            metadata=make_metadata(title="My Book"),
        )

        config = generate_mkdocs_config(book, site_name="Test", has_info_pages=True)

        parsed = yaml.safe_load(config)
        nav = parsed["nav"]
        assert nav[1] == {"About": "my_book/info.md"}

    def test_nav_excludes_about_by_default(self) -> None:
        book = make_intermediate_book(
            metadata=make_metadata(title="My Book"),
        )

        config = generate_mkdocs_config(book, site_name="Test")

        parsed = yaml.safe_load(config)
        nav = parsed["nav"]
        assert not any("About" in entry for entry in nav)

    def test_includes_arithmatex_extension(self) -> None:
        book = make_intermediate_book()

        config = generate_mkdocs_config(book, site_name="Test")

        parsed = yaml.safe_load(config)
        extensions = parsed.get("markdown_extensions", [])
        arithmatex = next(
            (e for e in extensions if isinstance(e, dict) and "pymdownx.arithmatex" in e),
            None,
        )
        assert arithmatex is not None
        assert arithmatex["pymdownx.arithmatex"]["generic"] is True

    def test_includes_mathjax_extra_javascript(self) -> None:
        book = make_intermediate_book()

        config = generate_mkdocs_config(book, site_name="Test")

        parsed = yaml.safe_load(config)
        extra_js = parsed.get("extra_javascript", [])
        assert any("mathjax" in str(entry).lower() for entry in extra_js)

    def test_uses_sidebar_navigation_not_tabs(self) -> None:
        book = make_intermediate_book()

        config = generate_mkdocs_config(book, site_name="Test")

        parsed = yaml.safe_load(config)
        features = parsed["theme"]["features"]
        assert "navigation.tabs" not in features
        assert "navigation.expand" not in features
        assert "navigation.sections" not in features
