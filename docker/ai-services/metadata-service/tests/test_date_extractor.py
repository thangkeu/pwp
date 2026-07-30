from app.engine.date_extractor import DateExtractor


class TestDateExtractor:
    def test_dinh_dang_dd_mm_yyyy(self):
        extractor = DateExtractor()
        result = extractor.extract("Hợp đồng ký ngày 12/07/2026, hiệu lực đến 12/07/2027.")
        assert "12/07/2026" in result
        assert "12/07/2027" in result

    def test_dinh_dang_iso(self):
        extractor = DateExtractor()
        result = extractor.extract("Ngày tạo: 2026-07-28.")
        assert "2026-07-28" in result

    def test_dinh_dang_tieng_viet_day_du(self):
        extractor = DateExtractor()
        result = extractor.extract("Biên bản họp ngày 15 tháng 8 năm 2026.")
        assert any("15" in d and "8" in d and "2026" in d for d in result)

    def test_dinh_dang_tieng_anh(self):
        extractor = DateExtractor()
        result = extractor.extract("Proposal submitted on 12 July 2026.")
        assert any("July" in d for d in result)

    def test_khong_trung_lap(self):
        extractor = DateExtractor()
        result = extractor.extract("12/07/2026 và 12/07/2026 lại xuất hiện.")
        assert result.count("12/07/2026") == 1

    def test_van_ban_khong_co_ngay_tra_rong(self):
        extractor = DateExtractor()
        assert extractor.extract("Không có ngày tháng nào ở đây.") == []
