"""
DocumentTypeClassifier — suy luận `document_type` (proposal/bom/meeting_minutes/contract/...)
từ tên file và từ khoá nội dung. Config-driven qua `METADATA_DOCTYPE_KEYWORDS_PATH`.
"""

from __future__ import annotations

import json
import os
import re

# Thứ tự trong dict quyết định độ ưu tiên khi nhiều loại cùng khớp (liệt kê trước = ưu tiên hơn).
DEFAULT_DOCTYPE_KEYWORDS: dict[str, list[str]] = {
    "bom": ["bill of material", "bom", "danh mục thiết bị", "part number", "bảng vật tư"],
    "boq": ["bill of quantity", "boq", "khối lượng mời thầu"],
    "meeting_minutes": ["biên bản họp", "meeting minutes", "action item", "minutes of meeting"],
    "contract": ["hợp đồng", "contract", "phụ lục hợp đồng", "điều khoản"],
    "proposal": ["đề xuất giải pháp", "proposal", "báo giá", "quotation"],
    "survey_report": ["khảo sát", "survey report", "site survey"],
    "architecture_design": ["kiến trúc giải pháp", "high level design", "hld", "low level design", "lld"],
}


class DocumentTypeClassifier:
    def __init__(self, keywords: dict[str, list[str]] | None = None):
        self._keywords = keywords or self._load_from_env_or_default()

    @staticmethod
    def _load_from_env_or_default() -> dict[str, list[str]]:
        path = os.environ.get("METADATA_DOCTYPE_KEYWORDS_PATH", "")
        if path and os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return DEFAULT_DOCTYPE_KEYWORDS

    def classify(self, text: str, filename: str | None = None) -> str | None:
        haystack = f"{filename or ''} {text}".lower()
        for doc_type, keywords in self._keywords.items():
            for kw in keywords:
                if re.search(re.escape(kw.lower()), haystack):
                    return doc_type
        return None
