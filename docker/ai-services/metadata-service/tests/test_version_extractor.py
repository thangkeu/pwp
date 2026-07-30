from app.engine.version_extractor import VersionExtractor


class TestVersionExtractor:
    def test_dinh_dang_v_prefix(self):
        extractor = VersionExtractor()
        result = extractor.extract("Nâng cấp lên v7.2.5 trong quý tới.")
        assert "v7.2.5" in result

    def test_dinh_dang_phien_ban(self):
        extractor = VersionExtractor()
        result = extractor.extract("Tài liệu này là phiên bản 2.1, thay thế bản cũ.")
        assert any("phiên bản 2.1" in v.lower() for v in result)

    def test_ten_phan_mem_kem_so_version(self):
        extractor = VersionExtractor()
        result = extractor.extract("Yêu cầu tối thiểu FortiOS 7.2 và ESXi 8.0.")
        assert any("7.2" in v for v in result)
        assert any("8.0" in v for v in result)

    def test_van_ban_khong_co_version_tra_rong(self):
        extractor = VersionExtractor()
        assert extractor.extract("Không có version nào trong văn bản này cả.") == []
