"""
VendorModelExtractor — nhận diện Vendor + Model thiết bị hạ tầng trong văn bản.

Config-driven (Nguyên tắc 3, INSTRUCTIONS.md 1.5): danh sách vendor/pattern mặc định định
nghĩa dưới đây chỉ là DEFAULT — có thể override hoàn toàn bằng cách trỏ biến môi trường
`METADATA_VENDOR_DICT_PATH` tới 1 file JSON cùng cấu trúc, KHÔNG cần sửa code khi thêm vendor
mới hoặc đổi pattern (đúng tinh thần Sprint 1.2 "Sync/Metadata Engine" — mở rộng không sửa lõi).
"""

from __future__ import annotations

import json
import os
import re

from app.domain.extracted_metadata import VendorModelMatch

# DEFAULT_VENDOR_PATTERNS: mỗi vendor map tới 1 danh sách regex pattern (không phân biệt hoa
# thường) khớp TÊN MODEL cụ thể. Vendor chỉ được thêm vào kết quả khi có ít nhất 1 model pattern
# khớp HOẶC khi tên vendor xuất hiện trần trụi trong text (fallback, độ tin cậy thấp hơn).
DEFAULT_VENDOR_PATTERNS: dict[str, list[str]] = {
    "Fortinet": [
        r"\bFortiGate[\s-]?\d{2,4}[A-Z]?\b",
        r"\bFortiAnalyzer[\s-]?\w*\b",
        r"\bFortiManager[\s-]?\w*\b",
        r"\bFortiSwitch[\s-]?\w*\b",
        r"\bFortiAP[\s-]?\w*\b",
    ],
    "Cisco": [
        r"\bCatalyst\s?\d{3,4}\w*\b",
        r"\bASA\s?\d{4}\w*\b",
        r"\bNexus\s?\d{4}\w*\b",
        r"\bMeraki\s?[A-Z]{1,3}\d{2,3}\b",
    ],
    "Juniper": [
        r"\bSRX\s?\d{2,4}\b",
        r"\bEX\s?\d{4}\b",
        r"\bMX\s?\d{3,4}\b",
    ],
    "Palo Alto Networks": [
        r"\bPA-\d{3,4}\b",
    ],
    "Aruba (HPE)": [
        r"\bAruba\s?\d{4}\w*\b",
    ],
    "Dell EMC": [
        r"\bPowerEdge\s?[A-Z]\d{3,4}\b",
        r"\bPowerStore\s?\d{3,4}\w?\b",
    ],
    "NetApp": [
        r"\bFAS\d{3,4}\b",
        r"\bAFF\s?[A-Z]\d{3}\b",
    ],
    "VMware": [
        r"\bvSphere\s?\d(\.\d)?\b",
        r"\bvSAN\s?\d(\.\d)?\b",
    ],
    "F5": [
        r"\bBIG-IP\s?\w*\b",
    ],
    "Huawei": [
        r"\bAR\d{3,4}\b",
        r"\bCE\d{4}\b",
    ],
}


class VendorModelExtractor:
    def __init__(self, vendor_patterns: dict[str, list[str]] | None = None):
        self._vendor_patterns = vendor_patterns or self._load_from_env_or_default()
        self._compiled = {
            vendor: [re.compile(p, re.IGNORECASE) for p in patterns]
            for vendor, patterns in self._vendor_patterns.items()
        }

    @staticmethod
    def _load_from_env_or_default() -> dict[str, list[str]]:
        path = os.environ.get("METADATA_VENDOR_DICT_PATH", "")
        if path and os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return DEFAULT_VENDOR_PATTERNS

    def extract(self, text: str) -> list[VendorModelMatch]:
        """
        @param text: nội dung văn bản đã parse (ParsedDocument.text)
        @returns: danh sách (vendor, model) duy nhất theo `matched_text`, giữ thứ tự xuất hiện
        """
        matches: list[VendorModelMatch] = []
        seen: set[str] = set()

        for vendor, patterns in self._compiled.items():
            for pattern in patterns:
                for m in pattern.finditer(text):
                    matched_text = m.group(0).strip()
                    dedupe_key = f"{vendor}:{matched_text.lower()}"
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    matches.append(VendorModelMatch(vendor=vendor, model=matched_text, matched_text=matched_text))

            # Fallback độ tin cậy thấp: tên vendor xuất hiện trần trụi mà KHÔNG có model pattern
            # nào khớp (vd: "giải pháp của Cisco" mà không kèm số hiệu thiết bị cụ thể).
            vendor_name_pattern = re.compile(re.escape(vendor.split(" (")[0]), re.IGNORECASE)
            if vendor not in [vm.vendor for vm in matches] and vendor_name_pattern.search(text):
                dedupe_key = f"{vendor}:__name_only__"
                if dedupe_key not in seen:
                    seen.add(dedupe_key)
                    matches.append(VendorModelMatch(vendor=vendor, model=None, matched_text=vendor.split(" (")[0]))

        return matches
