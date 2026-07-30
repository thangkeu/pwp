"""DateExtractor — nhận diện chuỗi ngày tháng phổ biến trong tài liệu presales tiếng Việt/Anh."""

from __future__ import annotations

import re

_PATTERNS = [
    # 12/07/2026, 12-07-2026, 12.07.2026
    r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4}\b",
    # 2026-07-12 (ISO)
    r"\b\d{4}-\d{1,2}-\d{1,2}\b",
    # "ngày 12 tháng 7 năm 2026"
    r"\bngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}\b",
    # "12 July 2026", "July 12, 2026"
    r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _PATTERNS]


class DateExtractor:
    def extract(self, text: str) -> list[str]:
        """@returns: danh sách chuỗi ngày phát hiện được, giữ nguyên định dạng gốc, không trùng lặp."""
        found: list[str] = []
        seen: set[str] = set()
        for pattern in _COMPILED:
            for m in pattern.finditer(text):
                value = m.group(0).strip()
                key = value.lower()
                if key not in seen:
                    seen.add(key)
                    found.append(value)
        return found
