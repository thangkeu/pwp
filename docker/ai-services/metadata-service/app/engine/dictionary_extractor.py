"""
DictionaryExtractor — nhận diện Khách hàng / Dự án / Lĩnh vực bằng cách khớp với 1 danh sách
tên đã biết trước (dictionary lookup), KHÔNG dùng NER (xem README_SPRINT1.2.md Mục 2 — NER
model thật là known gap, dời sang Sprint sau).

Khác với Vendor (danh sách vendor hạ tầng IT phổ biến là kiến thức chung, có thể đặt default
hợp lý), tên KHÁCH HÀNG và DỰ ÁN là dữ liệu đặc thù riêng từng công ty Presales — do đó
`DEFAULT_CUSTOMERS`/`DEFAULT_PROJECTS` cố ý để RỖNG, bắt buộc cấu hình qua
`METADATA_CUSTOMER_DICT_PATH`/`METADATA_PROJECT_DICT_PATH` (danh sách khách hàng/dự án thật của
công ty, lấy từ Sheet `Projects`/`Contacts` đã có — Sprint 1.2b nên tự động đồng bộ danh sách
này từ Gateway thay vì cấu hình tay).

`DEFAULT_INDUSTRIES` có sẵn giá trị mặc định vì lĩnh vực kinh doanh phổ biến (ngân hàng, viễn
thông...) là kiến thức chung, ít thay đổi.
"""

from __future__ import annotations

import json
import os
import re

DEFAULT_CUSTOMERS: list[str] = []
DEFAULT_PROJECTS: list[str] = []

DEFAULT_INDUSTRIES: dict[str, list[str]] = {
    "Ngân hàng - Tài chính": ["ngân hàng", "bank", "tài chính", "chứng khoán", "fintech"],
    "Viễn thông": ["viễn thông", "telecom", "nhà mạng", "isp"],
    "Y tế": ["bệnh viện", "y tế", "healthcare", "hospital"],
    "Giáo dục": ["trường học", "đại học", "giáo dục", "education", "university"],
    "Chính phủ": ["chính phủ", "government", "bộ", "sở", "uỷ ban nhân dân", "ủy ban nhân dân"],
    "Sản xuất": ["nhà máy", "sản xuất", "manufacturing", "factory"],
    "Bán lẻ": ["bán lẻ", "retail", "siêu thị", "chuỗi cửa hàng"],
}


def _load_list_from_env(env_var: str, default: list[str]) -> list[str]:
    path = os.environ.get(env_var, "")
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def _load_dict_from_env(env_var: str, default: dict[str, list[str]]) -> dict[str, list[str]]:
    path = os.environ.get(env_var, "")
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


class DictionaryExtractor:
    def __init__(
        self,
        customers: list[str] | None = None,
        projects: list[str] | None = None,
        industries: dict[str, list[str]] | None = None,
    ):
        self._customers = customers if customers is not None else _load_list_from_env(
            "METADATA_CUSTOMER_DICT_PATH", DEFAULT_CUSTOMERS
        )
        self._projects = projects if projects is not None else _load_list_from_env(
            "METADATA_PROJECT_DICT_PATH", DEFAULT_PROJECTS
        )
        self._industries = industries if industries is not None else _load_dict_from_env(
            "METADATA_INDUSTRY_DICT_PATH", DEFAULT_INDUSTRIES
        )

    def extract_customers(self, text: str) -> list[str]:
        return self._match_names(text, self._customers)

    def extract_projects(self, text: str) -> list[str]:
        return self._match_names(text, self._projects)

    def extract_industries(self, text: str) -> list[str]:
        lowered = text.lower()
        matched = []
        for industry, keywords in self._industries.items():
            if any(re.search(re.escape(kw), lowered) for kw in keywords):
                matched.append(industry)
        return matched

    @staticmethod
    def _match_names(text: str, names: list[str]) -> list[str]:
        lowered = text.lower()
        return [name for name in names if re.search(re.escape(name.lower()), lowered)]
