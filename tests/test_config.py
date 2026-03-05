"""Tests for SpinaConfig - frozen Pydantic configuration with sensible defaults."""

import pytest
from pydantic import ValidationError

from spina.config import SpinaConfig


class TestSpinaConfig:
    def test_creates_with_defaults(self) -> None:
        config = SpinaConfig()
        assert config.force_ocr is False
        assert config.gpu is False
        assert config.page_threshold == 30
        assert config.generate_epub is True
        assert config.generate_clean_pdf is False
        assert config.site_name == "spina"

    def test_is_frozen(self) -> None:
        config = SpinaConfig()
        with pytest.raises(ValidationError):
            config.force_ocr = True  # type: ignore[misc]

    def test_overrides_defaults(self) -> None:
        config = SpinaConfig(
            force_ocr=True,
            gpu=True,
            page_threshold=50,
            generate_epub=False,
            site_name="My Library",
        )
        assert config.force_ocr is True
        assert config.gpu is True
        assert config.page_threshold == 50
        assert config.generate_epub is False
        assert config.site_name == "My Library"

    def test_rejects_page_threshold_below_one(self) -> None:
        with pytest.raises(ValidationError):
            SpinaConfig(page_threshold=0)

    def test_rejects_empty_site_name(self) -> None:
        with pytest.raises(ValidationError):
            SpinaConfig(site_name="")
