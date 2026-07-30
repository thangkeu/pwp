from app.adapters.base import ParsingError
from app.adapters.pptx_adapter import PptxAdapter


class TestPptxAdapter:
    def test_supported_extensions(self):
        assert PptxAdapter().supported_extensions == ["pptx"]

    def test_parse_trich_xuat_text_theo_slide(self, sample_pptx_bytes):
        result = PptxAdapter().parse(sample_pptx_bytes, "kientruc.pptx")

        assert "[Slide 1]" in result.text
        assert "Kiến trúc SD-WAN đề xuất" in result.text
        assert "Nội dung mẫu cho unit test PptxAdapter" in result.text
        assert result.metadata.page_count == 1

    def test_parse_file_hong_nem_parsing_error(self):
        try:
            PptxAdapter().parse(b"not a pptx", "fake.pptx")
            assert False, "Phải ném ParsingError"
        except ParsingError:
            pass
