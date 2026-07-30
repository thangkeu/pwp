"""
CadAdapter — trích xuất từ file CAD.

Phạm vi có chủ đích (README_SPRINT1.1.md Mục 2):
  - .dxf: hỗ trợ THẬT qua ezdxf (định dạng mở, không cần binary ngoài).
  - .dwg: KHÔNG parse trực tiếp được — đây là định dạng nhị phân độc quyền của Autodesk,
    cần ODA File Converter (phần mềm ngoài, có giấy phép riêng) hoặc thư viện thương mại để đọc.
    Thay vì giả vờ hỗ trợ hoặc âm thầm trả kết quả rỗng, adapter đăng ký cho CẢ '.dwg' để trả
    lỗi RÕ RÀNG kèm hướng dẫn khắc phục cụ thể (convert sang DXF trước khi upload) — đúng
    nguyên tắc Fail Gracefully, giống cách xử lý DependencyUnavailableError cho Tesseract.
"""

from __future__ import annotations

import io

import ezdxf
from ezdxf.lldxf.const import DXFError

from app.adapters.base import DependencyUnavailableError, ParserAdapter, ParsingError
from app.domain.parsed_document import ParsedDocument, ParsedDocumentMetadata

_TEXT_ENTITY_TYPES = {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}

_DWG_GUIDANCE = (
    "File .dwg là định dạng nhị phân độc quyền của Autodesk, PWP Parser Service KHÔNG đọc "
    "trực tiếp được (cần ODA File Converter hoặc thư viện thương mại, chưa cài trong service "
    "này). Cách khắc phục: mở file trong AutoCAD/DraftSight/LibreCAD/QCAD, chọn 'Save As' → "
    "định dạng DXF (.dxf), rồi upload lại file .dxf đó. Hoặc dùng ODA File Converter miễn phí "
    "(https://www.opendesign.com/guestfiles/oda_file_converter) để convert hàng loạt."
)


class CadAdapter(ParserAdapter):
    @property
    def supported_extensions(self) -> list[str]:
        return ["dxf", "dwg"]

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext == "dwg":
            raise DependencyUnavailableError(_DWG_GUIDANCE)

        try:
            text_stream = io.StringIO(content.decode("utf-8", errors="replace"))
            document = ezdxf.read(text_stream)
        except (DXFError, UnicodeDecodeError, ValueError) as exc:
            raise ParsingError(f"File DXF không hợp lệ hoặc hỏng: {filename} ({exc})") from exc

        warnings: list[str] = []
        text_parts: list[str] = []
        layers_seen: set[str] = set()

        try:
            modelspace = document.modelspace()
            for entity in modelspace:
                layer = getattr(entity.dxf, "layer", None)
                if layer:
                    layers_seen.add(layer)

                dxftype = entity.dxftype()
                if dxftype == "TEXT":
                    text_parts.append(entity.dxf.text)
                elif dxftype == "MTEXT":
                    text_parts.append(entity.text)
                elif dxftype in ("ATTRIB", "ATTDEF"):
                    text_parts.append(entity.dxf.text)
        except Exception as exc:  # noqa: BLE001 - best-effort, không chặn phần đã đọc được
            warnings.append(f"Dừng sớm khi duyệt entity trong modelspace: {exc}")

        block_names = sorted({block.name for block in document.blocks if not block.name.startswith("*")})
        if block_names:
            text_parts.append("[Blocks] " + ", ".join(block_names))

        text = "\n".join(part for part in text_parts if part and part.strip())
        word_count = len(text.split())

        return ParsedDocument(
            text=text,
            metadata=ParsedDocumentMetadata(
                parser_name="CadAdapter",
                source_filename=filename,
                mime_type="image/vnd.dxf",
                word_count=word_count,
                warnings=warnings + ([f"Layers phát hiện: {', '.join(sorted(layers_seen))}"] if layers_seen else []),
            ),
        )
