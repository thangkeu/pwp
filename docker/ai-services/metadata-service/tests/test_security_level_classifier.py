from app.engine.security_level_classifier import SecurityLevelClassifier


class TestSecurityLevelClassifier:
    def test_mac_dinh_internal_khi_khong_co_tin_hieu(self):
        classifier = SecurityLevelClassifier()
        result = classifier.classify("Đây là tài liệu bình thường không có từ khoá đặc biệt.")
        assert result.level == "internal"
        assert result.matched_keywords == []

    def test_nhan_dien_confidential(self):
        classifier = SecurityLevelClassifier()
        result = classifier.classify("Tài liệu MẬT - không phổ biến ra ngoài.")
        assert result.level == "confidential"
        assert "mật" in result.matched_keywords

    def test_nhan_dien_public(self):
        classifier = SecurityLevelClassifier()
        result = classifier.classify("Đây là brochure công khai gửi khách hàng.")
        assert result.level == "public"

    def test_uu_tien_confidential_neu_ca_2_cung_xuat_hien(self):
        classifier = SecurityLevelClassifier()
        result = classifier.classify("Tài liệu công khai nhưng có phần MẬT bên trong.")
        assert result.level == "confidential"

    def test_khong_phan_biet_hoa_thuong(self):
        classifier = SecurityLevelClassifier()
        result = classifier.classify("CONFIDENTIAL - internal use only for review team.")
        assert result.level == "confidential"

    def test_dictionary_tuy_chinh(self):
        classifier = SecurityLevelClassifier(keywords={"confidential": ["top secret"], "public": []})
        result = classifier.classify("This document is top secret.")
        assert result.level == "confidential"
