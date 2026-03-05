"""Configuration for spina. Frozen Pydantic model with sensible defaults."""

from pydantic import BaseModel, Field


class SpinaConfig(BaseModel, frozen=True):
    force_ocr: bool = False
    gpu: bool = False
    page_threshold: int = Field(default=30, gt=0)
    generate_epub: bool = True
    generate_clean_pdf: bool = False
    site_name: str = Field(default="spina", min_length=1)
