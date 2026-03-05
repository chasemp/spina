"""MarkerEngine - PDF conversion using marker-pdf with lazy model loading."""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING

from spina.engines.base import ConversionResult

if TYPE_CHECKING:
    from marker.converters.pdf import PdfConverter


class MarkerEngine:
    def __init__(self, *, gpu: bool = False, force_ocr: bool = False) -> None:
        self._gpu = gpu
        self._force_ocr = force_ocr
        self._converter: PdfConverter | None = None

    def _ensure_converter(self) -> PdfConverter:
        if self._converter is not None:
            return self._converter

        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict

        device = None if self._gpu else "cpu"
        artifact_dict = create_model_dict(device=device)

        config: dict[str, object] = {}
        if not self._gpu:
            config["TORCH_DEVICE"] = "cpu"

        self._converter = PdfConverter(
            artifact_dict=artifact_dict,
            config=config,
        )
        return self._converter

    def convert(self, pdf_path: Path) -> ConversionResult:
        converter = self._ensure_converter()
        output = converter(str(pdf_path))

        images_bytes: dict[str, bytes] = {}
        for name, img in output.images.items():
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            images_bytes[name] = buf.getvalue()

        string_metadata = {
            k: str(v) for k, v in output.metadata.items() if isinstance(v, str)
        }

        return ConversionResult(
            markdown=output.markdown,
            images=images_bytes,
            metadata=string_metadata,
            page_count=converter.page_count,
        )
