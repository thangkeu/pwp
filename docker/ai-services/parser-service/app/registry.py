"""
ParserRegistry — nơi duy nhất tra cứu "extension nào dùng adapter nào".

Thêm định dạng mới (vd: Draw.io/Visio/CAD ở Sprint sau) = viết 1 adapter mới implement
ParserAdapter, rồi thêm 1 dòng `registry.register(NewAdapter())` trong `default_registry()`
— không sửa main.py hay adapter khác (Open/Closed Principle).
"""

from __future__ import annotations

from app.adapters.base import ParserAdapter, UnsupportedFileTypeError


class ParserRegistry:
    def __init__(self) -> None:
        self._by_extension: dict[str, ParserAdapter] = {}

    def register(self, adapter: ParserAdapter) -> None:
        """
        @raises ValueError: nếu 1 extension đã có adapter khác đăng ký (chống ghi đè âm thầm,
            giống `registerService()` bên Gateway Node.js).
        """
        for ext in adapter.supported_extensions:
            ext = ext.lower()
            if ext in self._by_extension:
                raise ValueError(
                    f"Extension '.{ext}' đã được đăng ký bởi {type(self._by_extension[ext]).__name__}, "
                    f"không thể đăng ký lại bởi {type(adapter).__name__}"
                )
            self._by_extension[ext] = adapter

    def resolve(self, filename: str) -> ParserAdapter:
        """
        @raises UnsupportedFileTypeError: khi không có adapter nào xử lý được extension này.
        """
        if "." not in filename:
            raise UnsupportedFileTypeError(f"Không xác định được extension từ tên file: {filename}")
        ext = filename.rsplit(".", 1)[-1].lower()
        adapter = self._by_extension.get(ext)
        if adapter is None:
            raise UnsupportedFileTypeError(
                f"Không có adapter nào hỗ trợ '.{ext}'. Định dạng hỗ trợ: {self.supported_extensions()}"
            )
        return adapter

    def supported_extensions(self) -> list[str]:
        return sorted(self._by_extension.keys())


def default_registry() -> ParserRegistry:
    """Registry mặc định — 6 định dạng Sprint 1.1 + CAD/Visio/Draw.io ở Sprint 1.1b."""
    from app.adapters.cad_adapter import CadAdapter
    from app.adapters.docx_adapter import DocxAdapter
    from app.adapters.drawio_adapter import DrawioAdapter
    from app.adapters.image_ocr_adapter import ImageOcrAdapter
    from app.adapters.pdf_adapter import PdfAdapter
    from app.adapters.pptx_adapter import PptxAdapter
    from app.adapters.text_adapter import TextAdapter
    from app.adapters.visio_adapter import VisioAdapter
    from app.adapters.xlsx_adapter import XlsxAdapter
    from app.config import settings

    registry = ParserRegistry()
    registry.register(TextAdapter())
    registry.register(DocxAdapter())
    registry.register(XlsxAdapter())
    registry.register(PptxAdapter())
    registry.register(PdfAdapter())
    registry.register(
        ImageOcrAdapter(
            ocr_languages=settings.ocr_languages,
            tesseract_cmd=settings.tesseract_cmd or None,
        )
    )
    registry.register(CadAdapter())
    registry.register(VisioAdapter())
    registry.register(DrawioAdapter())
    return registry
