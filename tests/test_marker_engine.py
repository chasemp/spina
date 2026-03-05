"""Tests for MarkerEngine - wraps marker-pdf for PDF conversion."""

from pathlib import Path
from typing import NamedTuple
from unittest.mock import MagicMock

import pytest
from PIL import Image

from spina.engines.base import ConversionResult
from spina.engines.marker_engine import MarkerEngine


class FakeMarkerOutput(NamedTuple):
    markdown: str
    images: dict[str, Image.Image]
    metadata: dict[str, object]


def _make_test_image() -> Image.Image:
    return Image.new("RGB", (10, 10), color="red")


def _make_engine_with_mock(
    fake_output: FakeMarkerOutput,
    page_count: int = 1,
) -> MarkerEngine:
    """Create a MarkerEngine with a pre-injected mock converter."""
    engine = MarkerEngine(gpu=False)
    mock_converter = MagicMock(return_value=fake_output)
    mock_converter.page_count = page_count
    engine._converter = mock_converter
    return engine


class TestMarkerEngine:
    def test_convert_returns_conversion_result(self) -> None:
        engine = _make_engine_with_mock(
            FakeMarkerOutput(
                markdown="# Test\n\nHello world",
                images={"img.png": _make_test_image()},
                metadata={"title": "Test Doc"},
            ),
            page_count=5,
        )

        result = engine.convert(Path("test.pdf"))

        assert isinstance(result, ConversionResult)
        assert result.markdown == "# Test\n\nHello world"
        assert result.page_count == 5

    def test_convert_serializes_images_to_bytes(self) -> None:
        engine = _make_engine_with_mock(
            FakeMarkerOutput(
                markdown="# Test",
                images={"fig1.png": _make_test_image()},
                metadata={},
            ),
        )

        result = engine.convert(Path("test.pdf"))

        assert "fig1.png" in result.images
        assert isinstance(result.images["fig1.png"], bytes)
        assert len(result.images["fig1.png"]) > 0

    def test_convert_handles_empty_images(self) -> None:
        engine = _make_engine_with_mock(
            FakeMarkerOutput(markdown="# No images", images={}, metadata={}),
            page_count=2,
        )

        result = engine.convert(Path("test.pdf"))

        assert result.images == {}

    def test_convert_extracts_string_metadata(self) -> None:
        engine = _make_engine_with_mock(
            FakeMarkerOutput(
                markdown="# Test",
                images={},
                metadata={"title": "My Book", "author": "Author", "pages": 42},
            ),
            page_count=42,
        )

        result = engine.convert(Path("test.pdf"))

        assert result.metadata["title"] == "My Book"
        assert result.metadata["author"] == "Author"
        assert "pages" not in result.metadata

    def test_converter_called_with_string_path(self) -> None:
        engine = _make_engine_with_mock(
            FakeMarkerOutput(markdown="test", images={}, metadata={}),
        )

        engine.convert(Path("some/path.pdf"))

        engine._converter.assert_called_once_with("some/path.pdf")  # type: ignore[union-attr]

    def test_lazy_initialization_does_not_create_converter_on_init(self) -> None:
        engine = MarkerEngine(gpu=False)
        assert engine._converter is None

    @pytest.mark.slow
    def test_real_conversion_on_sample_pdf(self) -> None:
        sample = Path("samples/2026-82154-001.pdf")
        if not sample.exists():
            pytest.skip("Sample PDF not available")

        engine = MarkerEngine(gpu=False)
        result = engine.convert(sample)

        assert len(result.markdown) > 100
        assert result.page_count > 0
