import glob
import os
import tempfile

from app.adapters.base import ParsingError
from app.adapters.visio_adapter import VisioAdapter


class TestVisioAdapter:
    def test_supported_extensions(self):
        assert VisioAdapter().supported_extensions == ["vsdx"]

    def test_parse_trich_xuat_text_theo_page(self, sample_vsdx_bytes):
        result = VisioAdapter().parse(sample_vsdx_bytes, "kientruc.vsdx")

        assert "[Page: Page-1]" in result.text
        assert "Kien truc SD-WAN de xuat" in result.text
        assert result.metadata.page_count == 1
        assert result.metadata.parser_name == "VisioAdapter"

    def test_parse_file_hong_nem_parsing_error(self):
        try:
            VisioAdapter().parse(b"not a real vsdx file", "fake.vsdx")
            assert False, "Phải ném ParsingError"
        except ParsingError:
            pass

    def test_parse_khong_ro_ri_file_tam_trong_thu_muc_temp_he_thong(self, sample_vsdx_bytes):
        """
        Adapter phải dọn `tempfile.NamedTemporaryFile` (suffix .vsdx) trong `finally`, dù parse
        thành công hay ném ParsingError — xác nhận bằng cách đếm số file .vsdx còn sót trong
        thư mục temp hệ thống trước/sau khi gọi parse() nhiều lần (kể cả trường hợp file hỏng).
        """
        pattern = os.path.join(tempfile.gettempdir(), "*.vsdx")
        before = set(glob.glob(pattern))

        for _ in range(3):
            VisioAdapter().parse(sample_vsdx_bytes, "kientruc.vsdx")
        try:
            VisioAdapter().parse(b"not a real vsdx file", "fake.vsdx")
        except ParsingError:
            pass

        after = set(glob.glob(pattern))
        assert after == before, f"Rò rỉ file tạm: {after - before}"
