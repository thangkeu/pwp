from app.adapters.base import ParsingError
from app.adapters.docx_adapter import DocxAdapter


class TestDocxAdapter:
    def test_supported_extensions(self):
        assert DocxAdapter().supported_extensions == ["docx"]

    def test_parse_trich_xuat_text_va_table(self, sample_docx_bytes):
        result = DocxAdapter().parse(sample_docx_bytes, "baogia.docx")

        assert "Báo giá Fortigate 100F" in result.text
        assert "Đây là tài liệu mẫu" in result.text
        assert len(result.tables) == 1
        assert result.tables[0].rows[0] == ["Part Number", "Qty"]
        assert result.tables[0].rows[1] == ["FG-100F", "2"]
        assert result.metadata.parser_name == "DocxAdapter"
        assert result.metadata.source_filename == "baogia.docx"
        assert result.metadata.word_count > 0

    def test_parse_file_hong_nem_parsing_error(self):
        garbage = b"day khong phai file docx that"
        try:
            DocxAdapter().parse(garbage, "fake.docx")
            assert False, "Phải ném ParsingError"
        except ParsingError:
            pass
