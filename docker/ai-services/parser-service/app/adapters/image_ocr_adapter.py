"""ImageOcrAdapter — OCR ảnh scan thành text, dùng pytesseract + Pillow."""

from __future__ import annotations

import base64
import io

import pytesseract
from PIL import Image, UnidentifiedImageError

from app.adapters.base import DependencyUnavailableError, ParserAdapter, ParsingError
from app.domain.parsed_document import (
    ParsedDocument,
    ParsedDocumentMetadata,
    ParsedImage,
)


class ImageOcrAdapter(ParserAdapter):
    """
    OCR cho tài liệu scan (FR-KB-01 "ảnh có chữ qua OCR").
    Ngôn ngữ OCR mặc định 'eng+vie' — cấu hình được qua tham số constructor, KHÔNG hard-code
    cứng nếu Sprint sau cần thêm ngôn ngữ khác (Nguyên tắc 3 Config-driven).
    """

    def __init__(self, ocr_languages: str = "eng+vie", tesseract_cmd: str | None = None):
        self._ocr_languages = ocr_languages
        if tesseract_cmd:
            # Trên Windows, tesseract.exe thường KHÔNG tự có trong PATH sau khi cài đặt —
            # cho phép trỏ thẳng đường dẫn qua biến môi trường PARSER_TESSERACT_CMD thay vì
            # bắt buộc người dùng tự sửa PATH hệ thống (xem README Mục 14 "Lưu ý Windows").
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    @property
    def supported_extensions(self) -> list[str]:
        return ["png", "jpg", "jpeg", "tiff", "bmp"]

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            image = Image.open(io.BytesIO(content))
            image.load()
        except UnidentifiedImageError as exc:
            raise ParsingError(f"File ảnh không hợp lệ hoặc hỏng: {filename} ({exc})") from exc

        warnings: list[str] = []
        try:
            text = pytesseract.image_to_string(image, lang=self._ocr_languages).strip()
        except pytesseract.TesseractNotFoundError as exc:
            # Lỗi hạ tầng (thiếu binary tesseract trên máy), KHÔNG phải lỗi nội dung file —
            # ném DependencyUnavailableError để endpoint /parse trả 503 kèm hướng dẫn khắc phục,
            # thay vì để traceback khó hiểu lộ ra ngoài (Fail gracefully, không im lặng).
            raise DependencyUnavailableError(
                "Không tìm thấy chương trình 'tesseract' trên hệ thống. Cần cài Tesseract OCR "
                "và đảm bảo nó nằm trong PATH, hoặc đặt biến môi trường PARSER_TESSERACT_CMD "
                "trỏ thẳng tới file thực thi (vd trên Windows: "
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                "). Xem README_SPRINT1.1.md mục 14 - Lưu ý Windows."
            ) from exc
        except pytesseract.TesseractError as exc:
            # Fail gracefully: OCR lỗi không có nghĩa cả file vô dụng — trả về text rỗng kèm warning
            # thay vì raise ParsingError, vì ảnh vẫn được lưu lại (content_base64) để xem thủ công.
            text = ""
            warnings.append(f"OCR thất bại: {exc}")

        word_count = len(text.split())

        return ParsedDocument(
            text=text,
            images=[
                ParsedImage(
                    index=0,
                    width=image.width,
                    height=image.height,
                    content_base64=base64.b64encode(content).decode("ascii"),
                    ocr_text=text or None,
                )
            ],
            metadata=ParsedDocumentMetadata(
                parser_name="ImageOcrAdapter",
                source_filename=filename,
                mime_type=Image.MIME.get(image.format, "image/unknown"),
                word_count=word_count,
                warnings=warnings,
            ),
        )
