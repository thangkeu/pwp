"""
DrawioAdapter — trích xuất từ file .drawio (mxGraph XML).

Draw.io (app.diagrams.net) lưu dưới 2 dạng con phổ biến, adapter phải xử lý cả 2:
  1. XML thô: <diagram> chứa trực tiếp <mxGraphModel> làm phần tử con.
  2. XML nén: <diagram> chứa text là chuỗi base64(deflate(urlencode(xml))) — mặc định khi
     lưu từ giao diện web app.diagrams.net.
"""

from __future__ import annotations

import base64
import urllib.parse
import zlib
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

from app.adapters.base import ParserAdapter, ParsingError
from app.domain.parsed_document import ParsedDocument, ParsedDocumentMetadata


def _strip_html(value: str) -> str:
    """Nhãn shape trong draw.io thường chứa HTML nhỏ (vd: '<b>Branch</b><br>200 users')."""
    return BeautifulSoup(value, "html.parser").get_text(separator=" ", strip=True)


def _decompress_diagram_text(raw_text: str) -> str:
    """
    Giải nén nội dung <diagram> dạng compressed của app.diagrams.net.
    @raises ParsingError: khi base64/deflate không hợp lệ (không phải file draw.io thật).
    """
    try:
        compressed = base64.b64decode(raw_text)
        decompressed = zlib.decompress(compressed, -15)  # raw deflate, không header/trailer zlib
        return urllib.parse.unquote(decompressed.decode("utf-8"))
    except Exception as exc:
        raise ParsingError(f"Không giải nén được nội dung <diagram> (draw.io): {exc}") from exc


class DrawioAdapter(ParserAdapter):
    @property
    def supported_extensions(self) -> list[str]:
        return ["drawio"]

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            raw = content.decode("utf-8", errors="replace")
            root = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise ParsingError(f"File .drawio không phải XML hợp lệ: {filename} ({exc})") from exc

        diagrams = root.findall(".//diagram")
        if not diagrams:
            # Bản thân root có thể chính là <mxGraphModel> (file export chỉ 1 diagram, không bọc <mxfile>).
            diagrams = [root] if root.tag == "mxGraphModel" else []

        text_parts: list[str] = []
        links: list[str] = []
        warnings: list[str] = []

        for diagram in diagrams:
            diagram_name = diagram.get("name", "")
            graph_model = diagram if diagram.tag == "mxGraphModel" else diagram.find("mxGraphModel")

            if graph_model is None and diagram.text and diagram.text.strip():
                try:
                    xml_str = _decompress_diagram_text(diagram.text.strip())
                    graph_model = ET.fromstring(xml_str)
                except ParsingError as exc:
                    warnings.append(str(exc))
                    continue

            if graph_model is None:
                continue

            labels = []
            for cell in graph_model.findall(".//mxCell"):
                value = cell.get("value")
                if value and value.strip():
                    clean_text = _strip_html(value)
                    if clean_text:
                        labels.append(clean_text)
                        if cell.get("edge") == "1":
                            links.append(clean_text)  # nhãn trên mũi tên/kết nối — dùng như "reference"

            if labels:
                header = f"[Diagram: {diagram_name}]" if diagram_name else "[Diagram]"
                text_parts.append(header + "\n" + "\n".join(labels))

        text = "\n\n".join(text_parts)
        word_count = len(text.split())

        return ParsedDocument(
            text=text,
            references=links,
            metadata=ParsedDocumentMetadata(
                parser_name="DrawioAdapter",
                source_filename=filename,
                mime_type="application/vnd.jgraph.mxfile",
                page_count=len(diagrams) or None,
                word_count=word_count,
                warnings=warnings,
            ),
        )
