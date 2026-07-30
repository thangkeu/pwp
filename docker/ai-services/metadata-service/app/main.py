"""
PWP Metadata Engine Service (FastAPI) — Sprint 1.2, Giai đoạn 4 AI KEF.

Nhận văn bản đã parse (thường từ Parser Service, Sprint 1.1) và trả về metadata chuẩn hoá để
Gateway lưu vào cột riêng (`documents.customer`, `.vendor`...) và JSONB `extra_metadata`
(INSTRUCTIONS.md 6.4).
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.domain.extracted_metadata import ExtractedMetadata
from app.engine.metadata_engine import MetadataEngine

logger = logging.getLogger("pwp.metadata_service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="PWP Metadata Engine Service",
    version="0.1.0",
    description="Nhận diện Customer/Vendor/Model/Ngày/Version/Security Level/Document Type từ văn bản đã parse.",
)

engine = MetadataEngine()


class ExtractRequest(BaseModel):
    text: str = Field(..., description="Nội dung văn bản đã parse, thường là ParsedDocument.text")
    filename: str | None = Field(None, description="Tên file gốc, hỗ trợ DocumentTypeClassifier")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "pwp-metadata-service", "version": "0.1.0"}


@app.post("/metadata/extract", response_model=ExtractedMetadata)
async def extract_metadata(request: ExtractRequest) -> ExtractedMetadata:
    max_chars = settings.max_text_length_mb * 1024 * 1024
    if len(request.text) > max_chars:
        size_mb = len(request.text) / 1024 / 1024
        raise HTTPException(
            status_code=413,
            detail=f"Văn bản vượt giới hạn {settings.max_text_length_mb}MB (nhận {size_mb:.1f}MB)",
        )

    try:
        return engine.extract(request.text, request.filename)
    except Exception as exc:  # noqa: BLE001 - không nuốt lỗi im lặng, luôn log + trả lỗi rõ ràng
        logger.exception("Lỗi không lường trước khi trích xuất metadata")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ khi trích xuất metadata: {exc}") from exc


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):  # noqa: ANN001, ARG001
    logger.exception("Unhandled exception ở Metadata Service")
    return JSONResponse(status_code=500, content={"detail": "internal_server_error"})
