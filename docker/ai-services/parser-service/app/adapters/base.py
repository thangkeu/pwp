"""
ParserAdapter — interface trừu tượng mà MỌI adapter định dạng file phải implement.

Tuân thủ Nguyên tắc 2 (Plugin Architecture, INSTRUCTIONS.md 2.7 mục 5 áp dụng tương tự cho
Parser): thêm định dạng file mới = viết 1 class mới kế thừa ParserAdapter, đăng ký vào
ParserRegistry — không sửa main.py hay adapter khác.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.parsed_document import ParsedDocument


class UnsupportedFileTypeError(Exception):
    """Ném ra khi không có adapter nào đăng ký cho extension/mime_type yêu cầu."""


class ParsingError(Exception):
    """
    Ném ra khi adapter tìm thấy nhưng parse thất bại (file hỏng, mã hoá lạ...).
    Không bao giờ nuốt lỗi im lặng (Fail gracefully — INSTRUCTIONS.md Nguyên tắc 8):
    endpoint /parse phải trả lỗi rõ ràng, không trả ParsedDocument rỗng giả vờ thành công.
    """


class DependencyUnavailableError(Exception):
    """
    Ném ra khi adapter cần 1 dependency NGOÀI Python (vd: binary `tesseract` của hệ điều hành)
    nhưng dependency đó chưa được cài đặt/cấu hình đúng trên máy đang chạy service.

    Khác với ParsingError: đây KHÔNG phải lỗi do nội dung file (file vẫn có thể hoàn toàn hợp
    lệ) — đây là lỗi môi trường/hạ tầng. Endpoint /parse trả mã lỗi khác (503) cho trường hợp
    này để người vận hành phân biệt được "cần sửa file" hay "cần cài thêm phần mềm trên server".
    """


class ParserAdapter(ABC):
    """Interface chuẩn — mọi adapter cụ thể (PdfAdapter, DocxAdapter...) implement 2 hàm này."""

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Danh sách extension (không dấu chấm, chữ thường) adapter này xử lý được, vd: ['pdf']."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        """
        Parse nội dung file thành ParsedDocument chuẩn hoá.

        @param content: nội dung file dạng byte thô
        @param filename: tên file gốc (dùng để điền metadata, KHÔNG dùng để quyết định logic parse)
        @raises ParsingError: khi nội dung không parse được (file hỏng, định dạng không khớp thật)
        """
        raise NotImplementedError
