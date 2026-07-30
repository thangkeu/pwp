from app.engine.dictionary_extractor import DictionaryExtractor


class TestDictionaryExtractor:
    def test_mac_dinh_customer_project_rong(self):
        extractor = DictionaryExtractor()
        assert extractor.extract_customers("Công ty ABC là khách hàng lớn.") == []
        assert extractor.extract_projects("Dự án Nâng cấp hạ tầng chi nhánh.") == []

    def test_nhan_dien_customer_khi_co_dictionary(self):
        extractor = DictionaryExtractor(customers=["Ngân hàng ABC", "Công ty XYZ"])
        result = extractor.extract_customers("Đề xuất gửi Ngân hàng ABC về giải pháp SD-WAN.")
        assert result == ["Ngân hàng ABC"]

    def test_nhan_dien_project_khi_co_dictionary(self):
        extractor = DictionaryExtractor(projects=["Nâng cấp hạ tầng chi nhánh 2026"])
        result = extractor.extract_projects("Tài liệu thuộc dự án Nâng cấp hạ tầng chi nhánh 2026.")
        assert result == ["Nâng cấp hạ tầng chi nhánh 2026"]

    def test_khong_phan_biet_hoa_thuong(self):
        extractor = DictionaryExtractor(customers=["Ngân Hàng ABC"])
        result = extractor.extract_customers("làm việc với ngân hàng abc trong quý này")
        assert result == ["Ngân Hàng ABC"]

    def test_nhan_dien_industry_mac_dinh(self):
        extractor = DictionaryExtractor()
        result = extractor.extract_industries("Dự án triển khai tại ngân hàng thương mại cổ phần.")
        assert "Ngân hàng - Tài chính" in result

    def test_nhieu_industry_cung_luc(self):
        extractor = DictionaryExtractor()
        result = extractor.extract_industries("Khách hàng vừa là ngân hàng vừa có mảng viễn thông.")
        assert "Ngân hàng - Tài chính" in result
        assert "Viễn thông" in result

    def test_khong_khop_industry_nao_tra_rong(self):
        extractor = DictionaryExtractor()
        assert extractor.extract_industries("Văn bản không thuộc lĩnh vực cụ thể nào.") == []
