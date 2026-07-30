"""Cấu hình Parser Service — đọc từ biến môi trường (Nguyên tắc 3 Config-driven, không hard-code)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ocr_languages: str = os.environ.get("PARSER_OCR_LANGUAGES", "eng+vie")
    max_upload_mb: int = int(os.environ.get("PARSER_MAX_UPLOAD_MB", "50"))
    gateway_api_key: str = os.environ.get("GATEWAY_API_KEY", "")
    # Đường dẫn tới tesseract.exe/tesseract binary — bắt buộc trên Windows nếu tesseract không
    # tự nằm trong PATH sau khi cài (mặc định trình cài đặt UB-Mannheim không tự thêm vào PATH).
    # Để trống (mặc định) nếu chạy trong Docker image (đã cài qua apt, tự có trong PATH) hoặc
    # trên Linux/macOS đã cài qua apt/brew.
    tesseract_cmd: str = os.environ.get("PARSER_TESSERACT_CMD", "")


settings = Settings()
