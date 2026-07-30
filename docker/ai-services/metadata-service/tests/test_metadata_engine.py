from app.engine.metadata_engine import MetadataEngine


class TestMetadataEngine:
    def test_tong_hop_tat_ca_extractor(self):
        engine = MetadataEngine()
        text = (
            "Đề xuất giải pháp SD-WAN cho Ngân hàng ABC, ngày 12/07/2026. "
            "Sử dụng FortiGate 100F chạy FortiOS 7.2.5. Tài liệu MẬT."
        )
        result = engine.extract(text, filename="deXuat_SDWAN.docx")

        assert result.security_level.level == "confidential"
        assert any(m.vendor == "Fortinet" for m in result.vendor_models)
        assert "12/07/2026" in result.dates_found
        assert any("7.2.5" in v for v in result.versions_found)
        assert "Ngân hàng - Tài chính" in result.industries
        assert result.document_type == "proposal"
        assert result.warnings == []

    def test_van_ban_rong_khong_loi(self):
        engine = MetadataEngine()
        result = engine.extract("", filename=None)

        assert result.customers == []
        assert result.vendor_models == []
        assert result.security_level.level == "internal"

    def test_canh_bao_van_ban_qua_dai(self):
        engine = MetadataEngine()
        result = engine.extract("a" * 600_000)
        assert len(result.warnings) == 1
        assert "vượt ngưỡng" in result.warnings[0]

    def test_dependency_injection_extractor_tuy_chinh(self):
        from app.engine.vendor_dictionary import VendorModelExtractor

        custom_vendor_extractor = VendorModelExtractor(vendor_patterns={"ACME": [r"\bACME-\d+\b"]})
        engine = MetadataEngine(vendor_extractor=custom_vendor_extractor)

        result = engine.extract("Sử dụng ACME-100 cho hệ thống.")
        assert result.vendor_models[0].vendor == "ACME"
