"""
SecurityLevelClassifier — phân loại `security_level` (public/internal/confidential) theo từ
khoá xuất hiện trong văn bản (INSTRUCTIONS.md 2.6: trường `security_level` dùng để Context
Builder lọc theo quyền người hỏi).

Mặc định 'internal' khi không có tín hiệu rõ ràng — AN TOÀN HƠN mặc định 'public', vì tài liệu
presales nội bộ (báo giá, kiến trúc khách hàng) không nên vô tình lộ ra ngoài chỉ vì thiếu từ
khoá nhận diện.
"""

from __future__ import annotations

import os
import re

from app.domain.extracted_metadata import SecurityLevelResult

DEFAULT_KEYWORDS: dict[str, list[str]] = {
    "confidential": [
        "mật", "tuyệt mật", "tối mật", "confidential", "strictly confidential",
        "not for distribution", "nda", "bảo mật tuyệt đối",
    ],
    "public": [
        "công khai", "public", "marketing", "brochure", "công bố rộng rãi",
    ],
    # 'internal' không cần từ khoá riêng — là mặc định khi không khớp 2 nhóm trên.
}


class SecurityLevelClassifier:
    def __init__(self, keywords: dict[str, list[str]] | None = None):
        self._keywords = keywords or self._load_from_env_or_default()

    @staticmethod
    def _load_from_env_or_default() -> dict[str, list[str]]:
        import json

        path = os.environ.get("METADATA_SECURITY_KEYWORDS_PATH", "")
        if path and os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return DEFAULT_KEYWORDS

    def classify(self, text: str) -> SecurityLevelResult:
        lowered = text.lower()

        # Ưu tiên 'confidential' TRƯỚC 'public' — nếu văn bản vừa có từ "công khai" vừa có
        # "tuyệt mật" (hiếm nhưng có thể xảy ra khi trích dẫn văn bản khác), thà bảo mật quá mức
        # còn hơn để lộ tài liệu nhạy cảm (Fail-safe theo hướng an toàn).
        for level in ("confidential", "public"):
            matched = [kw for kw in self._keywords.get(level, []) if re.search(re.escape(kw), lowered)]
            if matched:
                return SecurityLevelResult(level=level, matched_keywords=matched)

        return SecurityLevelResult(level="internal", matched_keywords=[])
