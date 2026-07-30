from app.adapters.base import ParsingError
from app.adapters.pdf_adapter import PdfAdapter


class TestPdfAdapter:
    def test_supported_extensions(self):
        assert PdfAdapter().supported_extensions == ["pdf"]

    def test_parse_trich_xuat_text(self, sample_pdf_bytes):
        result = PdfAdapter().parse(sample_pdf_bytes, "taimau.pdf")

        assert "Tai lieu mau cho unit test PdfAdapter" in result.text
        assert result.metadata.page_count == 1
        assert result.metadata.parser_name == "PdfAdapter"

    def test_parse_file_hong_nem_parsing_error(self):
        try:
            PdfAdapter().parse(b"%PDF-not-really-valid", "fake.pdf")
            assert False, "Phải ném ParsingError"
        except ParsingError:
            pass
