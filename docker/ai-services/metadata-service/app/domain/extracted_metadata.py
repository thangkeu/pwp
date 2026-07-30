"""
ExtractedMetadata — kết quả chuẩn hoá của Metadata Engine (Module 06, INSTRUCTIONS.md 6.4).

Ánh xạ đúng 2 nhóm metadata đã định nghĩa trong INSTRUCTIONS.md 6.4:
  - Structured (lưu cột riêng, dùng để filter/index): customer, project, vendors, models,
    security_level, document_type, industry.
  - Semi-structured (JSONB `extra_metadata`): mọi thứ còn lại (dates, versions, evidence chi
    tiết cho từng field) — nhóm vào `extra` để phía Gateway lưu thẳng vào cột JSONB mà không
    cần đổi schema mỗi khi Metadata Engine thêm 1 loại tín hiệu mới.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VendorModelMatch(BaseModel):
    """1 cặp (vendor, model) phát hiện được trong văn bản, kèm bằng chứng để người dùng kiểm chứng."""

    vendor: str
    model: str | None = Field(None, description="Model cụ thể nếu regex khớp được, None nếu chỉ nhận diện tên vendor")
    matched_text: str = Field(..., description="Đoạn text gốc khớp pattern — bằng chứng cho người review")


class SecurityLevelResult(BaseModel):
    level: str = Field(
        ..., description="'public' | 'internal' | 'confidential' — mặc định 'internal' nếu không có tín hiệu rõ ràng"
    )
    matched_keywords: list[str] = Field(default_factory=list)


class ExtractedMetadata(BaseModel):
    # --- Structured fields (INSTRUCTIONS.md 6.4) ---
    customers: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    vendor_models: list[VendorModelMatch] = Field(default_factory=list)
    security_level: SecurityLevelResult
    document_type: str | None = Field(None, description="vd: 'proposal', 'bom', 'meeting_minutes', 'contract'")
    industries: list[str] = Field(default_factory=list)

    # --- Semi-structured (-> extra_metadata JSONB phía Gateway) ---
    dates_found: list[str] = Field(default_factory=list)
    versions_found: list[str] = Field(default_factory=list)

    # --- Metadata về chính lần chạy Metadata Engine (để debug/audit) ---
    engine_version: str = "0.1.0"
    warnings: list[str] = Field(default_factory=list)
