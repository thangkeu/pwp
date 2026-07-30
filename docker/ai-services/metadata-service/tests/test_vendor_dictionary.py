from app.engine.vendor_dictionary import VendorModelExtractor


class TestVendorModelExtractor:
    def test_nhan_dien_model_cu_the(self):
        extractor = VendorModelExtractor()
        result = extractor.extract("Đề xuất triển khai 2x FortiGate 100F cho chi nhánh 200 user.")

        vendors = [m.vendor for m in result]
        models = [m.model for m in result]
        assert "Fortinet" in vendors
        assert any("FortiGate 100F" in (m or "") for m in models)

    def test_nhieu_vendor_trong_1_van_ban(self):
        extractor = VendorModelExtractor()
        result = extractor.extract("So sánh Cisco Catalyst 9300 với Juniper EX4300 cho lớp access.")

        vendors = {m.vendor for m in result}
        assert "Cisco" in vendors
        assert "Juniper" in vendors

    def test_khong_trung_lap_neu_model_xuat_hien_nhieu_lan(self):
        extractor = VendorModelExtractor()
        result = extractor.extract("FortiGate 100F là thiết bị chính. FortiGate 100F HA cluster 2 node.")

        forti_100f_matches = [m for m in result if m.model and "100F" in m.model]
        assert len(forti_100f_matches) == 1

    def test_fallback_ten_vendor_khong_kem_model(self):
        extractor = VendorModelExtractor()
        result = extractor.extract("Khách hàng đang cân nhắc giải pháp của Fortinet.")

        assert len(result) == 1
        assert result[0].vendor == "Fortinet"
        assert result[0].model is None

    def test_van_ban_khong_co_vendor_nao_tra_rong(self):
        extractor = VendorModelExtractor()
        assert extractor.extract("Đây là văn bản không liên quan thiết bị mạng nào.") == []

    def test_dictionary_tuy_chinh_qua_constructor(self):
        custom = {"ACME": [r"\bACME-\d{3}\b"]}
        extractor = VendorModelExtractor(vendor_patterns=custom)
        result = extractor.extract("Sử dụng thiết bị ACME-500 cho dự án.")

        assert len(result) == 1
        assert result[0].vendor == "ACME"
        assert result[0].model == "ACME-500"
