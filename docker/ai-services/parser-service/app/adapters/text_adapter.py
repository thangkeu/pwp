"""TextAdapter — xử lý TXT, Markdown, HTML (3 định dạng text-based, đủ đơn giản để gộp 1 adapter)."""

from __future__ import annotations

import re

import markdown as md_lib
from bs4 import BeautifulSoup

from app.adapters.base import ParserAdapter, ParsingError
from app.domain.parsed_document import ParsedDocument, ParsedDocumentMetadata

_LINK_PATTERN = re.compile(r"https?://[^\s)\]\"'<>]+")


class TextAdapter(ParserAdapter):
    """Hỗ trợ .txt (thuần), .md (render qua HTML để tách link/text), .html (parse DOM)."""

    @property
    def supported_extensions(self) -> list[str]:
        return ["txt", "md", "markdown", "html", "htm"]

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            raw = content.decode("utf-8", errors="replace")
        except Exception as exc:  # pragma: no cover - decode('utf-8', errors='replace') hiếm khi tự ném lỗi
            raise ParsingError(f"Không decode được nội dung text của {filename}: {exc}") from exc

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

        if ext in ("md", "markdown"):
            html = md_lib.markdown(raw, extensions=["tables"])
            text, links, tables = self._parse_html(html)
        elif ext in ("html", "htm"):
            text, links, tables = self._parse_html(raw)
        else:
            text = raw
            links = _LINK_PATTERN.findall(raw)
            tables = []

        word_count = len(text.split())
        return ParsedDocument(
            text=text,
            tables=tables,
            links=sorted(set(links)),
            metadata=ParsedDocumentMetadata(
                parser_name="TextAdapter",
                source_filename=filename,
                mime_type=f"text/{ext}",
                word_count=word_count,
            ),
        )

    @staticmethod
    def _parse_html(html: str):
        soup = BeautifulSoup(html, "html.parser")

        links = [a.get("href") for a in soup.find_all("a", href=True)]
        links = [str(link) for link in links if link]

        tables = []
        for table_tag in soup.find_all("table"):
            rows = []
            for tr in table_tag.find_all("tr"):
                cells = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(cells)
            if rows:
                from app.domain.parsed_document import ParsedTable

                tables.append(ParsedTable(rows=rows))

        text = soup.get_text(separator="\n", strip=True)
        return text, links, tables
