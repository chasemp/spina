"""Tests for ConversionEngine protocol and ConversionResult."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from spina.engines.base import ConversionEngine, ConversionResult


class TestConversionResult:
    def test_creates_with_required_fields(self) -> None:
        result = ConversionResult(
            markdown="# Hello\n\nWorld",
            images={},
            metadata={"title": "Test"},
            page_count=5,
        )
        assert result.markdown == "# Hello\n\nWorld"
        assert result.images == {}
        assert result.metadata == {"title": "Test"}
        assert result.page_count == 5

    def test_is_frozen(self) -> None:
        result = ConversionResult(
            markdown="# Hello",
            images={},
            metadata={},
            page_count=1,
        )
        with pytest.raises(ValidationError):
            result.markdown = "changed"  # type: ignore[misc]

    def test_stores_images_mapping(self) -> None:
        result = ConversionResult(
            markdown="![img](img.png)",
            images={"img.png": b"\x89PNG"},
            metadata={},
            page_count=1,
        )
        assert result.images["img.png"] == b"\x89PNG"


class TestConversionEngineProtocol:
    def test_any_class_with_convert_method_satisfies_protocol(self) -> None:
        class FakeEngine:
            def convert(self, pdf_path: Path) -> ConversionResult:
                return ConversionResult(
                    markdown="fake",
                    images={},
                    metadata={},
                    page_count=1,
                )

        engine: ConversionEngine = FakeEngine()
        result = engine.convert(Path("test.pdf"))
        assert result.markdown == "fake"
