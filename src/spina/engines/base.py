"""ConversionEngine protocol and ConversionResult model."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class ConversionResult(BaseModel, frozen=True):
    markdown: str
    images: dict[str, bytes]
    metadata: dict[str, str]
    page_count: int


@runtime_checkable
class ConversionEngine(Protocol):
    def convert(self, pdf_path: Path) -> ConversionResult: ...
