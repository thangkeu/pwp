from app.adapters.text_adapter import TextAdapter


class TestTextAdapter:
    def test_supported_extensions(self):
        assert set(TextAdapter().supported_extensions) == {"txt", "md", "markdown", "html", "htm"}

    def test_parse_txt_thuan(self):
        result = TextAdapter().parse("Xin chào https://example.com/vi thế giới".encode(), "note.txt")
        assert "Xin chào" in result.text
        assert "https://example.com/vi" in result.links

    def test_parse_markdown_tach_link_va_table(self, sample_markdown_bytes):
        result = TextAdapter().parse(sample_markdown_bytes, "doc.md")

        assert "Tiêu đề" in result.text
        assert "https://example.com/docs" in result.links
        assert len(result.tables) == 1
        assert result.tables[0].rows[0] == ["A", "B"]
        assert result.tables[0].rows[1] == ["1", "2"]

    def test_parse_html_tach_link_va_table(self, sample_html_bytes):
        result = TextAdapter().parse(sample_html_bytes, "page.html")

        assert "Tiêu đề" in result.text
        assert "https://example.com" in result.links
        assert len(result.tables) == 1
        assert result.tables[0].rows == [["1", "2"]]

    def test_parse_khong_nem_loi_voi_encoding_la(self):
        # Nội dung binary không phải UTF-8 hợp lệ vẫn phải parse được nhờ errors='replace',
        # không được crash toàn bộ pipeline vì 1 file text lạ encoding.
        result = TextAdapter().parse(b"\xff\xfe\x00\x01 hello", "weird.txt")
        assert "hello" in result.text
