"""PdfAdapter — trích xuất từ file .pdf dùng pdfplumber (text + table theo từng trang)."""

from __future__ import annotations

import io

import pdfplumber

from app.adapters.base import ParserAdapter, ParsingError
from app.domain.parsed_document import (
    ParsedDocument,
    ParsedDocumentMetadata,
    ParsedTable,
)


class PdfAdapter(ParserAdapter):
    @property
    def supported_extensions(self) -> list[str]:
        return ["pdf"]

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        warnings: list[str] = []
        text_parts: list[str] = []
        tables: list[ParsedTable] = []
        links: list[str] = []

        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                page_count = len(pdf.pages)
                for page_number, page in enumerate(pdf.pages, start=1):
                    try:
                        page_text = page.extract_text() or ""
                        if page_text.strip():
                            text_parts.append(page_text)

                        for table_data in page.extract_tables():
                            rows = [
                                ["" if cell is None else str(cell) for cell in row]
                                for row in table_data
                                if row
                            ]
                            if rows:
                                tables.append(ParsedTable(rows=rows, page_number=page_number))

                        for annot in page.annots or []:
                            uri = (annot.get("data") or {}).get("URI") if annot.get("data") else None
                            if uri:
                                links.append(uri)
                    except Exception as exc:  # noqa: BLE001
                        # Fail gracefully theo từng trang: 1 trang lỗi không làm hỏng cả tài liệu.
                        warnings.append(f"Trang {page_number}: lỗi khi trích xuất ({exc})")
        except Exception as exc:
            raise ParsingError(f"File PDF không hợp lệ hoặc hỏng: {filename} ({exc})") from exc

        text = "\n\n".join(text_parts)
        word_count = len(text.split())

        return ParsedDocument(
            text=text,
            tables=tables,
            links=sorted(set(links)),
            metadata=ParsedDocumentMetadata(
                parser_name="PdfAdapter",
                source_filename=filename,
                mime_type="application/pdf",
                page_count=page_count,
                word_count=word_count,
                warnings=warnings,
            ),
        )
