"""
PWP Document Parser Service (FastAPI) — Sprint 1.1, Giai đoạn 4 AI KEF.

Theo ADR-001: service AI/ML nặng viết bằng Python/FastAPI, chạy độc lập trong Docker,
Gateway (Node.js) gọi sang qua REST nội bộ, KHÔNG chứa logic parse trong Gateway.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.adapters.base import DependencyUnavailableError, ParsingError, UnsupportedFileTypeError
from app.config import settings
from app.domain.parsed_document import ParsedDocument
from app.registry import default_registry

logger = logging.getLogger("pwp.parser_service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="PWP Document Parser Service",
    version="0.1.0",
    description="Chuẩn hoá mọi định dạng tài liệu thành ParsedDocument cho Metadata/Embedding Engine.",
)

registry = default_registry()


@app.get("/health")
async def health() -> dict:
    """Đúng chuẩn health check như Gateway (INSTRUCTIONS.md 8.7)."""
    return {"status": "ok", "service": "pwp-parser-service", "version": "0.1.0"}


@app.get("/parsers")
async def list_parsers() -> dict:
    """Liệt kê extension đang được hỗ trợ — hữu ích cho Document Manager kiểm tra trước khi gửi file."""
    return {"supported_extensions": registry.supported_extensions()}


@app.post("/parse", response_model=ParsedDocument)
async def parse_document(file: UploadFile = File(...)) -> ParsedDocument:
    """
    Nhận 1 file, trả về ParsedDocument chuẩn hoá.

    Fail gracefully (INSTRUCTIONS.md Nguyên tắc 8): mọi lỗi trả HTTPException với message rõ
    ràng và mã lỗi phù hợp, không bao giờ trả 200 với dữ liệu rỗng giả vờ thành công.
    """
    content = await file.read()

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File vượt giới hạn {settings.max_upload_mb}MB (nhận {len(content) / 1024 / 1024:.1f}MB)",
        )

    try:
        adapter = registry.resolve(file.filename or "")
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    try:
        result = adapter.parse(content, file.filename or "unknown")
    except DependencyUnavailableError as exc:
        logger.error("Thiếu dependency hạ tầng khi parse %s: %s", file.filename, exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ParsingError as exc:
        logger.error("Parsing thất bại cho %s: %s", file.filename, exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Lỗi không lường trước khi parse %s", file.filename)
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ khi parse file: {exc}") from exc

    return result


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.exception("Unhandled exception ở Parser Service")
    return JSONResponse(status_code=500, content={"detail": "internal_server_error"})
