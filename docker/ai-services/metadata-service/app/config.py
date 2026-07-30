"""Cấu hình Metadata Service — đọc từ biến môi trường (Config-driven)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_text_length_mb: int = int(os.environ.get("METADATA_MAX_TEXT_LENGTH_MB", "5"))


settings = Settings()
