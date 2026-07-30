"""VisioAdapter — trích xuất từ file .vsdx dùng thư viện `vsdx`."""

from __future__ import annotations

import os
import tempfile
import zipfile

import vsdx

from app.adapters.base import ParserAdapter, ParsingError
from app.domain.parsed_document import ParsedDocument, ParsedDocumentMetadata


class VisioAdapter(ParserAdapter):
    """
    Thư viện `vsdx` chỉ nhận đường dẫn file thật (dùng zipfile nội bộ theo path, không nhận
    BytesIO trực tiếp) — adapter phải ghi tạm ra file, đọc, rồi dọn dẹp ngay trong `finally`
    để không rò rỉ file tạm dù parse thành công hay thất bại.
    """

    @property
    def supported_extensions(self) -> list[str]:
        return ["vsdx"]

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".vsdx", delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            text_parts: list[str] = []
            page_count = 0
            warnings: list[str] = []

            with vsdx.VisioFile(tmp_path) as visio_file:
                for page in visio_file.pages:
                    page_count += 1
                    shape_texts = []
                    try:
                        for shape in page.all_shapes:
                            shape_text = (shape.text or "").strip()
                            if shape_text:
                                shape_texts.append(shape_text)
                    except Exception as exc:  # noqa: BLE001 - best-effort theo từng page
                        warnings.append(f"Page '{page.name}': lỗi khi đọc shape ({exc})")

                    if shape_texts:
                        text_parts.append(f"[Page: {page.name}]\n" + "\n".join(shape_texts))

            text = "\n\n".join(text_parts)
            word_count = len(text.split())

            return ParsedDocument(
                text=text,
                metadata=ParsedDocumentMetadata(
                    parser_name="VisioAdapter",
                    source_filename=filename,
                    mime_type="application/vnd.ms-visio.drawing.main+xml",
                    page_count=page_count,
                    word_count=word_count,
                    warnings=warnings,
                ),
            )
        except zipfile.BadZipFile as exc:
            raise ParsingError(f"File VSDX không hợp lệ hoặc hỏng: {filename} ({exc})") from exc
        except (KeyError, AttributeError) as exc:
            # vsdx ném KeyError/AttributeError khi cấu trúc XML nội bộ không đúng schema Visio
            # (vd: file .vsdx đổi tên từ định dạng khác) — coi là file hỏng, không phải bug adapter.
            raise ParsingError(f"Cấu trúc file VSDX không hợp lệ: {filename} ({exc})") from exc
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
