from app.adapters.base import ParsingError
from app.adapters.drawio_adapter import DrawioAdapter


class TestDrawioAdapter:
    def test_supported_extensions(self):
        assert DrawioAdapter().supported_extensions == ["drawio"]

    def test_parse_dang_tho_trich_xuat_nhan_shape(self, sample_drawio_bytes):
        result = DrawioAdapter().parse(sample_drawio_bytes, "kientruc.drawio")

        assert "[Diagram: Kien truc SD-WAN]" in result.text
        assert "Fortigate 100F" in result.text
        # Nhãn HTML phải được strip tag, giữ lại text thuần
        assert "Branch Office 200 users" in result.text
        assert "<b>" not in result.text

    def test_parse_dang_tho_nhan_tren_edge_dua_vao_references(self, sample_drawio_bytes):
        result = DrawioAdapter().parse(sample_drawio_bytes, "kientruc.drawio")
        assert "ket noi VPN" in result.references

    def test_parse_dang_nen_giai_nen_dung(self, sample_drawio_compressed_bytes):
        result = DrawioAdapter().parse(sample_drawio_compressed_bytes, "nen.drawio")
        assert "Node nen thu (compressed)" in result.text

    def test_parse_khong_phai_xml_nem_parsing_error(self):
        try:
            DrawioAdapter().parse(b"khong phai xml hop le <<<", "fake.drawio")
            assert False, "Phải ném ParsingError"
        except ParsingError:
            pass
