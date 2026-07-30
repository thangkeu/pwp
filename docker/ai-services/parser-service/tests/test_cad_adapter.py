from app.adapters.base import DependencyUnavailableError, ParsingError
from app.adapters.cad_adapter import CadAdapter


class TestCadAdapter:
    def test_supported_extensions(self):
        assert set(CadAdapter().supported_extensions) == {"dxf", "dwg"}

    def test_parse_dxf_trich_xuat_text_tu_entity(self, sample_dxf_bytes):
        result = CadAdapter().parse(sample_dxf_bytes, "sodo.dxf")

        assert "Fortigate 100F - Rack A1" in result.text
        assert "Ghi chu: 2x FG-100F HA cluster" in result.text
        assert result.metadata.parser_name == "CadAdapter"
        assert any("Layers phát hiện" in w for w in result.metadata.warnings)

    def test_parse_dxf_hong_nem_parsing_error(self):
        try:
            CadAdapter().parse(b"not a real dxf file content", "fake.dxf")
            assert False, "Phải ném ParsingError"
        except ParsingError:
            pass

    def test_parse_dwg_nem_dependency_unavailable_voi_huong_dan_ro_rang(self):
        """
        .dwg là định dạng nhị phân độc quyền, KHÔNG parse trực tiếp được — adapter phải trả lỗi
        rõ ràng kèm hướng dẫn convert sang DXF, thay vì giả vờ hỗ trợ hoặc trả kết quả rỗng.
        """
        try:
            CadAdapter().parse(b"fake dwg binary content", "sodo.dwg")
            assert False, "Phải ném DependencyUnavailableError"
        except DependencyUnavailableError as exc:
            assert "DXF" in str(exc)
            assert "ODA File Converter" in str(exc)
