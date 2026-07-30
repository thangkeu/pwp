"""VersionExtractor — nhận diện chuỗi phiên bản phần mềm/firmware trong văn bản."""

from __future__ import annotations

import re

_PATTERNS = [
    # "v1.2.3", "v7.2", "phiên bản 2.0", "version 3.1.4"
    r"\bv\d+(\.\d+){1,3}\b",
    r"\b(?:phiên bản|version)\s+\d+(\.\d+){0,3}\b",
    # "FortiOS 7.2.5", "IOS-XE 17.3", "ESXi 8.0" — tên phần mềm + số version liền kề
    r"\b[A-Za-z][A-Za-z0-9-]{2,20}\s+\d+(\.\d+){1,3}\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _PATTERNS]


class VersionExtractor:
    def extract(self, text: str) -> list[str]:
        """@returns: danh sách chuỗi version phát hiện được, không trùng lặp, giữ thứ tự xuất hiện."""
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
