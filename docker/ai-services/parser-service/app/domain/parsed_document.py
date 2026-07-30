"""
ParsedDocument — cấu trúc đầu ra CHUẨN mà MỌI ParserAdapter phải trả về.

Đây là "hợp đồng" tương đương AIProviderAdapter ở Gateway (Node.js): bất kể adapter nào
(PDF/DOCX/XLSX/PPTX/...) xử lý, Metadata Engine và Embedding Engine ở Sprint sau chỉ cần biết
đúng 1 cấu trúc này — không cần biết định dạng file gốc là gì (Interface Segregation + Liskov
Substitution, INSTRUCTIONS.md Phần IV.2).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ParsedTable(BaseModel):
    """1 bảng biểu trích xuất được từ tài liệu."""

    rows: list[list[str]] = Field(..., description="Dữ liệu bảng dạng ma trận chuỗi, hàng đầu thường là header")
    caption: str | None = Field(None, description="Chú thích bảng nếu phát hiện được")
    page_number: int | None = Field(
        None, description="Trang chứa bảng (1-indexed), None nếu định dạng không phân trang"
    )


class ParsedImage(BaseModel):
    """1 hình ảnh trích xuất được từ tài liệu."""

    index: int = Field(..., description="Thứ tự hình ảnh trong tài liệu, bắt đầu từ 0")
    caption: str | None = Field(None, description="Chú thích/alt-text nếu có")
    page_number: int | None = Field(None, description="Trang chứa hình (1-indexed)")
    width: int | None = None
    height: int | None = None
    content_base64: str | None = Field(
        None,
        description=(
            "Nội dung ảnh gốc mã hoá base64, để Sprint sau (Embedding/OCR) "
            "dùng lại mà không phải mở lại file gốc"
        ),
    )
    ocr_text: str | None = Field(None, description="Văn bản OCR trích xuất từ ảnh này, nếu adapter có bật OCR")


class ParsedDocumentMetadata(BaseModel):
    """Thông tin phụ trợ về quá trình parse, phục vụ debug và Knowledge Governance."""

    parser_name: str
    parser_version: str = "0.1.0"
    source_filename: str
    mime_type: str | None = None
    page_count: int | None = None
    word_count: int = 0
    warnings: list[str] = Field(
        default_factory=list,
        description="Cảnh báo không chặn (vd: 1 trang OCR lỗi nhưng các trang khác vẫn parse được)",
    )


class ParsedDocument(BaseModel):
    """
    Kết quả chuẩn hoá của 1 lần parse tài liệu — tương ứng output mong đợi ở
    AI Knowledge Engineering Framework.docx mục "Document Parser" và
    INSTRUCTIONS.md FR-KB-01: "Trích xuất Tables, Images, Captions, Headers, Footers, Links,
    References, Revision History, Comments".
    """

    text: str = Field(..., description="Toàn bộ văn bản thuần trích xuất được, đã loại bỏ markup")
    tables: list[ParsedTable] = Field(default_factory=list)
    images: list[ParsedImage] = Field(default_factory=list)
    headers: list[str] = Field(default_factory=list, description="Header lặp lại theo trang/section")
    footers: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list, description="Hyperlink phát hiện được trong nội dung")
    references: list[str] = Field(
        default_factory=list, description="Trích dẫn/tham chiếu nếu định dạng hỗ trợ (vd: footnote)"
    )
    comments: list[str] = Field(
        default_factory=list, description="Comment/annotation của tài liệu, nếu định dạng hỗ trợ"
    )
    revision_history: list[str] = Field(
        default_factory=list, description="Lịch sử chỉnh sửa nếu định dạng lưu lại (vd: DOCX track changes)"
    )
    metadata: ParsedDocumentMetadata

    def content_hash_input(self) -> str:
        """
        Chuỗi dùng để tính content_hash (INSTRUCTIONS.md FR-DOC-04 cảnh báo tài liệu trùng lặp).
        Chỉ dựa vào `text` — cố ý bỏ qua metadata (filename, thời điểm parse) vì 2 file cùng
        nội dung nhưng khác tên/nguồn vẫn phải được coi là trùng lặp.
        """
        return self.text
